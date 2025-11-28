from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    outline_nodes: Mapped[list["OutlineNode"]] = relationship("OutlineNode", back_populates="region")
    gateway_nodes: Mapped[list["GatewayNode"]] = relationship("GatewayNode", back_populates="region")
    pool_regions: Mapped[list["OutlinePoolRegion"]] = relationship("OutlinePoolRegion", back_populates="region")
