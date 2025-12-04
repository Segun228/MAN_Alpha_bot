import http from 'k6/http';
import { check } from 'k6';
import { CONFIG } from './config.js';
import handleSummary from './summary-reporter.js';
export { handleSummary };

export const options = {
    vus: 5,
    duration: '30s',
};

export function setup() {
    const login = `load_biz_user_${__VU}_${Date.now()}`;
    const password = 'password123';

    const createUserPayload = JSON.stringify({
        telegram_id: __VU + Date.now() + Math.round(Math.random() * 10000),
        login: login,
        password: password,
        email: `${login}@example.com`,
    });

    let createUserRes = http.post(`${CONFIG.BASE_URL}/api/users/users`, createUserPayload, {
        headers: { 'Content-Type': 'application/json', 'X-Bot-Key': CONFIG.BOT_KEY },
        tags: { name: 'CreateUser' },
    });

    if (createUserRes.status !== 201) { throw new Error(`Setup failed: could not create user. Status: ${createUserRes.status}`); }
    const userID = createUserRes.json('id');

    check(createUserRes, {
        'User Creation - Status is 201': (r) => r.status === 201,
    });

    const loginRes = http.post(`${CONFIG.BASE_URL}/login`, JSON.stringify({
        login: login,
        password: password,
    }), { headers: { 'Content-Type': 'application/json' } });
    if (loginRes.status !== 200) { throw new Error('Setup failed: could not log in.'); }
    const accessToken = loginRes.json('access_token');

    return { accessToken: accessToken, userID: userID };
}

export default function (data) {
    const authHeaders = { 'Authorization': `Bearer ${data.accessToken}`, 'Content-Type': 'application/json' };

    let getAllUsersRes = http.get(`${CONFIG.BASE_URL}/api/users/users`, { headers: authHeaders });
    check(getAllUsersRes, { 'Get all users (200)': (r) => r.status === 200 });

    // GET /api/users/{id}
    let getUserRes = http.get(`${CONFIG.BASE_URL}/api/users/users/${data.userID}`, { headers: authHeaders });
    check(getUserRes, { 'Get user by ID (200)': (r) => r.status === 200 });

    // PATCH /api/users/{id}
    let patchUserRes = http.patch(`${CONFIG.BASE_URL}/api/users/users/${data.userID}`, JSON.stringify({
        email: `loadtest_updated_${__VU}_${__ITER}@example.com`,
    }), { headers: authHeaders });
    check(patchUserRes, { 'Patch user (200)': (r) => r.status === 200 });
}

// teardown выполняется после завершения всех итераций VU
export function teardown(data) {
    const authHeaders = { 'Authorization': `Bearer ${data.accessToken}` };
    http.del(`${CONFIG.BASE_URL}/api/users/users/${data.userID}`, null, { headers: authHeaders });
    console.log(`Cleaned up user with ID: ${data.userID}`);
}
