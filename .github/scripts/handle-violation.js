const { Octokit } = require('@octokit/rest');

class ViolationHandler {
  constructor() {
    this.octokit = new Octokit({
      auth: process.env.GITHUB_TOKEN
    });
    this.prNumber = parseInt(process.env.PR_NUMBER);
    this.repository = process.env.REPOSITORY.split('/');
    this.owner = this.repository[0];
    this.repo = this.repository[1];
    this.violationMessage = process.env.VIOLATION_MESSAGE;
  }

  async handleViolation() {
    const commentBody = this.buildViolationComment();
    await this.postComment(commentBody);
    await this.addLabels(['needs-revision', 'pr-rules-violation']);
    await this.requestChanges();
  }

  buildViolationComment() {
    return `## ❌ PR 룰 위반이 감지되었습니다

${this.violationMessage}

### 📋 해결 방법
1. 위의 위반 사항들을 수정해주세요
2. 수정 후 새로운 커밋을 푸시하면 자동으로 다시 검증됩니다
3. 문의사항이 있으시면 언제든 코멘트로 남겨주세요

### 📚 PR 가이드라인
- [PR 작성 가이드](https://github.com/yunjae-park1111/test/blob/main/docs/pr-guide.md)
- [커밋 메시지 컨벤션](https://github.com/yunjae-park1111/test/blob/main/docs/commit-convention.md)
- [코딩 컨벤션](https://github.com/yunjae-park1111/test/blob/main/docs/coding-convention.md)

---
> 🤖 이 메시지는 자동으로 생성되었습니다. PR 룰을 준수하여 다시 제출해주세요.`;
  }

  async postComment(body) {
    try {
      await this.octokit.issues.createComment({
        owner: this.owner,
        repo: this.repo,
        issue_number: this.prNumber,
        body: body
      });
    } catch (error) {
      console.error('코멘트 작성 실패:', error);
    }
  }

  async addLabels(labels) {
    try {
      await this.octokit.issues.addLabels({
        owner: this.owner,
        repo: this.repo,
        issue_number: this.prNumber,
        labels: labels
      });
    } catch (error) {
      console.error('라벨 추가 실패:', error);
    }
  }

  async requestChanges() {
    try {
      await this.octokit.pulls.createReview({
        owner: this.owner,
        repo: this.repo,
        pull_number: this.prNumber,
        event: 'REQUEST_CHANGES',
        body: 'PR 룰 위반으로 인해 변경이 요청되었습니다. 위의 코멘트를 참고하여 수정해주세요.'
      });
    } catch (error) {
      console.error('리뷰 요청 실패:', error);
    }
  }
}

async function main() {
  try {
    const handler = new ViolationHandler();
    await handler.handleViolation();
    console.log('PR 룰 위반 처리 완료');
  } catch (error) {
    console.error('위반 처리 중 오류:', error);
    process.exit(1);
  }
}

main();
