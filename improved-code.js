// CodeRabbit 테스트: 개선된 코드 예시
// 이 파일은 sample-code.js의 문제점들을 수정한 버전입니다.

const express = require('express');
const bcrypt = require('bcrypt');
const { validationResult, body } = require('express-validator');

// 1. 개선된 계산 함수 - 함수형 프로그래밍 스타일
const calculateTotal = (items) => {
    if (!Array.isArray(items)) {
        throw new Error('Items must be an array');
    }
    
    return items.reduce((total, item) => {
        if (!item.price || !item.quantity) {
            throw new Error('Invalid item: price and quantity are required');
        }
        return total + (item.price * item.quantity);
    }, 0);
};

// 2. 안전한 데이터베이스 쿼리 - 준비된 문장 사용
const safeQuery = async (db, userInput) => { 
    try {
        const query = 'SELECT * FROM users WHERE name = ?';
        return await db.query(query, [userInput]);
    } catch (error) {
        console.error('Database query failed:', error);
        throw new Error('Database operation failed');
    }
};

// 3. 효율적인 정렬 알고리즘 - 내장 sort 사용
const efficientSort = (arr) => {
    if (!Array.isArray(arr)) {
        throw new Error('Input must be an array');
    }
    
    return [...arr].sort((a, b) => a - b);
};

// 4. 올바른 네이밍 컨벤션
const createUserProfile = (userName, userAge) => {
    const userData = {
        name: userName,
        age: userAge,
        createdAt: new Date(),
    };
    return userData;
};

// 5. 적절한 에러 처리
const safeApiCall = async (url) => {
    try {
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
};

// 6. 환경변수 사용 및 구성 가능한 검증
const CONFIG = {
    MIN_AGE: parseInt(process.env.MIN_AGE) || 18,
    MIN_PASSWORD_LENGTH: parseInt(process.env.MIN_PASSWORD_LENGTH) || 8,
    ADMIN_EMAILS: process.env.ADMIN_EMAILS?.split(',') || [],
};

const validateUser = (user) => {
    const errors = [];
    
    if (user.age < CONFIG.MIN_AGE) {
        errors.push(`User must be at least ${CONFIG.MIN_AGE} years old`);
    }
    
    if (user.password.length < CONFIG.MIN_PASSWORD_LENGTH) {
        errors.push(`Password must be at least ${CONFIG.MIN_PASSWORD_LENGTH} characters long`);
    }
    
    if (!CONFIG.ADMIN_EMAILS.includes(user.email)) {
        errors.push('User is not an authorized admin');
    }
    
    return {
        isValid: errors.length === 0,
        errors
    };
};

// 7. 명확한 함수 분리 및 주석 제거
const processData = (data) => {
    if (!Array.isArray(data)) {
        throw new Error('Data must be an array');
    }
    
    return data.map(item => {
        if (typeof item.value !== 'number') {
            throw new Error('Item value must be a number');
        }
        return item.value * 2;
    });
};

// 8. 가독성 있는 조건문
const checkUserAccess = (user, settings, permissions) => {
    // 기본 검증
    if (!user?.isActive || !settings?.allowAccess || !permissions?.read) {
        return false;
    }
    
    // 권한 검증
    const allowedRoles = ['admin', 'moderator'];
    if (!allowedRoles.includes(user.role)) {
        return false;
    }
    
    // 최근 로그인 검증 (24시간 이내)
    if (!user.lastLogin) {
        return false;
    }
    
    const oneDay = 24 * 60 * 60 * 1000; // 24시간을 밀리초로
    const timeSinceLogin = new Date() - new Date(user.lastLogin);
    
    return timeSinceLogin < oneDay;
};

// 9. 메모리 효율적인 캐시 - Map 사용 및 크기 제한
class CacheManager {
    constructor(maxSize = 100) {
        this.cache = new Map();
        this.maxSize = maxSize;
    }
    
    set(key, value) {
        // 크기 제한 확인
        if (this.cache.size >= this.maxSize) {
            const firstKey = this.cache.keys().next().value;
            this.cache.delete(firstKey);
        }
        
        this.cache.set(key, {
            value,
            timestamp: Date.now()
        });
    }
    
    get(key) {
        const item = this.cache.get(key);
        if (!item) return null;
        
        // 1시간 후 만료
        const oneHour = 60 * 60 * 1000;
        if (Date.now() - item.timestamp > oneHour) {
            this.cache.delete(key);
            return null;
        }
        
        return item.value;
    }
    
    clear() {
        this.cache.clear();
    }
}

// 10. 안전한 동적 실행 - eval 대신 Function 생성자 사용 (제한적)
const safeDynamicExecution = (expression) => {
    // 허용된 연산만 검증
    const allowedPattern = /^[0-9+\-*/\s().]+$/;
    if (!allowedPattern.test(expression)) {
        throw new Error('Invalid expression: only basic math operations are allowed');
    }
    
    try {
        // Function 생성자 사용 (eval보다 안전)
        const fn = new Function('return ' + expression);
        return fn();
    } catch (error) {
        throw new Error('Invalid mathematical expression');
    }
};

// Express.js 미들웨어 예시
const authMiddleware = async (req, res, next) => {
    try {
        const token = req.headers.authorization?.split(' ')[1];
        
        if (!token) {
            return res.status(401).json({ error: 'No token provided' });
        }
        
        // JWT 토큰 검증 로직 (실제 구현에서는 jwt.verify 사용)
        const decoded = await verifyToken(token);
        req.user = decoded;
        next();
    } catch (error) {
        return res.status(401).json({ error: 'Invalid token' });
    }
};

// 입력 검증 미들웨어
const validateUserInput = [
    body('email').isEmail().normalizeEmail(),
    body('password').isLength({ min: 8 }).matches(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/),
    body('name').trim().isLength({ min: 2, max: 50 }),
    
    (req, res, next) => {
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({ errors: errors.array() });
        }
        next();
    }
];

// 캐시 인스턴스 생성
const cacheManager = new CacheManager(50);

module.exports = {
    calculateTotal,
    safeQuery,
    efficientSort,
    createUserProfile,
    safeApiCall,
    validateUser,
    processData,
    checkUserAccess,
    CacheManager,
    cacheManager,
    safeDynamicExecution,
    authMiddleware,
    validateUserInput
};
