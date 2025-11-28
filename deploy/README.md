# Deploy

Каталог содержит артефакты для развёртывания HTTVPS в Kubernetes.

- `k8s/namespace.yaml` создаёт namespace `httvps`.
- `k8s/backend.yaml` разворачивает backend и сервис на порту 8000.
- `k8s/gateway.yaml` разворачивает gateway с TLS-секретом и сервисом на 8443.
- `k8s/secrets-example.yaml` показывает структуру секретов: DSN и ключи для backend и TLS-пара для gateway.

Минимальный порядок действий:
1. Создать namespace и секреты (`httvps-backend-secrets`, `httvps-gateway-tls`).
2. Применить Deployments и Services: `make k8s-apply` или `kubectl apply -f deploy/k8s`.
3. Обновить переменные окружения в манифестах под конкретный стенд при необходимости.
