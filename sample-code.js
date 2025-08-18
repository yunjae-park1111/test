// CodeRabbit 테스트용 샘플 코드
// 다양한 코드 품질 이슈를 포함하여 AI 리뷰 기능을 테스트합니다.

// 1. 기본적인 함수 - 개선 가능한 부분 포함
function calculateTotal(items) {
    let total = 0;
    for (let i = 0; i < items.length; i++) {
        total += items[i].price * items[i].quantity;
    }
    return total;
}

// 2. 보안 취약점 - SQL 인젝션 위험
function unsafeQuery(userInput) {
    const query = "SELECT * FROM users WHERE name = '" + userInput + "'";
    console.log("Executing query:", query); // 프로덕션에서 제거해야 할 로그
    return database.query(query);
}

// 3. 성능 이슈 - 비효율적인 정렬 알고리즘 (버블 정렬)
function inefficientSort(arr) {
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

// 4. 코딩 컨벤션 위반
function bad_naming_function(user_name, user_age) {
    const USER_DATA = {
        name: user_name,
        age: user_age
    };
    return USER_DATA;
}

// 5. 에러 처리 부족
function riskyApiCall(url) {
    const response = fetch(url);
    return response.json();
}

// 6. 하드코딩된 값들
function validateUser(user) {
    if (user.age < 18) {
        return false;
    }
    
    if (user.password.length < 8) {
        return false;
    }
    
    const adminEmails = ["admin@company.com", "super@company.com"];
    return adminEmails.includes(user.email);
}

// 7. 사용되지 않는 변수와 TODO 주석
function processData(data) {
    const unusedVariable = "This variable is never used";
    // TODO: 이 함수를 최적화해야 함
    
    let result = [];
    for (let item of data) {
        result.push(item.value * 2);
    }
    return result;
}

// 8. 복잡한 조건문 - 가독성 저하
function complexCondition(user, settings, permissions) {
    if (user && user.isActive && settings && settings.allowAccess && permissions && permissions.read && (user.role === "admin" || user.role === "moderator") && user.lastLogin && new Date() - new Date(user.lastLogin) < 86400000) {
        return true;
    }
    return false;
}

// 9. 메모리 누수 가능성
let globalCache = {};

function cacheData(key, value) {
    globalCache[key] = value; // 캐시가 계속 누적되어 메모리 누수 가능
}

// 10. 보안 - eval 사용 (매우 위험)
function dynamicExecution(userCode) {
    return eval(userCode); // 극도로 위험한 코드
}

module.exports = {
    calculateTotal,
    unsafeQuery,
    inefficientSort,
    bad_naming_function,
    riskyApiCall,
    validateUser,
    processData,
    complexCondition,
    cacheData,
    dynamicExecution
};
// Additional security test for CodeRabbit


// 🧪 GitHub Actions 테스트를 위한 새 함수 추가
function testAIReview() {
    console.log('AI 리뷰 테스트 함수입니다');
    return 'GitHub Actions + OpenAI API 테스트 중';
}
