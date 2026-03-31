from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy import CheckConstraint, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    posts = relationship("Post", back_populates="author", lazy="selectin")
    votes = relationship("PostVote", back_populates="user", lazy="selectin")


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    # Client-supplied key used to upsert posts through a single endpoint.
    post_key: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    image: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    author = relationship("User", back_populates="posts", lazy="selectin")
    votes = relationship("PostVote", back_populates="post", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("user_id", "post_key", name="uq_posts_user_post_key"),
    )


class PostVote(Base):
    __tablename__ = "post_votes"

    LIKE = 1
    DISLIKE = -1

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), nullable=False, index=True)

    vote_type: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True, default=LIKE, server_default=str(LIKE)
    )
    voted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )

    user = relationship("User", back_populates="votes", lazy="selectin")
    post = relationship("Post", back_populates="votes", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("user_id", "post_id", name="uq_post_votes_user_post"),
        CheckConstraint("vote_type IN (-1, 1)", name="ck_post_votes_vote_type"),
    )


def now_utc() -> datetime:
    # Helper for consistent ordering during vote refresh.
    return datetime.utcnow()


# Re-export constants to avoid importing class attributes everywhere.
LIKE = PostVote.LIKE
DISLIKE = PostVote.DISLIKE
