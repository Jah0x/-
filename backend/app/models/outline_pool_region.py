from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class OutlinePoolRegion(Base):
    __tablename__ = "outline_pool_regions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pool_id: Mapped[int] = mapped_column(ForeignKey("outline_pools.id", ondelete="CASCADE"), nullable=False)
    region_id: Mapped[int] = mapped_column(ForeignKey("regions.id", ondelete="CASCADE"), nullable=False)
    priority: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", default=True)
    pool: Mapped["OutlinePool"] = relationship("OutlinePool", back_populates="regions")
    region: Mapped["Region"] = relationship("Region", back_populates="pool_regions")
