# Документация HTTVPS

Вся архитектура, спецификации и изменения описаны в каталоге `docs`. Код не содержит комментариев или docstring, поэтому любые пояснения фиксируются здесь.

Структура:
- `00-spec-httvps.md` — основная спецификация протокола
- `00-dev-plan.md` — дорожная карта с задачами Stage 0–8
- `01-architecture-overview.md` — обзор архитектуры и компонентов
- `02-control-plane-api.md` — описание API контрол-плейна
- `03-httvps-protocol.md` — протокол HTTVPS
- `04-gateway-design.md` — дизайн gateway
- `05-outline-pool.md` — управление Outline-пулом
- `06-httvps-cli.md` — справочник по референс-клиенту
- `CHANGELOG.md` — история изменений

## Продакшн-контейнеры

- `backend/Dockerfile.prod` собирает FastAPI-приложение в виртуальном окружении, ставит gunicorn с UvicornWorker и запускает сервис от отдельного пользователя.
- `gateway/Dockerfile.prod` использует многоэтапную сборку Go, выпускает статический бинарник и запускает его в Alpine от непривилегированного пользователя.
- В `Makefile` добавлены цели `backend-image` и `gateway-image`, которые используют продакшн Dockerfile и позволяют переопределять реестр через переменную `REGISTRY`.

## Kubernetes-манифесты и TLS/секреты

- Каталог `deploy/k8s` содержит namespace, Deployment и Service для backend (`backend.yaml`) и gateway (`gateway.yaml`).
- Секреты вынесены в `deploy/k8s/secrets-example.yaml`: `httvps-backend-secrets` хранит DSN и ключи, `httvps-gateway-tls` ожидает base64-кодированные `tls.crt` и `tls.key` для HTTPS на gateway.
- Перед применением манифестов необходимо создать secrets с реальными значениями, например: `kubectl create namespace httvps`, `kubectl create secret generic httvps-backend-secrets --from-literal=BACKEND_DB_DSN=... --from-literal=BACKEND_SECRET_KEY=... --from-literal=BACKEND_GATEWAY_SECRET=... -n httvps`, `kubectl create secret tls httvps-gateway-tls --cert=tls.crt --key=tls.key -n httvps`.
- Переменные окружения в Deployment задают адрес backend для gateway, путь до TLS-секретов и URL WebSocket для backend.

## CI/CD

- Workflow `.github/workflows/ci-cd.yaml` прогоняет Python и Go тесты, а затем собирает и пушит продакшн-образы в GHCR при пуше в `main`.
- Workflow использует `backend/Dockerfile.prod` и `gateway/Dockerfile.prod` и тегирует образы `latest` и SHA-коммитом; реестр определяется через `REGISTRY`.

## Makefile

- Цели `k8s-apply` и `k8s-delete` применяют или удаляют базовые манифесты в namespace `httvps`.
- Значение `REGISTRY` и теги образов можно переопределять при вызове `make backend-image` или `make gateway-image`.
