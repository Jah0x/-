import argparse
import asyncio
import json
import os
import sys
import httpx


def get_base_url() -> str:
    return os.getenv("BACKEND_BASE_URL", "http://localhost:8000")


def get_admin_token() -> str:
    token = os.getenv("BACKEND_ADMIN_TOKEN")
    if not token:
        print("BACKEND_ADMIN_TOKEN is not set", file=sys.stderr)
        sys.exit(1)
    return token


def handle_response(response: httpx.Response) -> None:
    if response.status_code >= 400:
        print(f"error {response.status_code}: {response.text}", file=sys.stderr)
        sys.exit(1)
    if response.text:
        try:
            data = response.json()
            print(json.dumps(data, indent=2, ensure_ascii=False))
        except ValueError:
            print(response.text)


async def perform_request(method: str, path: str, payload: dict | None) -> None:
    base_url = get_base_url()
    token = get_admin_token()
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method,
            f"{base_url}{path}",
            headers={"X-Admin-Token": token},
            json=payload,
        )
    handle_response(response)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    plans = subparsers.add_parser("plans")
    plans_sub = plans.add_subparsers(dest="action", required=True)
    plans_sub.add_parser("list")
    plan_create = plans_sub.add_parser("create")
    plan_create.add_argument("--name", required=True)
    plan_create.add_argument("--description")
    plan_create.add_argument("--traffic-limit", type=int)
    plan_create.add_argument("--period-days", type=int)
    plan_create.add_argument("--price", type=float)
    plan_update = plans_sub.add_parser("update")
    plan_update.add_argument("plan_id", type=int)
    plan_update.add_argument("--name")
    plan_update.add_argument("--description")
    plan_update.add_argument("--traffic-limit", type=int)
    plan_update.add_argument("--period-days", type=int)
    plan_update.add_argument("--price", type=float)
    plan_delete = plans_sub.add_parser("delete")
    plan_delete.add_argument("plan_id", type=int)

    regions = subparsers.add_parser("regions")
    regions_sub = regions.add_subparsers(dest="action", required=True)
    regions_sub.add_parser("list")
    region_create = regions_sub.add_parser("create")
    region_create.add_argument("--code", required=True)
    region_create.add_argument("--name", required=True)
    region_update = regions_sub.add_parser("update")
    region_update.add_argument("region_id", type=int)
    region_update.add_argument("--code")
    region_update.add_argument("--name")
    region_delete = regions_sub.add_parser("delete")
    region_delete.add_argument("region_id", type=int)

    outline = subparsers.add_parser("outline-nodes")
    outline_sub = outline.add_subparsers(dest="action", required=True)
    outline_sub.add_parser("list")
    outline_create = outline_sub.add_parser("create")
    outline_create.add_argument("--host", required=True)
    outline_create.add_argument("--port", type=int, required=True)
    outline_create.add_argument("--name")
    outline_create.add_argument("--region")
    outline_create.add_argument("--method")
    outline_create.add_argument("--password")
    outline_create.add_argument("--api-url")
    outline_create.add_argument("--api-key")
    outline_create.add_argument("--tag")
    outline_create.add_argument("--priority", type=int)
    outline_create.add_argument("--inactive", action="store_true")
    outline_update = outline_sub.add_parser("update")
    outline_update.add_argument("node_id", type=int)
    outline_update.add_argument("--host")
    outline_update.add_argument("--port", type=int)
    outline_update.add_argument("--name")
    outline_update.add_argument("--region")
    outline_update.add_argument("--method")
    outline_update.add_argument("--password")
    outline_update.add_argument("--api-url")
    outline_update.add_argument("--api-key")
    outline_update.add_argument("--tag")
    outline_update.add_argument("--priority", type=int)
    outline_update.add_argument("--active", action="store_true")
    outline_update.add_argument("--inactive", action="store_true")
    outline_delete = outline_sub.add_parser("delete")
    outline_delete.add_argument("node_id", type=int)

    gateway = subparsers.add_parser("gateway-nodes")
    gateway_sub = gateway.add_subparsers(dest="action", required=True)
    gateway_sub.add_parser("list")
    gateway_create = gateway_sub.add_parser("create")
    gateway_create.add_argument("--host", required=True)
    gateway_create.add_argument("--port", type=int, required=True)
    gateway_create.add_argument("--region")
    gateway_create.add_argument("--inactive", action="store_true")
    gateway_update = gateway_sub.add_parser("update")
    gateway_update.add_argument("node_id", type=int)
    gateway_update.add_argument("--host")
    gateway_update.add_argument("--port", type=int)
    gateway_update.add_argument("--region")
    gateway_update.add_argument("--active", action="store_true")
    gateway_update.add_argument("--inactive", action="store_true")
    gateway_delete = gateway_sub.add_parser("delete")
    gateway_delete.add_argument("node_id", type=int)

    audit = subparsers.add_parser("audit")
    audit.add_argument("--limit", type=int, default=100)

    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    if args.command == "plans":
        if args.action == "list":
            await perform_request("GET", "/api/v1/admin/plans", None)
        elif args.action == "create":
            payload = {
                "name": args.name,
                "description": args.description,
                "traffic_limit": args.traffic_limit,
                "period_days": args.period_days,
                "price": args.price,
            }
            await perform_request("POST", "/api/v1/admin/plans", payload)
        elif args.action == "update":
            payload = {}
            for key in ["name", "description", "traffic_limit", "period_days", "price"]:
                value = getattr(args, key)
                if value is not None:
                    payload[key] = value
            await perform_request("PUT", f"/api/v1/admin/plans/{args.plan_id}", payload)
        elif args.action == "delete":
            await perform_request("DELETE", f"/api/v1/admin/plans/{args.plan_id}", None)
    elif args.command == "regions":
        if args.action == "list":
            await perform_request("GET", "/api/v1/admin/regions", None)
        elif args.action == "create":
            payload = {"code": args.code, "name": args.name}
            await perform_request("POST", "/api/v1/admin/regions", payload)
        elif args.action == "update":
            payload = {}
            for key in ["code", "name"]:
                value = getattr(args, key)
                if value is not None:
                    payload[key] = value
            await perform_request("PUT", f"/api/v1/admin/regions/{args.region_id}", payload)
        elif args.action == "delete":
            await perform_request("DELETE", f"/api/v1/admin/regions/{args.region_id}", None)
    elif args.command == "outline-nodes":
        if args.action == "list":
            await perform_request("GET", "/api/v1/admin/outline-nodes", None)
        elif args.action == "create":
            payload = {
                "host": args.host,
                "port": args.port,
                "name": args.name,
                "region_code": args.region,
                "method": args.method,
                "password": args.password,
                "api_url": args.api_url,
                "api_key": args.api_key,
                "tag": args.tag,
                "priority": args.priority,
                "is_active": not args.inactive,
            }
            await perform_request("POST", "/api/v1/admin/outline-nodes", payload)
        elif args.action == "update":
            payload = {}
            for key, arg_key in [
                ("host", "host"),
                ("port", "port"),
                ("name", "name"),
                ("region_code", "region"),
                ("method", "method"),
                ("password", "password"),
                ("api_url", "api_url"),
                ("api_key", "api_key"),
                ("tag", "tag"),
                ("priority", "priority"),
            ]:
                value = getattr(args, arg_key)
                if value is not None:
                    payload[key] = value
            if args.active:
                payload["is_active"] = True
            if args.inactive:
                payload["is_active"] = False
            await perform_request("PUT", f"/api/v1/admin/outline-nodes/{args.node_id}", payload)
        elif args.action == "delete":
            await perform_request("DELETE", f"/api/v1/admin/outline-nodes/{args.node_id}", None)
    elif args.command == "gateway-nodes":
        if args.action == "list":
            await perform_request("GET", "/api/v1/admin/gateway-nodes", None)
        elif args.action == "create":
            payload = {
                "host": args.host,
                "port": args.port,
                "region_code": args.region,
                "is_active": not args.inactive,
            }
            await perform_request("POST", "/api/v1/admin/gateway-nodes", payload)
        elif args.action == "update":
            payload = {}
            for key, arg_key in [("host", "host"), ("port", "port"), ("region_code", "region")]:
                value = getattr(args, arg_key)
                if value is not None:
                    payload[key] = value
            if args.active:
                payload["is_active"] = True
            if args.inactive:
                payload["is_active"] = False
            await perform_request("PUT", f"/api/v1/admin/gateway-nodes/{args.node_id}", payload)
        elif args.action == "delete":
            await perform_request("DELETE", f"/api/v1/admin/gateway-nodes/{args.node_id}", None)
    elif args.command == "audit":
        await perform_request("GET", f"/api/v1/admin/audit?limit={args.limit}", None)


if __name__ == "__main__":
    asyncio.run(main())
