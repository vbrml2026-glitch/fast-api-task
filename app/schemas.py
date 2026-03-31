from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)


class LoginRequest(BaseModel):
    username_or_email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


class UserPublicOut(BaseModel):
    id: int
    username: str


class UserFullOut(UserPublicOut):
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    created_at: datetime
    updated_at: datetime
    is_active: bool


class UserOut(UserPublicOut):
    # Same endpoint returns either public or full info depending on authorization.
    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    is_active: bool | None = None


class PostOut(BaseModel):
    id: int
    user_id: int
    post_key: str
    title: str
    content: str
    created_at: datetime
    updated_at: datetime


class VoterSummaryOut(BaseModel):
    id: int
    username: str


class PostAggregatesOut(PostOut):
    likes_count: int
    dislikes_count: int
    recently_liked_users: list[VoterSummaryOut]
    recently_disliked_users: list[VoterSummaryOut]


class PostByUserResponse(BaseModel):
    page: int
    page_size: int
    total: int
    posts: list[PostAggregatesOut]


class VoteRequest(BaseModel):
    vote_type: Literal["like", "dislike"]


class TopPostOut(PostOut):
    likes_count: int
    dislikes_count: int


class TopPostsResponse(BaseModel):
    vote_type: Literal["like", "dislike"]
    limit: int
    posts: list[TopPostOut]

