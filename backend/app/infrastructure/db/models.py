"""SQLAlchemy ORM models for Mood Hunter."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class StatusModel(Base):
    __tablename__ = "statuses"

    id: Mapped[int] = mapped_column(
        SmallInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(
        SmallInteger().with_variant(Integer, "sqlite"), default=0, nullable=False
    )

    def __repr__(self) -> str:
        return f"<StatusModel(id={self.id}, code='{self.code}', name='{self.name}')>"


class RequestModel(Base):
    __tablename__ = "requests"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    public_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status_id: Mapped[int] = mapped_column(
        SmallInteger().with_variant(Integer, "sqlite"), ForeignKey("statuses.id"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    # Relationships
    status: Mapped["StatusModel"] = relationship("StatusModel", lazy="joined")
    history: Mapped[list["RequestStatusHistoryModel"]] = relationship(
        "RequestStatusHistoryModel",
        back_populates="request",
        cascade="all, delete-orphan",
        order_by="RequestStatusHistoryModel.changed_at.asc()",
    )

    __table_args__ = (
        Index("idx_requests_status_updated", "status_id", "updated_at"),
        Index("idx_requests_updated", "updated_at"),
    )

    def __repr__(self) -> str:
        return f"<RequestModel(public_id='{self.public_id}', title='{self.title[:30]}...', status='{self.status.code if self.status else self.status_id}')>"


class RequestStatusHistoryModel(Base):
    __tablename__ = "request_status_history"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    request_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("requests.id", ondelete="CASCADE"),
        nullable=False,
    )
    from_status_id: Mapped[Optional[int]] = mapped_column(
        SmallInteger().with_variant(Integer, "sqlite"), ForeignKey("statuses.id"), nullable=True
    )
    to_status_id: Mapped[int] = mapped_column(
        SmallInteger().with_variant(Integer, "sqlite"), ForeignKey("statuses.id"), nullable=False
    )
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    # Relationships
    request: Mapped["RequestModel"] = relationship("RequestModel", back_populates="history")
    from_status: Mapped[Optional["StatusModel"]] = relationship(
        "StatusModel", foreign_keys=[from_status_id], lazy="joined"
    )
    to_status: Mapped["StatusModel"] = relationship(
        "StatusModel", foreign_keys=[to_status_id], lazy="joined"
    )

    __table_args__ = (Index("idx_hist_request", "request_id", "changed_at"),)

    def __repr__(self) -> str:
        from_code = self.from_status.code if self.from_status else "None"
        to_code = self.to_status.code if self.to_status else str(self.to_status_id)
        return f"<RequestStatusHistoryModel(request_id={self.request_id}, {from_code} -> {to_code})>"
