#!/usr/bin/env python3
"""
AI 클라이언트 관리 파일
모든 AI 클라이언트 초기화 및 공통 설정 관리
"""

import os
import yaml
import anthropic
import google.generativeai as genai
from openai import OpenAI

class AIClientManager:
    """AI 클라이언트들을 통합 관리하는 클래스"""
    
    def __init__(self):
        self.config = self.load_config()
        self.gpt_client = None
        self.claude_client = None
        self.gemini_client = None
        self.init_clients()
    
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
            'ai_models': {
                'gpt': {'model': 'gpt-5', 'enabled': True, 'max_tokens': 1000, 'temperature': 0.3},
                'claude': {'model': 'claude-4-sonnet', 'enabled': True, 'max_tokens': 1000, 'temperature': 0.3},
                'gemini': {'model': 'gemini-2.5-pro', 'enabled': True, 'max_tokens': 1000, 'temperature': 0.3}
            }
        }
    
    def init_clients(self):
        """모든 AI 클라이언트 초기화"""
        self.init_gpt()
        self.init_claude()
        self.init_gemini()
    
    def init_gpt(self):
        """GPT 클라이언트 초기화"""
        if not self.config.get('ai_models', {}).get('gpt', {}).get('enabled', True):
            return
        
        gpt_key = os.environ.get('OPENAI_API_KEY')
        if gpt_key:
            try:
                import httpx
                self.gpt_client = OpenAI(api_key=gpt_key, http_client=httpx.Client())
                self.gpt_model = self.config['ai_models']['gpt']['model']
                print(f"✅ GPT-5 클라이언트 초기화 완료")
            except Exception as e:
                print(f"❌ GPT 초기화 실패: {e}")
    
    def init_claude(self):
        """Claude 클라이언트 초기화"""
        if not self.config.get('ai_models', {}).get('claude', {}).get('enabled', True):
            return
        
        claude_key = os.environ.get('ANTHROPIC_API_KEY')
        if claude_key:
            try:
                import httpx
                self.claude_client = anthropic.Anthropic(api_key=claude_key, http_client=httpx.Client())
                self.claude_model = self.config['ai_models']['claude']['model']
                print(f"✅ Claude 4 Sonnet 클라이언트 초기화 완료")
            except Exception as e:
                print(f"❌ Claude 초기화 실패: {e}")
    
    def init_gemini(self):
        """Gemini 클라이언트 초기화"""
        if not self.config.get('ai_models', {}).get('gemini', {}).get('enabled', True):
            return
        
        gemini_key = os.environ.get('GEMINI_API_KEY')
        if gemini_key:
            try:
                genai.configure(api_key=gemini_key)
                self.gemini_client = genai.GenerativeModel(self.config['ai_models']['gemini']['model'])
                print(f"✅ Gemini 2.5 Pro 클라이언트 초기화 완료")
            except Exception as e:
                print(f"❌ Gemini 초기화 실패: {e}")
    
    def generate_with_ai(self, ai_name, prompt, system_message="당신은 전문적인 코드 리뷰어입니다."):
        """지정된 AI로 응답 생성"""
        try:
            ai_config = self.config.get('ai_models', {}).get(ai_name, {})
            
            if ai_name == 'gpt' and self.gpt_client:
                response = self.gpt_client.chat.completions.create(
                    model=self.gpt_model,
                    messages=[
                        {'role': 'system', 'content': system_message},
                        {'role': 'user', 'content': prompt}
                    ],
                    max_tokens=ai_config.get('max_tokens', 1000),
                    temperature=ai_config.get('temperature', 0.3)
                )
                return response.choices[0].message.content
            
            elif ai_name == 'claude' and self.claude_client:
                response = self.claude_client.messages.create(
                    model=self.claude_model,
                    max_tokens=ai_config.get('max_tokens', 1000),
                    temperature=ai_config.get('temperature', 0.3),
                    system=system_message,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            
            elif ai_name == 'gemini' and self.gemini_client:
                full_prompt = f"{system_message}\n\n{prompt}"
                response = self.gemini_client.generate_content(full_prompt)
                return response.text
            
        except Exception as e:
            print(f"❌ {ai_name} 응답 생성 실패: {e}")
            return None
    
    def get_available_ai(self):
        """사용 가능한 AI 클라이언트 반환 (우선순위: GPT > Claude > Gemini)"""
        if self.gpt_client:
            return 'gpt', 'GPT-5'
        elif self.claude_client:
            return 'claude', 'Claude 4 Sonnet'
        elif self.gemini_client:
            return 'gemini', 'Gemini 2.5 Pro'
        else:
            return None, None
    
    def get_all_available_ais(self):
        """모든 사용 가능한 AI 클라이언트 목록 반환"""
        available = []
        if self.gpt_client:
            available.append(('gpt', 'GPT-5'))
        if self.claude_client:
            available.append(('claude', 'Claude 4 Sonnet'))
        if self.gemini_client:
            available.append(('gemini', 'Gemini 2.5 Pro'))
        return available

if __name__ == "__main__":
    # 테스트용
    manager = AIClientManager()
    ai_name, display_name = manager.get_available_ai()
    if ai_name:
        print(f"🤖 사용 가능한 AI: {display_name}")
    else:
        print("❌ 사용 가능한 AI가 없습니다.")
