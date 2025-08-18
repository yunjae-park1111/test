// GitHub Actions + OpenAI API 가이드 검증 테스트 스크립트

console.log('🧪 GitHub Actions + OpenAI API 가이드 검증 테스트 시작\n');

// 1. 필수 모듈 import 테스트
console.log('1. 📦 필수 모듈 import 테스트');
try {
  const { Octokit } = require('@octokit/rest');
  const yaml = require('js-yaml');
  const fs = require('fs');
  console.log('✅ @octokit/rest 모듈 로드 성공');
  console.log('✅ js-yaml 모듈 로드 성공');
  console.log('✅ fs 모듈 로드 성공');
} catch (error) {
  console.error('❌ 모듈 로드 실패:', error.message);
}

// 2. 설정 파일 검증
console.log('\n2. ⚙️ 설정 파일 검증');
try {
  const yaml = require('js-yaml');
  const fs = require('fs');
  
  const configContent = fs.readFileSync('.github/pr-review-config.yml', 'utf8');
  const config = yaml.load(configContent);
  
  // 필수 설정 항목 확인
  const requiredKeys = ['pr_rules', 'review_settings'];
  const missingKeys = requiredKeys.filter(key => !config[key]);
  
  if (missingKeys.length === 0) {
    console.log('✅ 설정 파일 구조 정상');
    console.log(`✅ PR 룰 설정: ${Object.keys(config.pr_rules).length}개 항목`);
    console.log(`✅ AI 리뷰 설정: ${config.review_settings.model} 모델 사용`);
  } else {
    console.error('❌ 누락된 설정:', missingKeys);
  }
} catch (error) {
  console.error('❌ 설정 파일 읽기 실패:', error.message);
}

// 3. JavaScript 스크립트 문법 검증
console.log('\n3. 📝 JavaScript 스크립트 문법 검증');
const scripts = [
  '.github/scripts/validate-pr-rules.js',
  '.github/scripts/ai-code-review.js',
  '.github/scripts/handle-violation.js'
];

scripts.forEach(script => {
  try {
    require('child_process').execSync(`node -c ${script}`, { encoding: 'utf8' });
    console.log(`✅ ${script.split('/').pop()} 문법 정상`);
  } catch (error) {
    console.error(`❌ ${script.split('/').pop()} 문법 오류:`, error.message);
  }
});

// 4. GitHub Actions 워크플로우 검증
console.log('\n4. 🔄 GitHub Actions 워크플로우 검증');
try {
  const yaml = require('js-yaml');
  const fs = require('fs');
  
  const workflowContent = fs.readFileSync('.github/workflows/pr-review.yml', 'utf8');
  const workflow = yaml.load(workflowContent);
  
  // 필수 요소 확인
  if (workflow.on && workflow.jobs && workflow.jobs['pr-review']) {
    console.log('✅ 워크플로우 구조 정상');
    console.log(`✅ 트리거 이벤트: ${Object.keys(workflow.on).join(', ')}`);
    console.log(`✅ 실행 단계: ${workflow.jobs['pr-review'].steps.length}개`);
  } else {
    console.error('❌ 워크플로우 구조 불완전');
  }
} catch (error) {
  console.error('❌ 워크플로우 파일 검증 실패:', error.message);
}

// 5. 파일 구조 검증
console.log('\n5. 📁 파일 구조 검증');
const requiredFiles = [
  '.github/workflows/pr-review.yml',
  '.github/scripts/validate-pr-rules.js',
  '.github/scripts/ai-code-review.js',
  '.github/scripts/handle-violation.js',
  '.github/pr-review-config.yml'
];

requiredFiles.forEach(file => {
  const fs = require('fs');
  if (fs.existsSync(file)) {
    const stats = fs.statSync(file);
    console.log(`✅ ${file} (${Math.round(stats.size / 1024)}KB)`);
  } else {
    console.error(`❌ ${file} 파일 없음`);
  }
});

// 6. sample-code.js 검증 (테스트용 파일)
console.log('\n6. 🔍 테스트 파일 검증');
try {
  const fs = require('fs');
  const sampleCode = fs.readFileSync('sample-code.js', 'utf8');
  
  // 보안 취약점 패턴 확인
  const vulnerabilityPatterns = [
    { pattern: /eval\s*\(/, name: 'eval() 함수 사용' },
    { pattern: /\.innerHTML\s*=/, name: 'innerHTML 직접 할당' },
    { pattern: /SELECT.*\+.*userInput/, name: 'SQL 인젝션 패턴' },
    { pattern: /console\.log/, name: '디버그 로그' }
  ];
  
  const foundVulnerabilities = vulnerabilityPatterns.filter(v => v.pattern.test(sampleCode));
  
  if (foundVulnerabilities.length > 0) {
    console.log('✅ 테스트용 취약점 패턴 확인됨:');
    foundVulnerabilities.forEach(v => {
      console.log(`  • ${v.name}`);
    });
  } else {
    console.log('⚠️ 테스트용 취약점 패턴이 발견되지 않음');
  }
} catch (error) {
  console.error('❌ 테스트 파일 검증 실패:', error.message);
}

console.log('\n🎉 GitHub Actions + OpenAI API 가이드 검증 테스트 완료!');
console.log('\n📋 다음 단계:');
console.log('1. GitHub Secrets에 API_KEY 등록 확인');
console.log('2. yunjae-park1111/test 리포지토리에 파일들 푸시');
console.log('3. 테스트 PR 생성하여 실제 동작 확인');
