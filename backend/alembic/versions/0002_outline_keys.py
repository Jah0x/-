from alembic import op
import sqlalchemy as sa

revision = "0002_outline_keys"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("outline_nodes", sa.Column("name", sa.String(length=100)))
    op.add_column("outline_nodes", sa.Column("api_url", sa.String(length=255)))
    op.add_column("outline_nodes", sa.Column("api_key", sa.String(length=255)))
    op.add_column("outline_nodes", sa.Column("tag", sa.String(length=50)))
    op.add_column("outline_nodes", sa.Column("priority", sa.Integer()))
    op.add_column("outline_nodes", sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"))
    op.create_table(
        "outline_access_keys",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("outline_node_id", sa.Integer(), sa.ForeignKey("outline_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("access_key_id", sa.String(length=128), nullable=False),
        sa.Column("password", sa.String(length=255), nullable=False),
        sa.Column("method", sa.String(length=100)),
        sa.Column("port", sa.Integer(), nullable=False),
        sa.Column("access_url", sa.String(length=255)),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("outline_access_keys")
    op.drop_column("outline_nodes", "is_deleted")
    op.drop_column("outline_nodes", "priority")
    op.drop_column("outline_nodes", "tag")
    op.drop_column("outline_nodes", "api_key")
    op.drop_column("outline_nodes", "api_url")
    op.drop_column("outline_nodes", "name")
