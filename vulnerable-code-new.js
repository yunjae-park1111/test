// NEW FILE: CodeRabbit 보안 취약점 테스트용 파일
// 이 파일은 의도적으로 다양한 보안 문제를 포함합니다.

const express = require('express');
const app = express();

// 1. 심각한 보안 취약점 - SQL 인젝션
function loginUser(username, password) {
    const query = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password + "'";
    console.log("Executing dangerous query:", query);
    return database.query(query);
}

// 2. 매우 위험한 eval() 사용
function executeUserCode(userInput) {
    console.log("About to execute user code:", userInput);
    return eval(userInput); // 극도로 위험!
}

// 3. 하드코딩된 민감한 정보
const API_KEY = "sk-1234567890abcdef";
const DATABASE_PASSWORD = "admin123";
const SECRET_TOKEN = "supersecret";

// 4. XSS 취약점
function renderUserContent(userHTML) {
    document.getElementById('content').innerHTML = userHTML; // XSS 위험
}

// 5. 비효율적인 O(n²) 알고리즘
function slowSort(arr) {
    for (let i = 0; i < arr.length; i++) {
        for (let j = 0; j < arr.length - 1; j++) {
            if (arr[j] > arr[j + 1]) {
                let temp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = temp;
            }
        }
    }
    return arr;
}

// 6. 에러 처리 전혀 없음
function dangerousApiCall(url) {
    const response = fetch(url);
    return response.json(); // 에러 처리 없음
}

// 7. 입력 검증 부족
function processUserData(data) {
    return data.toUpperCase(); // data가 undefined/null일 수 있음
}

// 8. 보안되지 않은 랜덤값 생성
function generateSecretKey() {
    return Math.random().toString(36); // 암호학적으로 안전하지 않음
}

// 9. 무한루프 위험
function riskyLoop(userNumber) {
    while (userNumber > 0) {
        console.log(userNumber);
        // userNumber 감소 로직 없음 - 무한루프 위험
    }
}

// 10. 파일 시스템 접근 취약점
const fs = require('fs');
function readUserFile(filename) {
    return fs.readFileSync(filename); // 경로 순회 공격 가능
}

module.exports = {
    loginUser,
    executeUserCode,
    API_KEY,
    DATABASE_PASSWORD,
    SECRET_TOKEN,
    renderUserContent,
    slowSort,
    dangerousApiCall,
    processUserData,
    generateSecretKey,
    riskyLoop,
    readUserFile
};
