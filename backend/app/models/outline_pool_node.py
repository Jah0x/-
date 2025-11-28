from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class OutlinePoolNode(Base):
    __tablename__ = "outline_pool_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pool_id: Mapped[int] = mapped_column(ForeignKey("outline_pools.id", ondelete="CASCADE"), nullable=False)
    outline_node_id: Mapped[int] = mapped_column(ForeignKey("outline_nodes.id", ondelete="CASCADE"), nullable=False)
    priority: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", default=True)
    pool: Mapped["OutlinePool"] = relationship("OutlinePool", back_populates="nodes")
    outline_node: Mapped["OutlineNode"] = relationship("OutlineNode", back_populates="pools")
