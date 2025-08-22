#!/usr/bin/env python3
"""
PR 룰 체크 파일
PR 제목, 설명 등의 규칙을 검증
"""

import os
import yaml
from github import Github

class PRRulesChecker:
    """PR 규칙 검증 클래스"""
    
    def __init__(self):
        self.github = Github(os.environ['GITHUB_TOKEN'])
        self.repo = self.github.get_repo(os.environ['REPOSITORY'])
        self.pr_number = int(os.environ['PR_NUMBER'])
        self.pr = self.repo.get_pull(self.pr_number)
        self.config = self.load_config()
    
    def load_config(self):
        """설정 파일 로드"""
        try:
            config_files = ['.github/pr-review-config.yml', '.github/git_rules/templates/config.yml']
            for config_file in config_files:
                if os.path.exists(config_file):
                    with open(config_file, 'r', encoding='utf-8') as f:
                        return yaml.safe_load(f)
        except:
            pass
        
        # 기본 설정
        return {
            'pr_rules': {
                'title': {'min_length': 10},
                'description': {'min_length': 20}
            }
        }
    
    def validate_title(self):
        """제목 규칙 검증"""
        violations = []
        title_rules = self.config.get('pr_rules', {}).get('title', {})
        
        if 'min_length' in title_rules:
            if len(self.pr.title) < title_rules['min_length']:
                violations.append(f"제목이 너무 짧습니다 (최소 {title_rules['min_length']}자 필요, 현재 {len(self.pr.title)}자)")
        
        return violations
    
    def validate_description(self):
        """설명 규칙 검증"""
        violations = []
        desc_rules = self.config.get('pr_rules', {}).get('description', {})
        
        if 'min_length' in desc_rules:
            desc_length = len(self.pr.body or '')
            if desc_length < desc_rules['min_length']:
                violations.append(f"설명이 너무 짧습니다 (최소 {desc_rules['min_length']}자 필요, 현재 {desc_length}자)")
        
        return violations
    
    def validate_all(self):
        """모든 PR 규칙 검증"""
        all_violations = []
        
        # 제목 검증
        all_violations.extend(self.validate_title())
        
        # 설명 검증
        all_violations.extend(self.validate_description())
        
        return {
            'passed': len(all_violations) == 0,
            'violations': all_violations
        }
    
    def load_template(self, template_name):
        """템플릿 파일 로드"""
        try:
            template_path = f'.github/git_rules/templates/{template_name}'
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return None
    
    def post_violation_comment(self, violations):
        """위반 메시지를 PR에 코멘트로 작성"""
        template = self.load_template('pr_rule_violation.md')
        
        if template:
            violations_list = ""
            for violation in violations:
                violations_list += f"- {violation}\n"
            comment_body = template.replace('{violations}', violations_list)
        else:
            comment_body = f"""## ❌ PR 룰 위반이 감지되었습니다

**위반 사항:**
{chr(10).join(f"- {v}" for v in violations)}

수정 후 다시 제출해주세요."""
        
        try:
            self.pr.create_issue_comment(comment_body)
            print(f"✅ PR 위반 메시지 작성 완료")
        except Exception as e:
            print(f"❌ PR 위반 메시지 작성 실패: {e}")
    
    def run(self):
        """메인 실행 함수"""
        print(f"🔍 PR 규칙 검증 시작 - PR #{self.pr_number}")
        
        result = self.validate_all()
        
        if result['passed']:
            print("✅ PR 규칙 검증 통과")
            print("::set-output name=rules-passed::true")
        else:
            print(f"❌ PR 규칙 위반 감지: {len(result['violations'])}개")
            for violation in result['violations']:
                print(f"  - {violation}")
            
            # 위반 메시지 바로 작성
            self.post_violation_comment(result['violations'])
            
            print("::set-output name=rules-passed::false")
        
        return result

if __name__ == "__main__":
    checker = PRRulesChecker()
    checker.run()
