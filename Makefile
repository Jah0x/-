up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

backend-shell:
	docker-compose exec backend /bin/sh || true

cli-run:
	cd client/httvps-cli && BACKEND_URL?=http://localhost:8000 && go run . -backend $${BACKEND_URL} -device $${DEVICE_ID} -token $${DEVICE_TOKEN} -target $${TARGET:=example.com:80} -insecure true
