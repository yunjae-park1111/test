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
    
    def create_comprehensive_review_prompt(self, all_changes):
        """전체 변경사항에 대한 통합 리뷰 프롬프트 생성"""
        # 템플릿 로드
        template = self.load_template('review_prompt.md')
        
        # 모든 변경사항 통합
        all_changes_text = ""
        for change in all_changes:
            all_changes_text += f"""
=== {change['filename']} ({change['language']}) ===
추가: +{change['additions']}줄, 삭제: -{change['deletions']}줄

```diff
{change['patch']}
```

"""
        
        return template.format(
            pr_title=self.pr.title,
            pr_description=self.pr.body or '설명 없음',
            file_count=len(all_changes),
            all_changes=all_changes_text
        )
    
    def perform_review(self):
        """AI 코드 리뷰 수행"""
        files = list(self.pr.get_files())
        if not files:
            print("변경된 파일이 없습니다.")
            return None
        
        print(f"🔍 {len(files)}개 파일에 대한 AI 종합 리뷰 시작")
        
        # 전체 변경사항 수집
        all_changes = []
        for file in files:
            if file.patch:  # 변경사항이 있는 파일만
                language = self.get_file_language(file.filename)
                all_changes.append({
                    'filename': file.filename,
                    'language': language,
                    'patch': file.patch,
                    'additions': file.additions,
                    'deletions': file.deletions
                })
        
        if not all_changes:
            print("코드 변경사항이 없습니다.")
            return None
        
        # 전체 변경사항에 대한 통합 리뷰 프롬프트 생성
        prompt = self.create_comprehensive_review_prompt(all_changes)
        
        # 모든 사용 가능한 AI로 통합 리뷰
        all_available_ais = self.ai_manager.get_all_available_ais()
        if not all_available_ais:
            print("❌ 사용 가능한 AI가 없습니다.")
            return None
        
        all_reviews = []
        system_message = "당신은 전문적인 코드 리뷰어입니다. PR 전체의 변경사항을 종합적으로 분석하여 한국어로 건설적인 리뷰를 제공하세요."
        
        for ai_name, ai_display_name in all_available_ais:
            print(f"🔍 {ai_display_name}으로 리뷰 중...")
            review = self.ai_manager.generate_with_ai(ai_name, prompt, system_message)
            
            if review:
                all_reviews.append({
                    'ai_name': ai_display_name,
                    'review': review
                })
                print(f"  ✅ {ai_display_name} 리뷰 완료")
            else:
                print(f"  ❌ {ai_display_name} 리뷰 실패")
        
        if all_reviews:
            # 모든 AI 리뷰를 하나로 통합
            combined_data = self.combine_ai_reviews(all_reviews)
            return [{
                'filename': 'PR 전체 변경사항',
                'ai_name': 'Multi-AI Review',
                'review': combined_data['reviews'],
                'ai_names': combined_data['ai_names'],
                'ai_count': combined_data['ai_count']
            }]
        else:
            print("❌ 모든 AI 리뷰 실패")
            return None
    
    def combine_ai_reviews(self, all_reviews):
        """모든 AI 리뷰를 하나로 통합"""
        # 각 AI 리뷰 조합
        ai_reviews_text = ""
        for review_data in all_reviews:
            ai_name = review_data['ai_name']
            review = review_data['review']
            
            ai_reviews_text += f"### 🔧 **{ai_name} 리뷰**\n\n"
            ai_reviews_text += f"{review}\n\n"
            ai_reviews_text += "---\n\n"
        
        return {
            'reviews': ai_reviews_text,
            'ai_names': ', '.join([r['ai_name'] for r in all_reviews]),
            'ai_count': len(all_reviews)
        }
    
    def post_review_comment(self, reviews):
        """리뷰 결과를 PR에 코멘트로 작성"""
        if not reviews:
            return
        
        # 템플릿 로드
        template = self.load_template('code_review_result.md')
        
        # 템플릿 사용
        review_data = reviews[0]  # Multi-AI 리뷰는 하나의 통합 결과
        comment_body = template.format(
            reviews=review_data['review'],
            ai_names=review_data.get('ai_names', ''),
            ai_count=review_data.get('ai_count', 0)
        )
        
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
