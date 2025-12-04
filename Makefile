include .env
export

test: ### run k6 tests
	mkdir -p tests/k6/results

	GATEWAY_PORT=8081 BOT_KEY=$(BOT_API_KEY) SCENARIO=smoke_test k6 run tests/k6/smoke_test.js
	GATEWAY_PORT=8081 BOT_KEY=$(BOT_API_KEY) SCENARIO=load_auth k6 run tests/k6/load_auth.js
	GATEWAY_PORT=8081 BOT_KEY=$(BOT_API_KEY) SCENARIO=load_businesses k6 run tests/k6/load_businesses.js
	GATEWAY_PORT=8081 BOT_KEY=$(BOT_API_KEY) SCENARIO=load_chat_model k6 run tests/k6/load_chat-model.js
	GATEWAY_PORT=8081 BOT_KEY=$(BOT_API_KEY) SCENARIO=load_reports k6 run tests/k6/load_reports.js
	GATEWAY_PORT=8081 BOT_KEY=$(BOT_API_KEY) SCENARIO=load_users k6 run tests/k6/load_users.js
.PHONY: test

test-compose-up-down: ### run k6 tests with compose-up and compose-down
	mkdir -p tests/k6/results

	$(MAKE) compose-up
	GATEWAY_PORT=8081 BOT_KEY=$(BOT_API_KEY) SCENARIO=smoke_test k6 run tests/k6/smoke_test.js
	GATEWAY_PORT=8081 BOT_KEY=$(BOT_API_KEY) SCENARIO=load_auth k6 run tests/k6/load_auth.js
	GATEWAY_PORT=8081 BOT_KEY=$(BOT_API_KEY) SCENARIO=load_businesses k6 run tests/k6/load_businesses.js
	GATEWAY_PORT=8081 BOT_KEY=$(BOT_API_KEY) SCENARIO=load_chat_model k6 run tests/k6/load_chat-model.js
	GATEWAY_PORT=8081 BOT_KEY=$(BOT_API_KEY) SCENARIO=load_reports k6 run tests/k6/load_reports.js
	GATEWAY_PORT=8081 BOT_KEY=$(BOT_API_KEY) SCENARIO=load_users k6 run tests/k6/load_users.js
	$(MAKE) compose-down
.PHONY: test-compose-up-down