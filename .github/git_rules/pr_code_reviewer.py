#!/usr/bin/env python3
"""
PR 코드 리뷰 실행 파일
룰 위반시 코멘트만 남기고 reviewer 설정은 건드리지 않음
"""

import os
import sys
import yaml
from github import Github
from ai_client_manager import AIClientManager
from pr_approver import PRApprover

class PRCodeReviewer:
    """PR 코드 리뷰 실행 클래스"""
    
    def __init__(self):
        self.github = Github(os.environ['GITHUB_TOKEN'])
        self.repo = self.github.get_repo(os.environ['REPOSITORY'])
        self.pr_number = int(os.environ['PR_NUMBER'])
        self.pr = self.repo.get_pull(self.pr_number)
        self.ai_manager = AIClientManager()
        self.config = self.load_config()
    
    def load_config(self):
        """설정 파일 로드"""
        config_files = ['.github/pr-review-config.yml', '.github/git_rules/templates/config.yml']
        for config_file in config_files:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
        raise FileNotFoundError("설정 파일을 찾을 수 없습니다")
    
    def load_template(self, template_name):
        """템플릿 파일 로드"""
        try:
            template_path = f'.github/git_rules/templates/{template_name}'
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return None
    
    def get_file_language(self, filename):
        """파일 확장자로 언어 감지"""
        extensions = self.config['file_extensions']
        ext = os.path.splitext(filename)[1].lower()
        return extensions[ext]
    
    def create_review_prompt(self, file):
        """리뷰 프롬프트 생성"""
        language = self.get_file_language(file.filename)
        
        # 템플릿 로드
        template = self.load_template('review_prompt.md')
        
        return template.format(
            filename=file.filename,
            language=language,
            patch=file.patch
        )
    
    def perform_review(self):
        """AI 코드 리뷰 수행"""
        files = list(self.pr.get_files())
        if not files:
            print("변경된 파일이 없습니다.")
            return None
        
        print(f"🔍 {len(files)}개 파일에 대한 AI 리뷰 시작")
        
        all_reviews = []
        
        for file in files:
            if file.patch:  # 변경사항이 있는 파일만
                prompt = self.create_review_prompt(file)
                
                # 사용 가능한 AI로 리뷰
                ai_name, ai_display_name = self.ai_manager.get_available_ai()
                if ai_name:
                    review = self.ai_manager.generate_with_ai(
                        ai_name, 
                        prompt, 
                        "당신은 전문적인 코드 리뷰어입니다. 한국어로 건설적인 리뷰를 제공하세요."
                    )
                    
                    if review:
                        all_reviews.append({
                            'filename': file.filename,
                            'ai_name': ai_display_name,
                            'review': review
                        })
                        print(f"  ✅ {file.filename} 리뷰 완료 ({ai_display_name})")
                    else:
                        print(f"  ❌ {file.filename} 리뷰 실패")
                else:
                    print("❌ 사용 가능한 AI가 없습니다.")
                    break
        
        return all_reviews if all_reviews else None
    

    
    def post_review_comment(self, reviews):
        """리뷰 결과를 PR에 코멘트로 작성"""
        if not reviews:
            return
        
        # 템플릿 로드
        template = self.load_template('code_review_result.md')
        
        # 템플릿 사용
        reviews_text = ""
        for i, review_data in enumerate(reviews, 1):
            reviews_text += f"""### 📁 **{review_data['filename']}**
**🔧 리뷰어**: {review_data['ai_name']}

{review_data['review']}

---
"""
        comment_body = template.replace('{reviews}', reviews_text)
        
        try:
            self.pr.create_issue_comment(comment_body)
            print(f"✅ 리뷰 코멘트 작성 완료")
                
        except Exception as e:
            print(f"❌ 리뷰 코멘트 작성 실패: {e}")
    
    def post_failure_comment(self):
        """리뷰 실패시 코멘트 작성"""
        print("🔄 리뷰 실패 코멘트 작성 시작")
        
        try:
            template = self.load_template('review_failure.md')
            print(f"📝 템플릿 로드 완료: {len(template) if template else 0}자")
            
            self.pr.create_issue_comment(template)
            print("✅ 리뷰 실패 코멘트 작성 완료")
        except Exception as e:
            print(f"❌ 리뷰 실패 코멘트 작성 실패: {e}")
            print(f"❌ 에러 타입: {type(e).__name__}")
    
    def run(self):
        """메인 실행 함수 - 코드 리뷰만 수행"""
        print(f"🚀 AI 코드 리뷰 시작 - PR #{self.pr_number}")
        
        try:
            reviews = self.perform_review()
            if reviews:
                # 리뷰 결과 코멘트 작성
                self.post_review_comment(reviews)
                
                # PR 승인 처리는 별도 모듈에서 담당
                approver = PRApprover()
                approver.run(reviews)
                
                print("✅ AI 코드 리뷰 완료")
            else:
                print("❌ AI 코드 리뷰 실패")
                self.post_failure_comment()
        
        except Exception as e:
            print(f"❌ AI 코드 리뷰 중 오류: {e}")
            import traceback
            traceback.print_exc()
            # 예외 발생시에도 실패 코멘트 작성 시도
            try:
                self.post_failure_comment()
            except Exception as comment_error:
                print(f"❌ 실패 코멘트 작성도 실패: {comment_error}")

if __name__ == "__main__":
    reviewer = PRCodeReviewer()
    reviewer.run()
