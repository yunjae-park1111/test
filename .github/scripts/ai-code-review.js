const { Octokit } = require('@octokit/rest');
const OpenAI = require('openai');
const yaml = require('js-yaml');
const fs = require('fs');

class AICodeReviewer {
  constructor() {
    this.octokit = new Octokit({
      auth: process.env.GITHUB_TOKEN
    });
    this.openai = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY || process.env.API_KEY
    });
    this.prNumber = parseInt(process.env.PR_NUMBER);
    this.repository = process.env.REPOSITORY.split('/');
    this.owner = this.repository[0];
    this.repo = this.repository[1];
  }

  async loadReviewConfig() {
    try {
      const configContent = fs.readFileSync('.github/pr-review-config.yml', 'utf8');
      return yaml.load(configContent);
    } catch (error) {
      return this.getDefaultReviewConfig();
    }
  }

  getDefaultReviewConfig() {
    return {
      review_settings: {
        model: 'gpt-4o-mini',
        max_tokens: 1000,
        temperature: 0.3,
        focus_areas: [
          'security',
          'performance',
          'maintainability',
          'best_practices'
        ],
        languages: {
          javascript: {
            checks: ['async_patterns', 'error_handling', 'memory_leaks'],
            frameworks: ['react', 'node', 'express']
          },
          python: {
            checks: ['pep8', 'security', 'performance'],
            frameworks: ['django', 'flask', 'fastapi']
          }
        },
        severity_levels: {
          critical: '🚨',
          high: '⚠️',
          medium: '💡',
          low: 'ℹ️'
        }
      }
    };
  }

  async reviewPR() {
    const config = await this.loadReviewConfig();
    const pr = await this.getPRDetails();
    const files = await this.getPRFiles();
    
    console.log(`리뷰 시작: PR #${this.prNumber} - ${pr.title}`);
    
    const reviews = [];
    
    for (const file of files) {
      if (this.shouldReviewFile(file, config)) {
        const review = await this.reviewFile(file, config);
        if (review) {
          reviews.push(review);
        }
      }
    }

    await this.postReview(reviews, config);
  }

  async getPRDetails() {
    const { data } = await this.octokit.pulls.get({
      owner: this.owner,
      repo: this.repo,
      pull_number: this.prNumber
    });
    return data;
  }

  async getPRFiles() {
    const { data } = await this.octokit.pulls.listFiles({
      owner: this.owner,
      repo: this.repo,
      pull_number: this.prNumber
    });
    return data;
  }

  shouldReviewFile(file, config) {
    const reviewableExtensions = ['.js', '.ts', '.jsx', '.tsx', '.py', '.java', '.go', '.rs'];
    const hasReviewableExtension = reviewableExtensions.some(ext => 
      file.filename.endsWith(ext)
    );
    
    const isNotDeleted = file.status !== 'removed';
    const hasChanges = file.changes > 0;
    const isNotTooLarge = file.changes < 300; // 너무 큰 파일은 건너뛰기
    
    return hasReviewableExtension && isNotDeleted && hasChanges && isNotTooLarge;
  }

  async reviewFile(file, config) {
    try {
      const patch = file.patch;
      if (!patch) return null;

      const language = this.detectLanguage(file.filename);
      const prompt = this.buildReviewPrompt(file, patch, language, config);

      const response = await this.openai.chat.completions.create({
        model: config.review_settings.model,
        messages: [
          {
            role: 'system',
            content: '당신은 경험 많은 시니어 개발자입니다. 코드 리뷰를 수행하여 보안, 성능, 유지보수성, 베스트 프랙티스 관점에서 건설적인 피드백을 제공하세요.'
          },
          {
            role: 'user',
            content: prompt
          }
        ],
        max_tokens: config.review_settings.max_tokens,
        temperature: config.review_settings.temperature
      });

      const reviewContent = response.choices[0].message.content;
      
      return {
        filename: file.filename,
        review: reviewContent,
        language: language,
        changes: file.changes
      };

    } catch (error) {
      console.error(`파일 리뷰 중 오류: ${file.filename}`, error);
      return null;
    }
  }

  detectLanguage(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const languageMap = {
      'js': 'javascript',
      'jsx': 'javascript',
      'ts': 'typescript',
      'tsx': 'typescript',
      'py': 'python',
      'java': 'java',
      'go': 'go',
      'rs': 'rust'
    };
    return languageMap[ext] || 'unknown';
  }

  buildReviewPrompt(file, patch, language, config) {
    const focusAreas = config.review_settings.focus_areas.join(', ');
    
    return `
파일명: ${file.filename}
언어: ${language}
변경 라인 수: ${file.changes}

다음 코드 변경사항을 리뷰해주세요:

\`\`\`diff
${patch}
\`\`\`

리뷰 포커스: ${focusAreas}

다음 형식으로 응답해주세요:
1. **전체 요약**: 변경사항에 대한 간단한 요약
2. **주요 발견사항**: 중요한 이슈나 개선점 (있는 경우만)
3. **개선 제안**: 구체적인 코드 개선 방안 (있는 경우만)
4. **보안 검토**: 보안 관련 이슈 (있는 경우만)
5. **긍정적 피드백**: 잘 작성된 부분에 대한 인정

각 이슈의 심각도를 🚨(Critical), ⚠️(High), 💡(Medium), ℹ️(Low)로 표시해주세요.
`;
  }

  async postReview(reviews, config) {
    if (reviews.length === 0) {
      await this.postComment('🤖 **AI 코드 리뷰 완료**\n\n리뷰할 파일이 없거나 모든 파일이 양호합니다! ✅');
      return;
    }

    let commentBody = '🤖 **AI 코드 리뷰 결과**\n\n';
    
    // 전체 요약
    commentBody += '## 📊 전체 요약\n';
    commentBody += `- **리뷰된 파일**: ${reviews.length}개\n`;
    commentBody += `- **총 변경 라인**: ${reviews.reduce((sum, r) => sum + r.changes, 0)}개\n\n`;

    // 파일별 리뷰
    commentBody += '## 📝 상세 리뷰\n\n';
    
    for (const review of reviews) {
      commentBody += `### 📄 \`${review.filename}\`\n`;
      commentBody += `**언어**: ${review.language} | **변경**: ${review.changes}줄\n\n`;
      commentBody += review.review + '\n\n';
      commentBody += '---\n\n';
    }

    // 푸터
    commentBody += '> 🤖 이 리뷰는 AI에 의해 생성되었습니다. 추가 질문이나 토론이 필요한 부분이 있다면 언제든 코멘트로 남겨주세요!\n';
    commentBody += `> 📊 **사용된 모델**: ${config.review_settings.model}\n`;

    await this.postComment(commentBody);
  }

  async postComment(body) {
    try {
      await this.octokit.issues.createComment({
        owner: this.owner,
        repo: this.repo,
        issue_number: this.prNumber,
        body: body
      });
      console.log('리뷰 코멘트 작성 완료');
    } catch (error) {
      console.error('코멘트 작성 실패:', error);
    }
  }
}

async function main() {
  try {
    const reviewer = new AICodeReviewer();
    await reviewer.reviewPR();
    console.log('AI 코드 리뷰 완료');
  } catch (error) {
    console.error('AI 코드 리뷰 중 오류:', error);
    process.exit(1);
  }
}

main();
