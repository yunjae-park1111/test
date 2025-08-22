// 멀티 AI 리뷰 시스템 테스트용 파일
// 다양한 코드 품질 이슈를 포함하여 AI들의 리뷰 성능을 테스트

const express = require('express');
const mysql = require('mysql');
const app = express();

// 🚨 보안 취약점: SQL Injection 위험
function getUserById(userId) {
    const query = "SELECT * FROM users WHERE id = " + userId;
    connection.query(query, (error, results) => {
        if (error) throw error;
        return results;
    });
}

// ⚠️ 메모리 누수 위험: 이벤트 리스너 정리 안함
function setupWebSocket() {
    const ws = new WebSocket('ws://localhost:8080');
    ws.addEventListener('message', function(event) {
        console.log('Message received:', event.data);
    });
    // 정리 로직 없음
}

// 💡 성능 이슈: 동기 파일 읽기
function loadConfig() {
    const fs = require('fs');
    try {
        const config = fs.readFileSync('./config.json', 'utf8');
        return JSON.parse(config);
    } catch (err) {
        console.log('Config load failed');
        return {};
    }
}

// ℹ️ 코드 스타일 이슈: 일관성 없는 네이밍
const user_data = {};
const configData = {};
const UserService = {};

// 🚨 크리티컬 이슈: 에러 처리 없는 Promise
async function fetchUserData(id) {
    const response = await fetch(`/api/users/${id}`);
    const data = response.json(); // await 누락
    return data;
}

// ⚠️ 타입 체크 없음
function calculateTotal(items) {
    let total = 0;
    for (let item of items) {
        total += item.price * item.quantity;
    }
    return total;
}

// 💡 개선 가능: 함수가 너무 길고 복잡함
function processOrder(order) {
    // 주문 검증
    if (!order || !order.items || order.items.length === 0) {
        throw new Error('Invalid order');
    }
    
    // 재고 확인
    for (let item of order.items) {
        if (inventory[item.id] < item.quantity) {
            throw new Error('Insufficient inventory');
        }
    }
    
    // 할인 적용
    let discount = 0;
    if (order.user.membership === 'premium') {
        discount = 0.1;
    } else if (order.user.membership === 'gold') {
        discount = 0.05;
    }
    
    // 총액 계산
    let total = calculateTotal(order.items);
    total = total * (1 - discount);
    
    // 결제 처리
    const payment = processPayment(total, order.paymentMethod);
    
    // 재고 업데이트
    for (let item of order.items) {
        inventory[item.id] -= item.quantity;
    }
    
    // 주문 저장
    const orderId = saveOrder(order, total);
    
    // 이메일 발송
    sendConfirmationEmail(order.user.email, orderId);
    
    return { orderId, total };
}

// ✅ 좋은 예시: 명확한 함수와 에러 처리
async function validateUser(email, password) {
    try {
        if (!email || !password) {
            throw new Error('Email and password are required');
        }
        
        const user = await User.findByEmail(email);
        if (!user) {
            throw new Error('User not found');
        }
        
        const isValid = await bcrypt.compare(password, user.hashedPassword);
        return { isValid, user: isValid ? user : null };
        
    } catch (error) {
        console.error('User validation failed:', error);
        throw error;
    }
}

module.exports = { getUserById, validateUser, processOrder };
