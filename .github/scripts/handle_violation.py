#!/usr/bin/env python3

import os
import sys
from github import Github

class ViolationHandler:
    def __init__(self):
        self.github = Github(os.environ['GITHUB_TOKEN'])
        self.pr_number = int(os.environ['PR_NUMBER'])
        self.repository_name = os.environ['REPOSITORY']
        self.repo = self.github.get_repo(self.repository_name)
        self.violation_message = os.environ['VIOLATION_MESSAGE']
    
    def handle_violation(self):
        pr = self.repo.get_pull(self.pr_number)
        
        comment_body = self.build_violation_comment()
        self.post_comment(pr, comment_body)
        self.add_labels(pr, ['needs-revision', 'pr-rules-violation'])
        self.request_changes(pr)
    
    def build_violation_comment(self):
        return f"""## ❌ PR 룰 위반이 감지되었습니다

{self.violation_message}

### 📋 해결 방법
1. 위의 위반 사항들을 수정해주세요
2. 수정 후 새로운 커밋을 푸시하면 자동으로 다시 검증됩니다
3. 문의사항이 있으시면 언제든 코멘트로 남겨주세요

### 📚 PR 가이드라인
- [PR 작성 가이드](https://github.com/yunjae-park1111/test/blob/main/docs/pr-guide.md)
- [커밋 메시지 컨벤션](https://github.com/yunjae-park1111/test/blob/main/docs/commit-convention.md)
- [코딩 컨벤션](https://github.com/yunjae-park1111/test/blob/main/docs/coding-convention.md)

---
> 🤖 이 메시지는 자동으로 생성되었습니다. PR 룰을 준수하여 다시 제출해주세요."""
    
    def post_comment(self, pr, body):
        try:
            pr.create_issue_comment(body)
        except Exception as error:
            print(f'코멘트 작성 실패: {error}')
    
    def add_labels(self, pr, labels):
        try:
            issue = self.repo.get_issue(self.pr_number)
            issue.add_to_labels(*labels)
        except Exception as error:
            print(f'라벨 추가 실패: {error}')
    
    def request_changes(self, pr):
        try:
            pr.create_review(
                body='PR 룰 위반으로 인해 변경이 요청되었습니다. 위의 코멘트를 참고하여 수정해주세요.',
                event='REQUEST_CHANGES'
            )
        except Exception as error:
            print(f'리뷰 요청 실패: {error}')

def main():
    try:
        handler = ViolationHandler()
        handler.handle_violation()
        print('PR 룰 위반 처리 완료')
    except Exception as error:
        print(f'위반 처리 중 오류: {error}')
        sys.exit(1)

if __name__ == "__main__":
    main()
