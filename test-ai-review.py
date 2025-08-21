#!/usr/bin/env python3
"""
멀티 AI 리뷰 시스템 테스트용 Python 파일
다양한 코드 품질 이슈를 포함하여 AI들의 리뷰 성능을 테스트
"""

import os
import sqlite3
import requests
import hashlib

# 🚨 보안 취약점: SQL Injection 위험
def get_user_by_id(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # 위험한 문자열 포맷팅
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()
    return result

# ⚠️ 보안 이슈: 안전하지 않은 해싱
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

# 💡 성능 이슈: 비효율적인 반복문
def find_duplicates(data_list):
    duplicates = []
    for i in range(len(data_list)):
        for j in range(i + 1, len(data_list)):
            if data_list[i] == data_list[j]:
                duplicates.append(data_list[i])
    return duplicates

# ℹ️ 코딩 스타일: PEP 8 위반
class userManager:
    def __init__(self):
        self.users={}
        
    def addUser(self,user_id,user_data):
        self.users[user_id]=user_data
        
    def getUser(self,user_id):
        return self.users.get(user_id,None)

# 🚨 크리티컬 이슈: 예외 처리 없음
def download_file(url, filename):
    response = requests.get(url)
    with open(filename, 'wb') as file:
        file.write(response.content)
    return filename

# ⚠️ 리소스 관리 이슈: 파일 핸들 누수 위험
def read_config():
    file = open('config.txt', 'r')
    content = file.read()
    # file.close() 누락
    return content

# 💡 개선 가능: 하드코딩된 값들
def calculate_tax(amount):
    if amount < 1000:
        return amount * 0.05
    elif amount < 5000:
        return amount * 0.10
    else:
        return amount * 0.15

# 🚨 보안 취약점: 민감한 정보 하드코딩
API_KEY = "sk-1234567890abcdef"
DB_PASSWORD = "admin123"

class DatabaseManager:
    def __init__(self):
        self.connection = None
    
    def connect(self):
        # 하드코딩된 DB 정보
        self.connection = sqlite3.connect('database.db')
    
    # ⚠️ 메모리 누수: 연결 정리 안함
    def execute_query(self, query):
        cursor = self.connection.cursor()
        result = cursor.execute(query)
        return result.fetchall()

# ℹ️ 코드 복잡도: 너무 긴 함수
def process_data(data, filters, transformations, validations, output_format):
    """복잡하고 긴 함수의 예시"""
    
    # 필터링
    filtered_data = []
    for item in data:
        include = True
        for filter_func in filters:
            if not filter_func(item):
                include = False
                break
        if include:
            filtered_data.append(item)
    
    # 변환
    transformed_data = []
    for item in filtered_data:
        transformed_item = item
        for transform_func in transformations:
            transformed_item = transform_func(transformed_item)
        transformed_data.append(transformed_item)
    
    # 검증
    validated_data = []
    for item in transformed_data:
        is_valid = True
        for validation_func in validations:
            if not validation_func(item):
                is_valid = False
                break
        if is_valid:
            validated_data.append(item)
    
    # 출력 포맷팅
    if output_format == 'json':
        import json
        return json.dumps(validated_data)
    elif output_format == 'csv':
        # CSV 변환 로직
        csv_lines = []
        for item in validated_data:
            csv_lines.append(','.join(str(v) for v in item.values()))
        return '\n'.join(csv_lines)
    else:
        return validated_data

# ✅ 좋은 예시: 깔끔한 함수와 적절한 에러 처리
def safe_divide(a: float, b: float) -> float:
    """
    안전한 나눗셈 함수
    
    Args:
        a: 피제수
        b: 제수
        
    Returns:
        나눗셈 결과
        
    Raises:
        ValueError: b가 0인 경우
    """
    if b == 0:
        raise ValueError("Division by zero is not allowed")
    return a / b

# ✅ 좋은 예시: 컨텍스트 매니저 사용
def read_file_safely(filename: str) -> str:
    """파일을 안전하게 읽는 함수"""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"File {filename} not found")
        return ""
    except Exception as e:
        print(f"Error reading file {filename}: {e}")
        return ""

if __name__ == "__main__":
    # 테스트 코드
    print("AI 리뷰 시스템 테스트 파일")
    test_data = [1, 2, 3, 2, 4, 1, 5]
    duplicates = find_duplicates(test_data)
    print(f"중복 항목: {duplicates}")
