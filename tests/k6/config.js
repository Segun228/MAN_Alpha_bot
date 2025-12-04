// load_tests/config.js

export const CONFIG = {
    BASE_URL: `http://localhost:${__ENV.GATEWAY_PORT}`,
    BOT_KEY: __ENV.BOT_KEY,
    USER_LOGIN: 'default_login',
    USER_PASSWORD: 'default_password',
};
