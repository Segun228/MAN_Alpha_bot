import http from 'k6/http';
import { check } from 'k6';
import { CONFIG } from './config.js';

export const options = {
    vus: 10,
    duration: '30s',
    thresholds: {
        'checks{scenario:default,name:CreateUser}': ['rate>0.95'],
        'checks{scenario:default,name:LoginUser}': ['rate>0.95'],
    },
};

export default function () {
    const uniqueLogin = `loadtest_user_${Date.now()}_${Math.random() * 1000}`;
    const password = 'password123';

    const createUserPayload = JSON.stringify({
        telegram_id: __VU + __ITER + Date.now() + Math.round(Math.random() * 10000),
        login: uniqueLogin,
        password: password,
        email: `${uniqueLogin}@example.com`,
    });

    let createUserRes = http.post(`${CONFIG.BASE_URL}/api/users/users`, createUserPayload, {
        headers: { 'Content-Type': 'application/json', 'X-Bot-Key': CONFIG.BOT_KEY },
        tags: { name: 'CreateUser' },
    });

    check(createUserRes, {
        'User Creation - Status is 201': (r) => r.status === 201,
    });

    const loginPayload = JSON.stringify({
        login: uniqueLogin,
        password: password,
    });

    let loginRes = http.post(`${CONFIG.BASE_URL}/login`, loginPayload, {
        headers: { 'Content-Type': 'application/json' },
        tags: { name: 'LoginUser' },
    });

    check(loginRes, {
        'User Login - Status is 200': (r) => r.status === 200,
    });
}
