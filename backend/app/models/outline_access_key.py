from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class OutlineAccessKey(Base):
    __tablename__ = "outline_access_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    outline_node_id: Mapped[int] = mapped_column(ForeignKey("outline_nodes.id", ondelete="CASCADE"), nullable=False)
    access_key_id: Mapped[str] = mapped_column(String(128), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    method: Mapped[str | None] = mapped_column(String(100))
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    access_url: Mapped[str | None] = mapped_column(String(255))
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false", default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    device: Mapped["Device"] = relationship("Device")
    outline_node: Mapped["OutlineNode"] = relationship("OutlineNode", back_populates="access_keys")
