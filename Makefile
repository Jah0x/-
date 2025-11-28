REGISTRY ?= ghcr.io/example
BACKEND_IMAGE ?= $(REGISTRY)/httvps-backend:latest
GATEWAY_IMAGE ?= $(REGISTRY)/httvps-gateway:latest
K8S_NAMESPACE ?= httvps

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

backend-image:
	docker build -f backend/Dockerfile.prod -t $(BACKEND_IMAGE) backend

gateway-image:
	docker build -f gateway/Dockerfile.prod -t $(GATEWAY_IMAGE) gateway

k8s-apply:
	kubectl apply -f deploy/k8s/namespace.yaml
	kubectl apply -f deploy/k8s/backend.yaml
	kubectl apply -f deploy/k8s/gateway.yaml

k8s-delete:
	kubectl delete -f deploy/k8s/gateway.yaml || true
	kubectl delete -f deploy/k8s/backend.yaml || true
	kubectl delete -f deploy/k8s/namespace.yaml || true
