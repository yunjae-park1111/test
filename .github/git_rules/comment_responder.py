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
        return 'tkai-pr-bot' in [m.lower() for m in mentions]
    
    def format_response(self, ai_response, ai_display_name):
        """AI 응답을 템플릿으로 포맷팅"""
        template = self.load_template('comment_response.md')
        
        return template.format(
            ai_response=ai_response,
            ai_display_name=ai_display_name
        )
    
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
            
            # AI 응답 생성 - 풍부한 컨텍스트 포함
            # PR 기본 정보
            pr_info = f"""PR 제목: {self.pr.title}
PR 설명: {self.pr.body or '설명 없음'}"""
            
            # 변경된 파일 정보
            files_info = "변경된 파일들:\n"
            try:
                files = list(self.pr.get_files())
                for file in files:
                    files_info += f"\n파일: {file.filename} (+{file.additions}/-{file.deletions})\n"
                    if file.patch:
                        files_info += f"```diff\n{file.patch}\n```\n"
                    else:
                        files_info += "변경사항 없음\n"
            except:
                files_info += "파일 정보 로드 실패\n"
            
            # 모든 코멘트들 (AI 리뷰 결과 포함)
            comments_info = "모든 코멘트들:\n"
            try:
                comments = list(self.pr.get_issue_comments())
                for comment in comments:
                    author = comment.user.login
                    body = comment.body
                    comments_info += f"- {author}: {body}\n"
            except:
                comments_info += "코멘트 로드 실패\n"
            
            detailed_prompt = f"""사용자 질문: "{comment_body}"

PR 정보: {pr_info}

변경된 파일 정보: {files_info}

모든 코멘트 정보: {comments_info}

위 PR 정보와 코멘트 히스토리를 바탕으로 사용자 질문에 구체적이고 도움이 되는 답변을 한국어로 해주세요."""
            
            ai_name, ai_display_name = self.ai_manager.get_available_ai()
            if ai_name:
                ai_response = self.ai_manager.generate_with_ai(
                    ai_name,
                    detailed_prompt,
                    "당신은 친근하고 전문적인 코드 리뷰어입니다. PR 컨텍스트를 바탕으로 정확하고 도움이 되는 답변을 제공하세요."
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
