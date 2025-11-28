from app.schemas.nodes import OutlineNodeAssignment


def assign_outline_node(region_code: str | None) -> OutlineNodeAssignment:
    host = "outline.example.com"
    port = 12345
    method = "aes-256-gcm"
    password = "placeholder"
    return OutlineNodeAssignment(host=host, port=port, method=method, password=password, region=region_code)
