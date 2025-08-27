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
    
    def perform_review(self, ai_name, ai_display_name):
        """개별 AI 코드 리뷰 수행"""
        files = list(self.pr.get_files())
        if not files:
            print("변경된 파일이 없습니다.")
            return None
        
        print(f"🔍 {ai_display_name}으로 {len(files)}개 파일 리뷰 중...")
        
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
        system_message = "당신은 전문적인 코드 리뷰어입니다. PR 전체의 변경사항을 종합적으로 분석하여 한국어로 건설적인 리뷰를 제공하세요."
        
        # 개별 AI로 리뷰 수행
        review = self.ai_manager.generate_with_ai(ai_name, prompt, system_message)
        
        if review:
            print(f"  ✅ {ai_display_name} 리뷰 완료")
            return [{
                'filename': 'PR 전체 변경사항',
                'ai_name': ai_display_name,
                'review': review,
                'ai_names': ai_display_name,
                'ai_count': 1
            }]
        else:
            print(f"  ❌ {ai_display_name} 리뷰 실패")
            return None
    

    def post_review_comment(self, reviews):
        """리뷰 결과를 PR에 코멘트로 작성"""
        if not reviews:
            return
        
        # 템플릿 로드
        template = self.load_template('code_review_result.md')
        
        # 템플릿 사용 (개별 AI 리뷰)
        review_data = reviews[0]
        comment_body = template.format(
            ai_name=review_data['ai_name'],
            review=review_data['review']
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
            all_available_ais = self.ai_manager.get_all_available_ais()
            all_reviews = []  # 모든 AI 리뷰 결과 수집
            
            # 각 AI별로 개별 리뷰 수행
            for ai_name, ai_display_name in all_available_ais:
                reviews = self.perform_review(ai_name, ai_display_name)
                if reviews:
                    # 개별 리뷰 결과 코멘트 작성
                    self.post_review_comment(reviews)
                    all_reviews.extend(reviews)  # 성공한 리뷰만 수집
                    print(f"✅ {ai_display_name} 리뷰 완료")
                else:
                    print(f"❌ {ai_display_name} 리뷰 실패")
            
            # 모든 AI 리뷰 완료 후 종합 승인 처리
            if all_reviews:
                print(f"📋 총 {len(all_reviews)}개 AI 리뷰 완료, 승인 검토 시작")
                approver = PRApprover()
                approver.run(all_reviews)
                print("✅ AI 코드 리뷰 및 승인 검토 완료")
            else:
                print("❌ 모든 AI 리뷰 실패")
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
