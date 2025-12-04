include .env
export

compose-up: ### Run docker-compose
	docker-compose up --build -d
.PHONY: compose-up

compose-down: ### Down docker-compose
	docker-compose down --remove-orphans
.PHONY: compose-down

compose-down-v: ### Down docker-compose and remove volumes
	docker-compose down -v --remove-orphans
.PHONY: compose-down

docker-rm-volume: ### remove docker volume
	docker volume rm postgres-data
.PHONY: docker-rm-volume

test: ### run k6 tests
	GATEWAY_PORT=8081 BOT_KEY=$(BOT_API_KEY) k6 run tests/k6/smoke_test.js --out json=tests/k6/results/smoke_test_result.json
	GATEWAY_PORT=8081 BOT_KEY=$(BOT_API_KEY) k6 run tests/k6/load_auth.js --out json=tests/k6/results/load_auth_result.json
	GATEWAY_PORT=8081 BOT_KEY=$(BOT_API_KEY) k6 run tests/k6/load_businesses.js --out json=tests/k6/results/load_businesses_result.json
	GATEWAY_PORT=8081 BOT_KEY=$(BOT_API_KEY) k6 run tests/k6/load_chat-model.js --out json=tests/k6/results/load_chat_model_result.json
	GATEWAY_PORT=8081 BOT_KEY=$(BOT_API_KEY) k6 run tests/k6/load_reports.js --out json=tests/k6/results/load_reports_result.json
	GATEWAY_PORT=8081 BOT_KEY=$(BOT_API_KEY) k6 run tests/k6/load_users.js --out json=tests/k6/results/load_users_result.json
.PHONY: test

test-compose-up-down: ### run k6 tests with compose-up and compose-down
	$(MAKE) compose-up
	GATEWAY_PORT=8081 BOT_KEY=$(BOT_API_KEY) k6 run tests/k6/smoke_test.js --out json=tests/k6/results/smoke_test_result.json
	GATEWAY_PORT=8081 BOT_KEY=$(BOT_API_KEY) k6 run tests/k6/load_auth.js --out json=tests/k6/results/load_auth_result.json
	GATEWAY_PORT=8081 BOT_KEY=$(BOT_API_KEY) k6 run tests/k6/load_businesses.js --out json=tests/k6/results/load_businesses_result.json
	GATEWAY_PORT=8081 BOT_KEY=$(BOT_API_KEY) k6 run tests/k6/load_chat-model.js --out json=tests/k6/results/load_chat_model_result.json
	GATEWAY_PORT=8081 BOT_KEY=$(BOT_API_KEY) k6 run tests/k6/load_reports.js --out json=tests/k6/results/load_reports_result.json
	GATEWAY_PORT=8081 BOT_KEY=$(BOT_API_KEY) k6 run tests/k6/load_users.js --out json=tests/k6/results/load_users_result.json
	$(MAKE) compose-down
.PHONY: test-compose-up-down