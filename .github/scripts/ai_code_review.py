#!/usr/bin/env python3

import os
import sys
import yaml
from github import Github
from openai import OpenAI

import google.generativeai as genai
import anthropic

class AICodeReviewer:
    def __init__(self):
        self.github = Github(os.environ['GITHUB_TOKEN'])
        
        # AI 클라이언트들 초기화
        
        # GPT 초기화
        gpt_key = os.environ.get('OPENAI_API_KEY')
        if gpt_key:
            self.gpt_client = OpenAI(
                api_key=gpt_key
            )
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
            
        self.pr_number = int(os.environ['PR_NUMBER'])
        self.repository_name = os.environ['REPOSITORY']
        self.repo = self.github.get_repo(self.repository_name)
        self.pr_action = os.environ.get('PR_ACTION', 'opened')
    
    def load_review_config(self):
        try:
            with open('.github/pr-review-config.yml', 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return self.get_default_review_config()
    
    def get_default_review_config(self):
        return {
            'ai_models': {
                'gpt': {
                    'model': 'gpt-5',
                    'max_tokens': 1200,
                    'temperature': 0.2,
                    'enabled': True
                },
                'gemini': {
                    'model': 'gemini-2.5-pro',
                    'max_tokens': 1200,
                    'temperature': 0.2,
                    'enabled': True
                },
                'claude': {
                    'model': 'claude-4-sonnet',
                    'max_tokens': 1200,
                    'temperature': 0.2,
                    'enabled': True
                }
            },
            'review_settings': {
                'focus_areas': ['security', 'performance', 'maintainability', 'best_practices'],
                'languages': {
                    'javascript': {
                        'checks': ['async_patterns', 'error_handling', 'memory_leaks'],
                        'frameworks': ['react', 'node', 'express']
                    },
                    'python': {
                        'checks': ['pep8', 'security', 'performance'],
                        'frameworks': ['django', 'flask', 'fastapi']
                    }
                },
                'severity_levels': {
                    'critical': '🚨',
                    'high': '⚠️',
                    'medium': '💡',
                    'low': 'ℹ️'
                }
            }
        }
    
    def review_pr(self):
        config = self.load_review_config()
        pr = self.repo.get_pull(self.pr_number)
        files = list(pr.get_files())
        
        action_text = {
            'opened': '신규 PR',
            'synchronize': 'PR 업데이트', 
            'reopened': 'PR 재오픈'
        }.get(self.pr_action, 'PR')
        
        print(f"리뷰 시작 ({action_text}): PR #{self.pr_number} - {pr.title}")
        
        reviews = []
        
        for file in files:
            if self.should_review_file(file, config):
                review = self.review_file_multi_ai(file, config)
                if review:
                    reviews.append(review)
        
        self.post_review(pr, reviews, config)
    
    def should_review_file(self, file, config):
        reviewable_extensions = ['.js', '.ts', '.jsx', '.tsx', '.py', '.java', '.go', '.rs']
        has_reviewable_extension = any(file.filename.endswith(ext) for ext in reviewable_extensions)
        
        is_not_deleted = file.status != 'removed'
        has_changes = file.changes > 0
        is_not_too_large = file.changes < 300  # 너무 큰 파일은 건너뛰기
        
        return has_reviewable_extension and is_not_deleted and has_changes and is_not_too_large
    
    def review_file_multi_ai(self, file, config):
        """여러 AI로 파일을 리뷰하고 결과를 통합"""
        try:
            if not file.patch:
                return None
            
            language = self.detect_language(file.filename)
            prompt = self.build_review_prompt(file, language, config)
            
            reviews = {}
            
            # 멀티 AI 리뷰 실행
            ai_list = ['gpt', 'gemini', 'claude']
            ai_display_names = {'gpt': 'GPT', 'gemini': 'Gemini', 'claude': 'Claude'}
            
            for ai_name in ai_list:
                ai_review = self.review_with_ai(ai_name, prompt, config)
                if ai_review:
                    reviews[ai_display_names[ai_name]] = ai_review
            
            if not reviews:
                return None
            
            return {
                'filename': file.filename,
                'reviews': reviews,
                'language': language,
                'changes': file.changes
            }
            
        except Exception as error:
            print(f"파일 리뷰 중 오류: {file.filename} - {error}")
            return None
    
    def review_with_ai(self, ai_name, prompt, config):
        """통합 AI 리뷰 메소드"""
        try:
            ai_config = config.get('ai_models', {}).get(ai_name, {})
            if not ai_config.get('enabled', True):
                return None
            
            system_message = "당신은 경험 많은 시니어 개발자입니다. 코드 리뷰를 수행하여 보안, 성능, 유지보수성, 베스트 프랙티스 관점에서 건설적인 피드백을 제공하세요."
            
            if ai_name == 'gpt':
                if not self.gpt_client:
                    return None
                response = self.gpt_client.chat.completions.create(
                    model=ai_config.get('model', self.gpt_model),
                    messages=[
                        {'role': 'system', 'content': system_message},
                        {'role': 'user', 'content': prompt}
                    ],
                    max_tokens=ai_config.get('max_tokens', 1200),
                    temperature=ai_config.get('temperature', 0.2)
                )
                return response.choices[0].message.content
            
            elif ai_name == 'gemini':
                if not self.gemini_client:
                    return None
                full_prompt = f"{system_message}\n\n{prompt}"
                response = self.gemini_client.generate_content(full_prompt)
                return response.text
            
            elif ai_name == 'claude':
                if not self.claude_client:
                    return None
                response = self.claude_client.messages.create(
                    model=ai_config.get('model', self.claude_model),
                    max_tokens=ai_config.get('max_tokens', 1200),
                    temperature=ai_config.get('temperature', 0.2),
                    system=system_message,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            
            else:
                print(f"알 수 없는 AI: {ai_name}")
                return None
                
        except Exception as e:
            print(f"{ai_name.upper()} 리뷰 오류: {e}")
            return None
    
    def detect_language(self, filename):
        ext = filename.split('.')[-1].lower()
        language_map = {
            'js': 'javascript',
            'jsx': 'javascript',
            'ts': 'typescript',
            'tsx': 'typescript',
            'py': 'python',
            'java': 'java',
            'go': 'go',
            'rs': 'rust'
        }
        return language_map.get(ext, 'unknown')
    
    def build_review_prompt(self, file, language, config):
        focus_areas = ', '.join(config['review_settings']['focus_areas'])
        
        return f"""
파일명: {file.filename}
언어: {language}
변경 라인 수: {file.changes}

다음 코드 변경사항을 리뷰해주세요:

```diff
{file.patch}
```

리뷰 포커스: {focus_areas}

다음 형식으로 응답해주세요:
1. **전체 요약**: 변경사항에 대한 간단한 요약
2. **주요 발견사항**: 중요한 이슈나 개선점 (있는 경우만)
3. **개선 제안**: 구체적인 코드 개선 방안 (있는 경우만)
4. **보안 검토**: 보안 관련 이슈 (있는 경우만)
5. **긍정적 피드백**: 잘 작성된 부분에 대한 인정

각 이슈의 심각도를 🚨(Critical), ⚠️(High), 💡(Medium), ℹ️(Low)로 표시해주세요.
"""
    
    def post_review(self, pr, reviews, config):
        # PR 액션에 따른 헤더 메시지
        action_messages = {
            'opened': '🤖 **멀티 AI 코드 리뷰 결과**',
            'synchronize': '🔄 **멀티 AI 재리뷰 결과** (PR 업데이트됨)',
            'reopened': '🔄 **멀티 AI 재리뷰 결과** (PR 재오픈됨)'
        }
        
        header_message = action_messages.get(self.pr_action, '🤖 **멀티 AI 코드 리뷰 결과**')
        
        if not reviews:
            comment_body = f'{header_message}\n\n리뷰할 파일이 없거나 모든 파일이 양호합니다! ✅'
            if self.pr_action == 'synchronize':
                comment_body += '\n\n> 📝 **업데이트 내용**: 새로운 커밋이 추가되었지만 추가 리뷰가 필요한 변경사항은 없습니다.'
            pr.create_issue_comment(comment_body)
            return
        
        comment_body = f'{header_message}\n\n'
        
        if self.pr_action == 'synchronize':
            comment_body += '> 🔄 **PR 업데이트 감지**: 새로운 커밋에 대한 재리뷰를 수행했습니다.\n\n'
        
        # 전체 요약
        comment_body += '## 📊 전체 요약\n'
        comment_body += f'- **리뷰된 파일**: {len(reviews)}개\n'
        comment_body += f'- **총 변경 라인**: {sum(r["changes"] for r in reviews)}개\n'
        
        # 사용된 AI 모델들 표시
        available_ais = []
        if reviews and 'reviews' in reviews[0]:
            available_ais = list(reviews[0]['reviews'].keys())
        comment_body += f'- **사용된 AI**: {"、".join(available_ais)}\n\n'
        
        # 파일별 리뷰
        comment_body += '## 📝 상세 리뷰\n\n'
        
        for review in reviews:
            comment_body += f'### 📄 `{review["filename"]}`\n'
            comment_body += f'**언어**: {review["language"]} | **변경**: {review["changes"]}줄\n\n'
            
            # 각 AI의 리뷰를 탭으로 구분해서 표시
            for ai_name, ai_review in review["reviews"].items():
                emoji_map = {'GPT': '🤖', 'Gemini': '💎', 'Claude': '🧠'}
                emoji = emoji_map.get(ai_name, '🔹')
                
                comment_body += f'<details>\n'
                comment_body += f'<summary>{emoji} <strong>{ai_name} 리뷰</strong></summary>\n\n'
                comment_body += ai_review + '\n\n'
                comment_body += '</details>\n\n'
            
            comment_body += '---\n\n'
        
        # 푸터
        comment_body += '> 🤖 이 리뷰는 여러 AI에 의해 생성되었습니다. 추가 질문이나 토론이 필요한 부분이 있다면 언제든 코멘트로 남겨주세요!\n'
        # AI 모델 정보 표시
        ai_models = config.get('ai_models', {})
        gpt_model = ai_models.get('gpt', {}).get('model', 'gpt-5')
        gemini_model = ai_models.get('gemini', {}).get('model', 'gemini-2.5-pro')
        claude_model = ai_models.get('claude', {}).get('model', 'claude-4-sonnet')
        comment_body += f'> 📊 **GPT**: {gpt_model} | **Gemini**: {gemini_model} | **Claude**: {claude_model}\n'
        
        try:
            pr.create_issue_comment(comment_body)
            print('멀티 AI 리뷰 코멘트 작성 완료')
        except Exception as error:
            print(f'코멘트 작성 실패: {error}')

def main():
    try:
        reviewer = AICodeReviewer()
        reviewer.review_pr()
        print('멀티 AI 코드 리뷰 완료')
    except Exception as error:
        print(f'멀티 AI 코드 리뷰 중 오류: {error}')
        sys.exit(1)

if __name__ == "__main__":
    main()
