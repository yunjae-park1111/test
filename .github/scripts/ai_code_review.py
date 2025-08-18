#!/usr/bin/env python3

import os
import sys
import yaml
from github import Github
from openai import OpenAI

class AICodeReviewer:
    def __init__(self):
        self.github = Github(os.environ['GITHUB_TOKEN'])
        self.openai_client = OpenAI(
            api_key=os.environ.get('OPENAI_API_KEY') or os.environ.get('API_KEY')
        )
        self.pr_number = int(os.environ['PR_NUMBER'])
        self.repository_name = os.environ['REPOSITORY']
        self.repo = self.github.get_repo(self.repository_name)
    
    def load_review_config(self):
        try:
            with open('.github/pr-review-config.yml', 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return self.get_default_review_config()
    
    def get_default_review_config(self):
        return {
            'review_settings': {
                'model': 'gpt-4o-mini',
                'max_tokens': 1000,
                'temperature': 0.3,
                'focus_areas': ['security', 'performance', 'maintainability', 'best_practices'],
                'languages': {
                    'javascript': {
                        'checks': ['async_patterns', 'error_handling', 'memory_leaks'],
                        'frameworks': ['react', 'node', 'express']
                    },
                    'python': {
                        'checks': ['pep8', 'security', 'performance'],
                        'frameworks': ['django', 'flask', 'fastapi']
                    }
                },
                'severity_levels': {
                    'critical': '🚨',
                    'high': '⚠️',
                    'medium': '💡',
                    'low': 'ℹ️'
                }
            }
        }
    
    def review_pr(self):
        config = self.load_review_config()
        pr = self.repo.get_pull(self.pr_number)
        files = list(pr.get_files())
        
        print(f"리뷰 시작: PR #{self.pr_number} - {pr.title}")
        
        reviews = []
        
        for file in files:
            if self.should_review_file(file, config):
                review = self.review_file(file, config)
                if review:
                    reviews.append(review)
        
        self.post_review(pr, reviews, config)
    
    def should_review_file(self, file, config):
        reviewable_extensions = ['.js', '.ts', '.jsx', '.tsx', '.py', '.java', '.go', '.rs']
        has_reviewable_extension = any(file.filename.endswith(ext) for ext in reviewable_extensions)
        
        is_not_deleted = file.status != 'removed'
        has_changes = file.changes > 0
        is_not_too_large = file.changes < 300  # 너무 큰 파일은 건너뛰기
        
        return has_reviewable_extension and is_not_deleted and has_changes and is_not_too_large
    
    def review_file(self, file, config):
        try:
            if not file.patch:
                return None
            
            language = self.detect_language(file.filename)
            prompt = self.build_review_prompt(file, language, config)
            
            response = self.openai_client.chat.completions.create(
                model=config['review_settings']['model'],
                messages=[
                    {
                        'role': 'system',
                        'content': '당신은 경험 많은 시니어 개발자입니다. 코드 리뷰를 수행하여 보안, 성능, 유지보수성, 베스트 프랙티스 관점에서 건설적인 피드백을 제공하세요.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                max_tokens=config['review_settings']['max_tokens'],
                temperature=config['review_settings']['temperature']
            )
            
            review_content = response.choices[0].message.content
            
            return {
                'filename': file.filename,
                'review': review_content,
                'language': language,
                'changes': file.changes
            }
            
        except Exception as error:
            print(f"파일 리뷰 중 오류: {file.filename} - {error}")
            return None
    
    def detect_language(self, filename):
        ext = filename.split('.')[-1].lower()
        language_map = {
            'js': 'javascript',
            'jsx': 'javascript',
            'ts': 'typescript',
            'tsx': 'typescript',
            'py': 'python',
            'java': 'java',
            'go': 'go',
            'rs': 'rust'
        }
        return language_map.get(ext, 'unknown')
    
    def build_review_prompt(self, file, language, config):
        focus_areas = ', '.join(config['review_settings']['focus_areas'])
        
        return f"""
파일명: {file.filename}
언어: {language}
변경 라인 수: {file.changes}

다음 코드 변경사항을 리뷰해주세요:

```diff
{file.patch}
```

리뷰 포커스: {focus_areas}

다음 형식으로 응답해주세요:
1. **전체 요약**: 변경사항에 대한 간단한 요약
2. **주요 발견사항**: 중요한 이슈나 개선점 (있는 경우만)
3. **개선 제안**: 구체적인 코드 개선 방안 (있는 경우만)
4. **보안 검토**: 보안 관련 이슈 (있는 경우만)
5. **긍정적 피드백**: 잘 작성된 부분에 대한 인정

각 이슈의 심각도를 🚨(Critical), ⚠️(High), 💡(Medium), ℹ️(Low)로 표시해주세요.
"""
    
    def post_review(self, pr, reviews, config):
        if not reviews:
            comment_body = '🤖 **AI 코드 리뷰 완료**\n\n리뷰할 파일이 없거나 모든 파일이 양호합니다! ✅'
            pr.create_issue_comment(comment_body)
            return
        
        comment_body = '🤖 **AI 코드 리뷰 결과**\n\n'
        
        # 전체 요약
        comment_body += '## 📊 전체 요약\n'
        comment_body += f'- **리뷰된 파일**: {len(reviews)}개\n'
        comment_body += f'- **총 변경 라인**: {sum(r["changes"] for r in reviews)}개\n\n'
        
        # 파일별 리뷰
        comment_body += '## 📝 상세 리뷰\n\n'
        
        for review in reviews:
            comment_body += f'### 📄 `{review["filename"]}`\n'
            comment_body += f'**언어**: {review["language"]} | **변경**: {review["changes"]}줄\n\n'
            comment_body += review["review"] + '\n\n'
            comment_body += '---\n\n'
        
        # 푸터
        comment_body += '> 🤖 이 리뷰는 AI에 의해 생성되었습니다. 추가 질문이나 토론이 필요한 부분이 있다면 언제든 코멘트로 남겨주세요!\n'
        comment_body += f'> 📊 **사용된 모델**: {config["review_settings"]["model"]}\n'
        
        try:
            pr.create_issue_comment(comment_body)
            print('리뷰 코멘트 작성 완료')
        except Exception as error:
            print(f'코멘트 작성 실패: {error}')

def main():
    try:
        reviewer = AICodeReviewer()
        reviewer.review_pr()
        print('AI 코드 리뷰 완료')
    except Exception as error:
        print(f'AI 코드 리뷰 중 오류: {error}')
        sys.exit(1)

if __name__ == "__main__":
    main()
