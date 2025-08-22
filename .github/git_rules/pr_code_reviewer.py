#!/usr/bin/env python3
"""
PR 코드 리뷰 실행 파일
룰 위반시 코멘트만 남기고 reviewer 설정은 건드리지 않음
"""

import os
import sys
from github import Github
from ai_client_manager import AIClientManager

class PRCodeReviewer:
    """PR 코드 리뷰 실행 클래스"""
    
    def __init__(self):
        self.github = Github(os.environ['GITHUB_TOKEN'])
        self.repo = self.github.get_repo(os.environ['REPOSITORY'])
        self.pr_number = int(os.environ['PR_NUMBER'])
        self.pr = self.repo.get_pull(self.pr_number)
        self.ai_manager = AIClientManager()
    
    def load_template(self, template_name):
        """템플릿 파일 로드"""
        try:
            template_path = f'.github/git_rules/templates/{template_name}'
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return None
    
    def get_file_language(self, filename):
        """파일 확장자로 언어 감지"""
        extensions = {
            '.py': 'python', '.js': 'javascript', '.ts': 'typescript', '.tsx': 'typescript',
            '.java': 'java', '.go': 'go', '.rs': 'rust', '.cpp': 'cpp', '.c': 'c',
            '.php': 'php', '.rb': 'ruby', '.swift': 'swift', '.kt': 'kotlin',
            '.cs': 'csharp', '.html': 'html', '.css': 'css', '.sql': 'sql',
            '.sh': 'shell', '.yml': 'yaml', '.yaml': 'yaml', '.json': 'json'
        }
        ext = os.path.splitext(filename)[1].lower()
        return extensions.get(ext, 'text')
    
    def create_review_prompt(self, file):
        """리뷰 프롬프트 생성"""
        language = self.get_file_language(file.filename)
        
        return f"""파일: {file.filename}, 언어: {language}

코드 변경사항을 리뷰해주세요:
```diff
{file.patch}
```

다음 기준으로 리뷰해주세요:
1. **보안 취약점** - SQL 인젝션, XSS 등
2. **성능 최적화** - 메모리 누수, 비효율적 알고리즘  
3. **코드 품질** - 가독성, 유지보수성
4. **버그 가능성** - 로직 오류, 예외 처리
5. **베스트 프랙티스** - 코딩 컨벤션

**형식:**
- 전체 평가 (1-2줄)
- 주요 발견사항 
- 개선 제안
- 칭찬할 점

간결하고 건설적으로 작성해주세요."""
    
    def perform_review(self):
        """AI 코드 리뷰 수행"""
        files = list(self.pr.get_files())
        if not files:
            print("변경된 파일이 없습니다.")
            return None
        
        print(f"🔍 {len(files)}개 파일에 대한 AI 리뷰 시작")
        
        all_reviews = []
        
        for file in files:
            if file.patch:  # 변경사항이 있는 파일만
                prompt = self.create_review_prompt(file)
                
                # 사용 가능한 AI로 리뷰
                ai_name, ai_display_name = self.ai_manager.get_available_ai()
                if ai_name:
                    review = self.ai_manager.generate_with_ai(
                        ai_name, 
                        prompt, 
                        "당신은 전문적인 코드 리뷰어입니다. 한국어로 건설적인 리뷰를 제공하세요."
                    )
                    
                    if review:
                        all_reviews.append({
                            'filename': file.filename,
                            'ai_name': ai_display_name,
                            'review': review
                        })
                        print(f"  ✅ {file.filename} 리뷰 완료 ({ai_display_name})")
                    else:
                        print(f"  ❌ {file.filename} 리뷰 실패")
                else:
                    print("❌ 사용 가능한 AI가 없습니다.")
                    return None
        
        return all_reviews
    
    def post_review_comment(self, reviews):
        """리뷰 결과를 PR에 코멘트로 작성 (reviewer 설정은 건드리지 않음)"""
        if not reviews:
            return
        
        # 템플릿 로드
        template = self.load_template('code_review_result.md')
        
        if template:
            # 템플릿 사용
            reviews_text = ""
            for i, review_data in enumerate(reviews, 1):
                reviews_text += f"""### 📁 **{review_data['filename']}**
**🔧 리뷰어**: {review_data['ai_name']}

{review_data['review']}

---
"""
            comment_body = template.replace('{reviews}', reviews_text)
        else:
            # 기본 포맷
            comment_body = "## 🤖 **AI 코드 리뷰 결과**\n\n"
            
            for review_data in reviews:
                comment_body += f"""### 📁 **{review_data['filename']}**
**🔧 리뷰어**: {review_data['ai_name']}

{review_data['review']}

---
"""
            
            comment_body += """
### 🤖 **AI 리뷰 정보**
- **🔧 모델**: 멀티 AI 시스템 (GPT-5, Gemini 2.5 Pro, Claude 4 Sonnet)
- **🎯 분석 범위**: 보안, 성능, 품질, 베스트 프랙티스

**Happy Coding! 🚀**"""
        
        try:
            self.pr.create_issue_comment(comment_body)
            print(f"✅ 리뷰 코멘트 작성 완료")
        except Exception as e:
            print(f"❌ 리뷰 코멘트 작성 실패: {e}")
    
    def run(self):
        """메인 실행 함수 - 룰 위반시에도 코멘트만 남김"""
        print(f"🚀 AI 코드 리뷰 시작 - PR #{self.pr_number}")
        
        try:
            reviews = self.perform_review()
            if reviews:
                self.post_review_comment(reviews)
                print("✅ AI 코드 리뷰 완료")
            else:
                print("❌ AI 코드 리뷰 실패")
        
        except Exception as e:
            print(f"❌ AI 코드 리뷰 중 오류: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    reviewer = PRCodeReviewer()
    reviewer.run()
