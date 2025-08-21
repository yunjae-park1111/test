#!/usr/bin/env python3

import os
import sys
import yaml
import re
from github import Github
from openai import OpenAI
import google.generativeai as genai
import anthropic

class CommentHandler:
    def __init__(self):
        self.github = Github(os.environ['GITHUB_TOKEN'])
        self.repository_name = os.environ['REPOSITORY']
        self.repo = self.github.get_repo(self.repository_name)
        
        # 이벤트 정보 파싱
        self.event_action = os.environ.get('GITHUB_EVENT_ACTION', '')
        
        # PR 번호 가져오기 (코멘트 이벤트에서)
        if 'PR_NUMBER' in os.environ:
            self.pr_number = int(os.environ['PR_NUMBER'])
        else:
            # GitHub 이벤트에서 PR 번호 추출
            event_path = os.environ.get('GITHUB_EVENT_PATH', '')
            if event_path:
                import json
                with open(event_path, 'r') as f:
                    event_data = json.load(f)
                if 'pull_request' in event_data:
                    self.pr_number = event_data['pull_request']['number']
                elif 'issue' in event_data and 'pull_request' in event_data['issue']:
                    self.pr_number = event_data['issue']['number']
                else:
                    print("PR 번호를 찾을 수 없습니다.")
                    sys.exit(1)
            else:
                print("이벤트 정보를 찾을 수 없습니다.")
                sys.exit(1)
        
        # AI 클라이언트들 초기화
        self.init_ai_clients()
    
    def init_ai_clients(self):
        """AI 클라이언트들 초기화"""
        # GPT 초기화
        gpt_key = os.environ.get('OPENAI_API_KEY')
        if gpt_key:
            self.gpt_client = OpenAI(api_key=gpt_key)
            self.gpt_model = 'gpt-5'
        else:
            self.gpt_client = None
            self.gpt_model = None
        
        # Gemini 초기화
        gemini_key = os.environ.get('GEMINI_API_KEY')
        if gemini_key:
            genai.configure(api_key=gemini_key)
            self.gemini_client = genai.GenerativeModel('gemini-2.5-pro')
            self.gemini_model = 'gemini-2.5-pro'
        else:
            self.gemini_client = None
            self.gemini_model = None
        
        # Claude 초기화
        claude_key = os.environ.get('ANTHROPIC_API_KEY')
        if claude_key:
            self.claude_client = anthropic.Anthropic(api_key=claude_key)
            self.claude_model = 'claude-4-sonnet'
        else:
            self.claude_client = None
            self.claude_model = None
    
    def load_config(self):
        """설정 로드"""
        try:
            with open('.github/pr-review-config.yml', 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return {'ai_models': {'gpt': {'enabled': True}, 'gemini': {'enabled': True}, 'claude': {'enabled': True}}}
    
    def handle_comment_event(self):
        """코멘트 이벤트 처리"""
        try:
            # GitHub 이벤트 데이터 읽기
            event_path = os.environ.get('GITHUB_EVENT_PATH', '')
            if not event_path:
                print("이벤트 데이터를 찾을 수 없습니다.")
                return
            
            import json
            with open(event_path, 'r') as f:
                event_data = json.load(f)
            
            # 코멘트 정보 추출
            comment_body = event_data.get('comment', {}).get('body', '')
            comment_user = event_data.get('comment', {}).get('user', {}).get('login', '')
            comment_id = event_data.get('comment', {}).get('id', '')
            
            print(f"코멘트 처리: {comment_user}가 작성한 코멘트")
            
            # 봇 자신의 코멘트는 무시
            if comment_user in ['github-actions[bot]', 'dependabot[bot]']:
                print("봇 코멘트는 무시합니다.")
                return
            
            # 멘션/태그 확인
            mentions = self.extract_mentions(comment_body)
            if not self.should_respond_to_comment(comment_body, mentions):
                print("응답이 필요한 코멘트가 아닙니다.")
                return
            
            # AI 응답 생성
            response = self.generate_ai_response(comment_body, comment_user)
            if response:
                self.post_response(response, comment_id)
            
        except Exception as e:
            print(f"코멘트 처리 중 오류: {e}")
    
    def extract_mentions(self, comment_body):
        """코멘트에서 멘션 추출"""
        mention_pattern = r'@(\w+)'
        mentions = re.findall(mention_pattern, comment_body)
        return mentions
    
    def should_respond_to_comment(self, comment_body, mentions):
        """응답해야 할 코멘트인지 판단"""
        # 봇이 멘션된 경우
        bot_mentions = ['github-actions', 'bot', 'ai', 'review', 'reviewer']
        if any(mention.lower() in bot_mentions for mention in mentions):
            return True
        
        # 특정 키워드가 포함된 경우
        trigger_keywords = [
            '리뷰', 'review', '설명', 'explain', '분석', 'analyze',
            '체크', 'check', '확인', 'verify', '검토', '피드백', 'feedback'
        ]
        comment_lower = comment_body.lower()
        if any(keyword in comment_lower for keyword in trigger_keywords):
            return True
        
        return False
    
    def generate_ai_response(self, comment_body, comment_user):
        """AI 응답 생성"""
        try:
            config = self.load_config()
            pr = self.repo.get_pull(self.pr_number)
            
            # 컨텍스트 정보 수집
            pr_title = pr.title
            pr_description = pr.body or "설명 없음"
            
            # 최근 변경된 파일들 정보 (최대 3개)
            files = list(pr.get_files())[:3]
            files_info = []
            for file in files:
                files_info.append(f"- {file.filename} ({file.changes}줄 변경)")
            
            files_summary = "\n".join(files_info) if files_info else "변경된 파일 없음"
            
            prompt = f"""
다음은 GitHub PR에 대한 코멘트 상황입니다:

**PR 정보:**
- 제목: {pr_title}
- 설명: {pr_description}
- 변경된 파일들:
{files_summary}

**사용자 코멘트:**
사용자 {comment_user}가 다음과 같이 코멘트했습니다:
"{comment_body}"

**요청:**
위 코멘트에 대해 도움이 되는 응답을 제공해주세요. 
- 코드와 관련된 질문이면 구체적으로 설명해주세요
- 리뷰나 피드백 요청이면 해당 부분을 분석해서 답변해주세요
- 친근하고 전문적인 톤으로 답변해주세요
- 답변은 한국어로 해주세요

응답은 간결하고 유용해야 하며, 필요시 구체적인 코드 예시나 개선 제안을 포함해주세요.
"""
            
            # 사용 가능한 AI 중 하나로 응답 생성 (우선순위: GPT > Claude > Gemini)
            if self.gpt_client and config.get('ai_models', {}).get('gpt', {}).get('enabled', True):
                return self.generate_with_ai('gpt', prompt, config)
            elif self.claude_client and config.get('ai_models', {}).get('claude', {}).get('enabled', True):
                return self.generate_with_ai('claude', prompt, config)
            elif self.gemini_client and config.get('ai_models', {}).get('gemini', {}).get('enabled', True):
                return self.generate_with_ai('gemini', prompt, config)
            else:
                return "죄송합니다. 현재 AI 서비스에 접근할 수 없습니다."
                
        except Exception as e:
            print(f"AI 응답 생성 중 오류: {e}")
            return None
    
    def generate_with_ai(self, ai_name, prompt, config):
        """특정 AI로 응답 생성"""
        try:
            ai_config = config.get('ai_models', {}).get(ai_name, {})
            
            if ai_name == 'gpt' and self.gpt_client:
                response = self.gpt_client.chat.completions.create(
                    model=ai_config.get('model', self.gpt_model),
                    messages=[
                        {'role': 'system', 'content': '당신은 친근하고 전문적인 코드 리뷰어입니다. 사용자의 질문에 도움이 되는 답변을 제공하세요.'},
                        {'role': 'user', 'content': prompt}
                    ],
                    max_tokens=ai_config.get('max_tokens', 800),
                    temperature=ai_config.get('temperature', 0.3)
                )
                return response.choices[0].message.content
            
            elif ai_name == 'claude' and self.claude_client:
                response = self.claude_client.messages.create(
                    model=ai_config.get('model', self.claude_model),
                    max_tokens=ai_config.get('max_tokens', 800),
                    temperature=ai_config.get('temperature', 0.3),
                    system="당신은 친근하고 전문적인 코드 리뷰어입니다. 사용자의 질문에 도움이 되는 답변을 제공하세요.",
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            
            elif ai_name == 'gemini' and self.gemini_client:
                system_prompt = "당신은 친근하고 전문적인 코드 리뷰어입니다. 사용자의 질문에 도움이 되는 답변을 제공하세요."
                full_prompt = f"{system_prompt}\n\n{prompt}"
                response = self.gemini_client.generate_content(full_prompt)
                return response.text
            
            return None
            
        except Exception as e:
            print(f"{ai_name.upper()} 응답 생성 오류: {e}")
            return None
    
    def post_response(self, response, comment_id):
        """응답 게시"""
        try:
            pr = self.repo.get_pull(self.pr_number)
            
            # 응답 포맷팅
            formatted_response = f"""🤖 **AI 코드 어시스턴트 응답**

{response}

---
> 💡 추가 질문이나 더 자세한 설명이 필요하시면 언제든 말씀해주세요!
> 🔧 **AI 모델**: 멀티 AI 시스템 (GPT-5, Gemini 2.5 Pro, Claude 4 Sonnet)"""
            
            # PR에 코멘트 작성
            pr.create_issue_comment(formatted_response)
            print("AI 응답 코멘트 작성 완료")
            
        except Exception as e:
            print(f"응답 게시 중 오류: {e}")

def main():
    try:
        handler = CommentHandler()
        handler.handle_comment_event()
        print("코멘트 처리 완료")
    except Exception as error:
        print(f"코멘트 핸들러 오류: {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()
