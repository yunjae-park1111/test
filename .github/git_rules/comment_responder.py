#!/usr/bin/env python3
"""
코멘트 응답 파일
PR의 코멘트에 AI가 자동으로 응답
"""

import os
import re
from github import Github
from ai_client_manager import AIClientManager

class CommentResponder:
    """코멘트 응답 처리 클래스"""
    
    def __init__(self):
        self.github = Github(os.environ['GITHUB_TOKEN'])
        self.repo = self.github.get_repo(os.environ['REPOSITORY'])
        self.pr_number = int(os.environ['PR_NUMBER'])
        self.pr = self.repo.get_pull(self.pr_number)
        self.comment_id = int(os.environ.get('COMMENT_ID', 0))
        self.ai_manager = AIClientManager()
    
    def load_template(self, template_name):
        """템플릿 파일 로드"""
        try:
            template_path = f'.github/git_rules/templates/{template_name}'
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return None
    
    def extract_mentions(self, comment_body):
        """코멘트에서 멘션 추출"""
        mention_pattern = r'@(\w+)'
        mentions = re.findall(mention_pattern, comment_body)
        return mentions
    
    def should_respond(self, comment_body, mentions):
        """AI가 응답해야 하는 코멘트인지 판단"""
        comment_lower = comment_body.lower()
        
        # 트리거 키워드 확인
        trigger_keywords = [
            '리뷰', 'review', '설명', 'explain', '분석', 'analyze',
            '체크', 'check', '확인', 'verify', '검토', '피드백', 'feedback'
        ]
        
        if any(keyword in comment_lower for keyword in trigger_keywords):
            return True
        
        # 봇이 멘션된 경우
        bot_mentions = ['github-actions', 'bot', 'ai', 'review', 'reviewer']
        if any(mention.lower() in bot_mentions for mention in mentions):
            return True
        
        return False
    
    def format_response(self, ai_response, ai_display_name):
        """AI 응답을 템플릿으로 포맷팅"""
        template = self.load_template('comment_response.md')
        
        if template:
            return template.format(
                ai_response=ai_response,
                ai_display_name=ai_display_name
            )
        else:
            # 기본 포맷
            return f"""🤖 **AI 코드 어시스턴트 응답**

{ai_response}

---
> 💡 추가 질문이나 더 자세한 설명이 필요하시면 언제든 말씀해주세요!
> 🔧 **AI 모델**: {ai_display_name}"""
    
    def respond_to_comment(self):
        """코멘트에 AI 응답 생성"""
        if not self.comment_id:
            print("코멘트 ID가 없습니다.")
            return
        
        try:
            comment = self.repo.get_issue_comment(self.comment_id)
            comment_body = comment.body
            comment_user = comment.user.login
            mentions = self.extract_mentions(comment_body)
            
            print(f"📝 코멘트 분석: {comment_user} - '{comment_body[:50]}...'")
            
            # 응답이 필요한지 확인
            if not self.should_respond(comment_body, mentions):
                print("응답이 필요하지 않은 코멘트입니다.")
                return
            
            # AI 응답 생성
            simple_prompt = f"""사용자 질문: "{comment_body}"
PR 제목: {self.pr.title}
친근하게 한국어로 답변해주세요."""
            
            ai_name, ai_display_name = self.ai_manager.get_available_ai()
            if ai_name:
                ai_response = self.ai_manager.generate_with_ai(
                    ai_name,
                    simple_prompt,
                    "당신은 친근하고 전문적인 코드 리뷰어입니다. 사용자의 질문에 도움이 되는 답변을 제공하세요."
                )
                
                if ai_response:
                    formatted_response = self.format_response(ai_response, ai_display_name)
                    
                    # 응답 작성
                    self.pr.create_issue_comment(formatted_response)
                    print(f"✅ AI 응답 작성 완료 ({ai_display_name})")
                else:
                    print("❌ AI 응답 생성 실패")
            else:
                print("❌ 사용 가능한 AI가 없습니다.")
        
        except Exception as e:
            print(f"❌ 코멘트 응답 중 오류: {e}")
    
    def run(self):
        """메인 실행 함수"""
        print(f"💬 코멘트 응답 처리 시작 - PR #{self.pr_number}")
        
        try:
            self.respond_to_comment()
            print("✅ 코멘트 응답 처리 완료")
        
        except Exception as e:
            print(f"❌ 코멘트 응답 처리 중 오류: {e}")

if __name__ == "__main__":
    responder = CommentResponder()
    responder.run()
