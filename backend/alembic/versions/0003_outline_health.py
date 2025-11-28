from alembic import op
import sqlalchemy as sa

revision = "0003_outline_health"
down_revision = "0002_outline_keys"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("outline_nodes", sa.Column("last_check_at", sa.DateTime(timezone=True)))
    op.add_column(
        "outline_nodes",
        sa.Column("last_check_status", sa.String(length=20), nullable=True, server_default="unknown"),
    )
    op.add_column("outline_nodes", sa.Column("last_error", sa.String(length=255)))
    op.add_column("outline_nodes", sa.Column("recent_latency_ms", sa.Integer()))


def downgrade() -> None:
    op.drop_column("outline_nodes", "recent_latency_ms")
    op.drop_column("outline_nodes", "last_error")
    op.drop_column("outline_nodes", "last_check_status")
    op.drop_column("outline_nodes", "last_check_at")
