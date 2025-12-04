// load_tests/smoke_test.js

import http from 'k6/http';
import { check, sleep } from 'k6';
import { CONFIG } from './config.js';

export const options = {
    vus: 1,
    iterations: 1,
    thresholds: {
        // Мы ожидаем, что 100% проверок в smoke-тесте пройдут успешно
        'checks': ['rate==1.0'],
    },
};

export default function () {
    console.log('--- Starting Smoke Test ---');

    // --- 1. User Creation ---
    const uniqueLogin = `smokeuser_${Date.now()}`;
    const userPassword = 'password123';
    let userRes = http.post(`${CONFIG.BASE_URL}/api/users/users`, JSON.stringify({
        telegram_id: Date.now(),
        login: uniqueLogin,
        password: userPassword,
        email: `${uniqueLogin}@example.com`,
    }), {
        headers: { 'Content-Type': 'application/json', 'X-Bot-Key': CONFIG.BOT_KEY },
    });
    check(userRes, { 'User created (201)': (r) => r.status === 201 });
    if (userRes.status !== 201) {
        console.error(`Smoke test failed at User Creation. Status: ${userRes.status}, Body: ${userRes.body}`);
        return;
    }
    const userID = userRes.json('id');
    console.log(`User created with ID: ${userID}`);

    // --- 2. Login ---
    let loginRes = http.post(`${CONFIG.BASE_URL}/login`, JSON.stringify({
        login: uniqueLogin,
        password: userPassword,
    }), { headers: { 'Content-Type': 'application/json' } });
    check(loginRes, { 'Login successful (200)': (r) => r.status === 200 });
    if (loginRes.status !== 200) {
        console.error(`Smoke test failed at Login. Status: ${loginRes.status}, Body: ${loginRes.body}`);
        return;
    }
    const accessToken = loginRes.json('access_token');
    const authHeaders = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
    };
    console.log('Login successful.');

    // --- 3. Business Operations ---
    const businessName = `Smoke Biz ${Date.now()}`;
    let addBizRes = http.post(`${CONFIG.BASE_URL}/api/users/users/${userID}/businesses`, JSON.stringify({
        name: businessName,
        description: "Smoke test business",
    }), { headers: authHeaders });
    check(addBizRes, { 'Add Business (200)': (r) => r.status === 200 });
    const businesses = addBizRes.json('businesses');
    const businessID = businesses && businesses.length > 0 ? businesses[businesses.length - 1].id : null;
    console.log(`Business added with ID: ${businessID}`);

    // --- 4. Report Operations ---
    let addReportRes = http.post(`${CONFIG.BASE_URL}/api/users/reports`, JSON.stringify({
        name: `Smoke Report ${Date.now()}`,
        user_id: userID, users: 100, customers: 10, avp: 150.5, apc: 2, tms: 50000, cogs: 10000, cogs1s: 5000, fc: 20000, rr: 0.8, agr: 0.1
    }), { headers: authHeaders });
    check(addReportRes, { 'Add Report (201)': (r) => r.status === 201 });
    const reportID = addReportRes.json('id');
    console.log(`Report added with ID: ${reportID}`);

    // --- 5. Chat Model ---
    let chatRes = http.post(`${CONFIG.BASE_URL}/models/chat/generate_response`, JSON.stringify({
        text: "Кратко расскажи, что такое MVP в бизнесе.",
        context: { history: [] }
    }), { headers: authHeaders });
    check(chatRes, { 'Chat Model (200)': (r) => r.status === 200, 'Chat Model response not empty': (r) => r.json('response').length > 0 });
    console.log('Chat Model responded.');

    // --- 6. Cleanup ---
    if (reportID) {
        let delReportRes = http.del(`${CONFIG.BASE_URL}/api/users/reports/${reportID}`, null, { headers: authHeaders });
        check(delReportRes, { 'Delete Report (204)': (r) => r.status === 204 });
        console.log('Report deleted.');
    }
    if (businessID) {
        let delBizRes = http.del(`${CONFIG.BASE_URL}/api/users/businesses/${businessID}`, null, { headers: authHeaders });
        check(delBizRes, { 'Delete Business (200)': (r) => r.status === 200 });
        console.log('Business deleted.');
    }
    if (userID) {
        let delUserRes = http.del(`${CONFIG.BASE_URL}/api/users/users/${userID}`, null, { headers: authHeaders });
        check(delUserRes, { 'Delete User (204)': (r) => r.status === 204 });
        console.log('User deleted.');
    }

    console.log('--- Smoke Test Completed Successfully ---');
    sleep(1);
}
