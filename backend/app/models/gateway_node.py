from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class GatewayNode(Base):
    __tablename__ = "gateway_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    region_id: Mapped[int] = mapped_column(ForeignKey("regions.id", ondelete="SET NULL"))
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    region: Mapped["Region"] = relationship("Region", back_populates="gateway_nodes")
    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="gateway_node")
