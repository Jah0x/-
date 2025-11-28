from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    outline_node_id: Mapped[int | None] = mapped_column(ForeignKey("outline_nodes.id", ondelete="SET NULL"))
    gateway_node_id: Mapped[int | None] = mapped_column(ForeignKey("gateway_nodes.id", ondelete="SET NULL"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    bytes_up: Mapped[int] = mapped_column(BigInteger, default=0)
    bytes_down: Mapped[int] = mapped_column(BigInteger, default=0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    device: Mapped["Device"] = relationship("Device", back_populates="sessions")
    outline_node: Mapped["OutlineNode"] = relationship("OutlineNode", back_populates="sessions")
    gateway_node: Mapped["GatewayNode"] = relationship("GatewayNode", back_populates="sessions")
