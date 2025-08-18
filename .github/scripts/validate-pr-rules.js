const { Octokit } = require('@octokit/rest');
const yaml = require('js-yaml');
const fs = require('fs');

class PRRulesValidator {
  constructor() {
    this.octokit = new Octokit({
      auth: process.env.GITHUB_TOKEN
    });
    this.prNumber = parseInt(process.env.PR_NUMBER);
    this.repository = process.env.REPOSITORY.split('/');
    this.owner = this.repository[0];
    this.repo = this.repository[1];
  }

  async loadConfig() {
    try {
      const configContent = fs.readFileSync('.github/pr-review-config.yml', 'utf8');
      return yaml.load(configContent);
    } catch (error) {
      console.log('Using default configuration');
      return this.getDefaultConfig();
    }
  }

  getDefaultConfig() {
    return {
      pr_rules: {
        title: {
          min_length: 10,
          required_patterns: [
            '^(feat|fix|docs|style|refactor|test|chore):'
          ],
          forbidden_patterns: [
            'wip', 'temp', 'test123'
          ]
        },
        description: {
          min_length: 20,
          required_sections: [
            '## 변경사항',
            '## 테스트'
          ]
        },
        files: {
          max_files_changed: 20,
          max_lines_changed: 500,
          forbidden_paths: [
            'package-lock.json',
            '*.log',
            '.env'
          ]
        },
        commits: {
          max_commits: 10,
          required_commit_format: '^(feat|fix|docs|style|refactor|test|chore):'
        }
      }
    };
  }

  async validatePR() {
    const config = await this.loadConfig();
    const pr = await this.getPRDetails();
    const violations = [];

    // PR 제목 검증
    const titleViolations = this.validateTitle(pr.title, config.pr_rules.title);
    violations.push(...titleViolations);

    // PR 설명 검증
    const descriptionViolations = this.validateDescription(pr.body, config.pr_rules.description);
    violations.push(...descriptionViolations);

    // 파일 변경사항 검증
    const fileViolations = await this.validateFiles(config.pr_rules.files);
    violations.push(...fileViolations);

    // 커밋 검증
    const commitViolations = await this.validateCommits(config.pr_rules.commits);
    violations.push(...commitViolations);

    return {
      passed: violations.length === 0,
      violations: violations
    };
  }

  async getPRDetails() {
    const { data } = await this.octokit.pulls.get({
      owner: this.owner,
      repo: this.repo,
      pull_number: this.prNumber
    });
    return data;
  }

  validateTitle(title, rules) {
    const violations = [];

    if (title.length < rules.min_length) {
      violations.push(`PR 제목이 너무 짧습니다. (최소 ${rules.min_length}자 필요)`);
    }

    const hasRequiredPattern = rules.required_patterns.some(pattern => 
      new RegExp(pattern).test(title)
    );
    if (!hasRequiredPattern) {
      violations.push(`PR 제목이 필수 패턴을 만족하지 않습니다: ${rules.required_patterns.join(', ')}`);
    }

    const hasForbiddenPattern = rules.forbidden_patterns.some(pattern => 
      title.toLowerCase().includes(pattern.toLowerCase())
    );
    if (hasForbiddenPattern) {
      violations.push(`PR 제목에 금지된 패턴이 포함되어 있습니다: ${rules.forbidden_patterns.join(', ')}`);
    }

    return violations;
  }

  validateDescription(description, rules) {
    const violations = [];

    if (!description || description.length < rules.min_length) {
      violations.push(`PR 설명이 너무 짧습니다. (최소 ${rules.min_length}자 필요)`);
    }

    rules.required_sections.forEach(section => {
      if (!description.includes(section)) {
        violations.push(`PR 설명에 필수 섹션이 누락되었습니다: ${section}`);
      }
    });

    return violations;
  }

  async validateFiles(rules) {
    const violations = [];

    const { data: files } = await this.octokit.pulls.listFiles({
      owner: this.owner,
      repo: this.repo,
      pull_number: this.prNumber
    });

    if (files.length > rules.max_files_changed) {
      violations.push(`변경된 파일 수가 너무 많습니다. (${files.length}/${rules.max_files_changed})`);
    }

    const totalChanges = files.reduce((sum, file) => sum + file.changes, 0);
    if (totalChanges > rules.max_lines_changed) {
      violations.push(`변경된 라인 수가 너무 많습니다. (${totalChanges}/${rules.max_lines_changed})`);
    }

    const forbiddenFiles = files.filter(file => 
      rules.forbidden_paths.some(pattern => 
        file.filename.includes(pattern) || file.filename.match(new RegExp(pattern))
      )
    );

    if (forbiddenFiles.length > 0) {
      violations.push(`금지된 파일이 포함되어 있습니다: ${forbiddenFiles.map(f => f.filename).join(', ')}`);
    }

    return violations;
  }

  async validateCommits(rules) {
    const violations = [];

    const { data: commits } = await this.octokit.pulls.listCommits({
      owner: this.owner,
      repo: this.repo,
      pull_number: this.prNumber
    });

    if (commits.length > rules.max_commits) {
      violations.push(`커밋 수가 너무 많습니다. (${commits.length}/${rules.max_commits})`);
    }

    const invalidCommits = commits.filter(commit => 
      !new RegExp(rules.required_commit_format).test(commit.commit.message)
    );

    if (invalidCommits.length > 0) {
      violations.push(`커밋 메시지 형식이 올바르지 않습니다: ${rules.required_commit_format}`);
    }

    return violations;
  }
}

async function main() {
  try {
    const validator = new PRRulesValidator();
    const result = await validator.validatePR();

    console.log(`::set-output name=rules-passed::${result.passed}`);
    
    if (!result.passed) {
      const violationMessage = result.violations.join('\n- ');
      console.log(`::set-output name=violation-message::다음 PR 룰을 위반했습니다:\n- ${violationMessage}`);
    }

    process.exit(0);
  } catch (error) {
    console.error('PR 룰 검증 중 오류 발생:', error);
    process.exit(1);
  }
}

main();
