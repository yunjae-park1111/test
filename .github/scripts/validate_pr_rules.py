#!/usr/bin/env python3

import os
import sys
import yaml
import re
from github import Github

class PRRulesValidator:
    def __init__(self):
        self.github = Github(os.environ['GITHUB_TOKEN'])
        self.pr_number = int(os.environ['PR_NUMBER'])
        self.repository_name = os.environ['REPOSITORY']
        self.repo = self.github.get_repo(self.repository_name)
        
    def load_config(self):
        try:
            with open('.github/pr-review-config.yml', 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print("Using default configuration")
            return self.get_default_config()
    
    def get_default_config(self):
        return {
            'pr_rules': {
                'title': {
                    'min_length': 10,
                    'required_patterns': ['^(feat|fix|docs|style|refactor|test|chore):'],
                    'forbidden_patterns': ['wip', 'temp', 'test123']
                },
                'description': {
                    'min_length': 20,
                    'required_sections': ['## 변경사항', '## 테스트']
                },
                'files': {
                    'max_files_changed': 20,
                    'max_lines_changed': 500,
                    'forbidden_paths': ['package-lock.json', '*.log', '.env']
                },
                'commits': {
                    'max_commits': 10,
                    'required_commit_format': '^(feat|fix|docs|style|refactor|test|chore):'
                }
            }
        }
    
    def validate_pr(self):
        config = self.load_config()
        pr = self.repo.get_pull(self.pr_number)
        violations = []
        
        # PR 제목 검증
        violations.extend(self.validate_title(pr.title, config['pr_rules']['title']))
        
        # PR 설명 검증
        violations.extend(self.validate_description(pr.body, config['pr_rules']['description']))
        
        # 파일 변경사항 검증
        violations.extend(self.validate_files(pr, config['pr_rules']['files']))
        
        # 커밋 검증
        violations.extend(self.validate_commits(pr, config['pr_rules']['commits']))
        
        return {
            'passed': len(violations) == 0,
            'violations': violations
        }
    
    def validate_title(self, title, rules):
        violations = []
        
        if len(title) < rules['min_length']:
            violations.append(f"PR 제목이 너무 짧습니다. (최소 {rules['min_length']}자 필요)")
        
        has_required_pattern = any(re.match(pattern, title) for pattern in rules['required_patterns'])
        if not has_required_pattern:
            violations.append(f"PR 제목이 필수 패턴을 만족하지 않습니다: {', '.join(rules['required_patterns'])}")
        
        has_forbidden_pattern = any(pattern.lower() in title.lower() for pattern in rules['forbidden_patterns'])
        if has_forbidden_pattern:
            violations.append(f"PR 제목에 금지된 패턴이 포함되어 있습니다: {', '.join(rules['forbidden_patterns'])}")
        
        return violations
    
    def validate_description(self, description, rules):
        violations = []
        
        if not description or len(description) < rules['min_length']:
            violations.append(f"PR 설명이 너무 짧습니다. (최소 {rules['min_length']}자 필요)")
        
        for section in rules['required_sections']:
            if section not in description:
                violations.append(f"PR 설명에 필수 섹션이 누락되었습니다: {section}")
        
        return violations
    
    def validate_files(self, pr, rules):
        violations = []
        files = list(pr.get_files())
        
        if len(files) > rules['max_files_changed']:
            violations.append(f"변경된 파일 수가 너무 많습니다. ({len(files)}/{rules['max_files_changed']})")
        
        total_changes = sum(file.changes for file in files)
        if total_changes > rules['max_lines_changed']:
            violations.append(f"변경된 라인 수가 너무 많습니다. ({total_changes}/{rules['max_lines_changed']})")
        
        forbidden_files = []
        for file in files:
            for pattern in rules['forbidden_paths']:
                if pattern in file.filename or re.match(pattern.replace('*', '.*'), file.filename):
                    forbidden_files.append(file.filename)
                    break
        
        if forbidden_files:
            violations.append(f"금지된 파일이 포함되어 있습니다: {', '.join(forbidden_files)}")
        
        return violations
    
    def validate_commits(self, pr, rules):
        violations = []
        commits = list(pr.get_commits())
        
        if len(commits) > rules['max_commits']:
            violations.append(f"커밋 수가 너무 많습니다. ({len(commits)}/{rules['max_commits']})")
        
        invalid_commits = [
            commit for commit in commits 
            if not re.match(rules['required_commit_format'], commit.commit.message)
        ]
        
        if invalid_commits:
            violations.append(f"커밋 메시지 형식이 올바르지 않습니다: {rules['required_commit_format']}")
        
        return violations

def main():
    try:
        validator = PRRulesValidator()
        result = validator.validate_pr()
        
        print(f"::set-output name=rules-passed::{str(result['passed']).lower()}")
        
        if not result['passed']:
            violation_message = "\\n- ".join(result['violations'])
            print(f"::set-output name=violation-message::다음 PR 룰을 위반했습니다:\\n- {violation_message}")
        
        sys.exit(0)
    except Exception as error:
        print(f"PR 룰 검증 중 오류 발생: {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()
