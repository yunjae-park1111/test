#!/usr/bin/env python3

import os
import sys
from github import Github

class PRApprover:
    def __init__(self):
        self.github = Github(os.environ['GITHUB_TOKEN'])
        self.pr_number = int(os.environ['PR_NUMBER'])
        self.repository_name = os.environ['REPOSITORY']
        self.repo = self.github.get_repo(self.repository_name)
    
    def approve_pr(self):
        try:
            pr = self.repo.get_pull(self.pr_number)
            
            # 기존의 github-actions 리뷰 상태 확인
            reviews = list(pr.get_reviews())
            has_github_actions_request = any(
                review.user.login == 'github-actions[bot]' and 
                review.state == 'CHANGES_REQUESTED' 
                for review in reviews
            )
            
            if has_github_actions_request:
                # PR 룰을 모두 통과했으므로 승인 리뷰 추가
                pr.create_review(
                    body='✅ **PR 룰 검증 통과!**\n\n모든 PR 룰을 준수했습니다. 코드 리뷰가 완료되었습니다.',
                    event='APPROVE'
                )
                print('✅ PR 룰 통과로 자동 승인 완료')
            else:
                print('ℹ️ 승인이 필요한 이전 리뷰 없음')
                
        except Exception as error:
            print(f'PR 승인 중 오류: {error}')
            # 에러가 발생해도 워크플로우는 계속 진행
            pass

def main():
    try:
        approver = PRApprover()
        approver.approve_pr()
    except Exception as error:
        print(f'PR 승인 스크립트 오류: {error}')
        # 에러 발생해도 exit code 0으로 워크플로우 계속 진행
        pass

if __name__ == "__main__":
    main()
