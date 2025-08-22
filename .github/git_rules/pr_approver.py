#!/usr/bin/env python3
"""
PR 승인 파일
PR 규칙을 통과한 경우 승인 메시지 작성
"""

import os
from github import Github

class PRApprover:
    """PR 승인 처리 클래스"""
    
    def __init__(self):
        self.github = Github(os.environ['GITHUB_TOKEN'])
        self.repo = self.github.get_repo(os.environ['REPOSITORY'])
        self.pr_number = int(os.environ['PR_NUMBER'])
        self.pr = self.repo.get_pull(self.pr_number)
    
    def load_template(self, template_name):
        """템플릿 파일 로드"""
        try:
            template_path = f'.github/git_rules/templates/{template_name}'
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return None
    
    def post_approval_comment(self):
        """승인 메시지를 PR에 코멘트로 작성"""
        # 템플릿 로드
        template = self.load_template('pr_approval.md')
        
        if template:
            comment_body = template
        else:
            # 기본 승인 메시지
            comment_body = """## ✅ **PR 규칙 검증 성공!**

🎉 **축하합니다!** 귀하의 Pull Request가 모든 규칙을 통과했습니다.

### ✅ **통과한 검증 항목**
- ✅ **제목 형식**: 명확하고 적절한 제목
- ✅ **설명 내용**: 충분히 상세한 설명

### 🚀 **다음 단계**
이제 코드 리뷰를 진행하겠습니다. AI가 자동으로 코드를 분석하여 리뷰 의견을 제공할 예정입니다.

**감사합니다!** 좋은 코드와 문서화로 프로젝트에 기여해주셔서 고맙습니다! 🙏"""
        
        try:
            self.pr.create_issue_comment(comment_body)
            print(f"✅ PR 승인 메시지 작성 완료")
        except Exception as e:
            print(f"❌ PR 승인 메시지 작성 실패: {e}")
    
    def run(self):
        """메인 실행 함수"""
        print(f"🎉 PR 승인 처리 시작 - PR #{self.pr_number}")
        
        try:
            self.post_approval_comment()
            print("✅ PR 승인 처리 완료")
        
        except Exception as e:
            print(f"❌ PR 승인 처리 중 오류: {e}")

if __name__ == "__main__":
    approver = PRApprover()
    approver.run()
