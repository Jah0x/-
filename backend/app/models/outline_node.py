from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class OutlineNode(Base):
    __tablename__ = "outline_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str | None] = mapped_column(String(100))
    region_id: Mapped[int | None] = mapped_column(ForeignKey("regions.id", ondelete="SET NULL"))
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    method: Mapped[str | None] = mapped_column(String(100))
    password: Mapped[str | None] = mapped_column(String(255))
    api_url: Mapped[str | None] = mapped_column(String(255))
    api_key: Mapped[str | None] = mapped_column(String(255))
    tag: Mapped[str | None] = mapped_column(String(50))
    priority: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false", default=False)
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_check_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_check_status: Mapped[str | None] = mapped_column(String(20), server_default="unknown", default="unknown")
    last_error: Mapped[str | None] = mapped_column(String(255))
    recent_latency_ms: Mapped[int | None] = mapped_column(Integer)
    region: Mapped["Region"] = relationship("Region", back_populates="outline_nodes")
    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="outline_node")
    access_keys: Mapped[list["OutlineAccessKey"]] = relationship("OutlineAccessKey", back_populates="outline_node")
