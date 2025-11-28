from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class OutlinePool(Base):
    __tablename__ = "outline_pools"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false", default=False)
    nodes: Mapped[list["OutlinePoolNode"]] = relationship("OutlinePoolNode", back_populates="pool")
    regions: Mapped[list["OutlinePoolRegion"]] = relationship("OutlinePoolRegion", back_populates="pool")
