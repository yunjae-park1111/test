#!/usr/bin/env python3
"""
PR 리뷰어 관리 파일
PR 생성시 자동으로 리뷰어 추가
"""

import os
import yaml
from github import Github

class PRReviewerManager:
    """PR 리뷰어 관리 클래스"""
    
    def __init__(self):
        self.github = Github(os.environ['GITHUB_TOKEN'])
        self.repo = self.github.get_repo(os.environ['REPOSITORY'])
        self.pr_number = int(os.environ['PR_NUMBER'])
        self.pr = self.repo.get_pull(self.pr_number)
        self.config = self.load_config()
    
    def load_config(self):
        """설정 파일 로드"""
        config_files = ['.github/pr-review-config.yml', '.github/git_rules/templates/config.yml']
        for config_file in config_files:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
        raise FileNotFoundError("설정 파일을 찾을 수 없습니다")
    
    def add_bot_reviewer(self):
        """PR 봇을 리뷰어로 추가"""
        try:
            # github-actions[bot]을 리뷰어로 추가
            bot_username = "github-actions[bot]"
            pr_author = self.pr.user.login
            
            print(f"📝 PR 작성자: {pr_author}")
            print(f"🤖 {bot_username}을 리뷰어로 추가 중...")
            
            # tkai-pr-bot을 리뷰어로 추가
            self.pr.create_review_request(reviewers=[bot_username])
            
            print(f"✅ {bot_username}이 리뷰어로 추가되었습니다")
            print(f"✅ PR #{self.pr_number}에 AI 리뷰 봇 설정 완료")
            
        except Exception as e:
            print(f"❌ 리뷰어 추가 실패: {e}")
            print(f"❌ {bot_username} 계정이 존재하지 않거나 권한이 없을 수 있습니다")
            import traceback
            traceback.print_exc()
    
    def run(self):
        """메인 실행 함수"""
        print(f"👥 PR 리뷰어 설정 시작 - PR #{self.pr_number}")
        
        try:
            self.add_bot_reviewer()
            print("✅ PR 리뷰어 설정 완료")
        
        except Exception as e:
            print(f"❌ PR 리뷰어 설정 중 오류: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    manager = PRReviewerManager()
    manager.run()
