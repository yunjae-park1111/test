#!/usr/bin/env python3
"""
리뷰어 승인 파일
AI 코드 리뷰 결과를 바탕으로 PR 승인 여부 결정
"""

import os
import sys
import yaml
from github import Github
from ai_client_manager import AIClientManager

class PRApprover:
    """PR 승인 처리 클래스"""
    
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
    
    def analyze_review_results(self, reviews):
        """리뷰 결과 분석하여 승인 여부 결정"""
        if not reviews:
            return False
        
        # 설정 파일에서 키워드 로드
        critical_keywords = self.load_critical_keywords()
        
        for review_data in reviews:
            review_text = review_data['review'].lower()
            if any(keyword in review_text for keyword in critical_keywords):
                print(f"🚨 {review_data['filename']}에서 중요한 이슈 발견, 승인 보류")
                return False
        
        print("✅ 모든 리뷰에서 심각한 문제 없음, 승인 가능")
        return True
    
    def load_critical_keywords(self):
        """승인 보류 키워드 로드"""
        return self.config['critical_keywords']
    
    def approve_pr(self):
        """실제 PR 승인"""
        try:
            # 템플릿에서 승인 메시지 로드
            approval_template = self.load_template('pr_approval.md')
            
            # GitHub API로 PR approve
            self.pr.create_review(
                body=approval_template,
                event="APPROVE"
            )
            print(f"✅ PR #{self.pr_number} 자동 승인 완료")
        except Exception as e:
            print(f"❌ PR 승인 실패: {e}")
    
    def run(self, reviews=None):
        """메인 실행 함수"""
        print(f"🤖 PR 승인 검토 시작 - PR #{self.pr_number}")
        
        try:
            if reviews:
                # 리뷰 결과가 전달된 경우
                should_approve = self.analyze_review_results(reviews)
                if should_approve:
                    self.approve_pr()
                    print("✅ PR 자동 승인 완료")
                else:
                    print("⏸️ 승인 보류 - 리뷰 결과에서 중요한 이슈 발견")
            else:
                print("❌ 리뷰 결과가 없어 승인할 수 없습니다.")
        
        except Exception as e:
            print(f"❌ PR 승인 처리 중 오류: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    approver = PRApprover()
    approver.run()
