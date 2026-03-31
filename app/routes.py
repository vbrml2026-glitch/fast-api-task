from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi import status as http_status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import and_, desc, func, literal, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import DISLIKE, LIKE, Post, PostVote, User
from app.schemas import (
    LoginRequest,
    PostAggregatesOut,
    PostByUserResponse,
    PostOut,
    RegisterRequest,
    TopPostOut,
    TopPostsResponse,
    TokenResponse,
    UserOut,
    VoteRequest,
)
from app.security import create_access_token, decode_access_token, hash_password, verify_password

router = APIRouter()

bearer_required = HTTPBearer(auto_error=True)
bearer_optional = HTTPBearer(auto_error=False)

def get_current_user_optional(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_optional),
    db: Session = Depends(get_db),
) -> User | None:
    if not creds or not creds.credentials:
        return None

    try:
        user_id_str = decode_access_token(creds.credentials)
        user_id = int(user_id_str)
    except Exception:
        # For "optional auth" endpoints we treat invalid tokens as anonymous.
        return None

    return db.get(User, user_id)


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer_required),
    db: Session = Depends(get_db),
) -> User:
    try:
        user_id_str = decode_access_token(creds.credentials)
        user_id = int(user_id_str)
    except Exception:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user


@router.post("/auth/register", status_code=http_status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    existing = db.execute(
        select(User).where(or_(User.username == req.username, User.email == req.email))
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Username or email already exists",
        )

    user = User(
        username=req.username,
        email=req.email,
        first_name=req.first_name,
        last_name=req.last_name,
        password_hash=hash_password(req.password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username}


@router.post("/auth/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.execute(
        select(User).where(or_(User.username == req.username_or_email, User.email == req.username_or_email))
    ).scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token)


@router.get("/users", response_model=list[UserOut])
def get_users(
    ids: str | None = Query(default=None, description="Comma-separated list of user ids"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="id", description="id|username|created_at|updated_at"),
    sort_order: str = Query(default="desc", description="asc|desc"),
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> list[UserOut]:
    allowed_sort = {"id": User.id, "username": User.username, "created_at": User.created_at, "updated_at": User.updated_at}
    sort_col = allowed_sort.get(sort_by)
    if not sort_col:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Invalid sort_by")

    order_fn = desc if sort_order.lower() == "desc" else (lambda x: x)
    if sort_order.lower() not in {"asc", "desc"}:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Invalid sort_order")

    q = select(User)
    if ids:
        try:
            id_list = [int(x.strip()) for x in ids.split(",") if x.strip()]
        except ValueError as e:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Invalid ids") from e
        q = q.where(User.id.in_(id_list))

    # Paging
    total = db.execute(select(func.count()).select_from(q.subquery())).scalar_one()

    q = q.order_by(order_fn(sort_col)).offset((page - 1) * page_size).limit(page_size)
    users = db.execute(q).scalars().all()

    out: list[UserOut] = []
    for u in users:
        out.append(
            UserOut(
                id=u.id,
                username=u.username,
                email=u.email if current_user else None,
                first_name=u.first_name if current_user else None,
                last_name=u.last_name if current_user else None,
                created_at=u.created_at if current_user else None,
                updated_at=u.updated_at if current_user else None,
                is_active=u.is_active if current_user else None,
            )
        )
    return out


@router.post("/posts", response_model=PostOut, status_code=http_status.HTTP_201_CREATED)
def upsert_post(
    post_key: str = Form(..., min_length=1, max_length=100),
    title: str = Form(..., min_length=1, max_length=200),
    content: str = Form(...),
    image: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PostOut:
    image_bytes: bytes | None = None
    if image is not None:
        image_bytes = image.file.read()

    post = db.execute(
        select(Post).where(and_(Post.user_id == current_user.id, Post.post_key == post_key))
    ).scalar_one_or_none()

    created = False
    if post is None:
        post = Post(user_id=current_user.id, post_key=post_key, title=title, content=content, image=image_bytes)
        db.add(post)
        created = True
    else:
        post.title = title
        post.content = content
        post.image = image_bytes

    db.commit()
    db.refresh(post)

    # If it already existed, a real REST API might use 200/204.
    # Keeping 201 is acceptable for this learning task.
    return PostOut.model_validate(post, from_attributes=True)


@router.get("/posts/by-user", response_model=PostByUserResponse)
def get_posts_by_user(
    user_id: int = Query(..., ge=1),
    title: str | None = Query(default=None, description="Substring match"),
    content: str | None = Query(default=None, description="Substring match"),
    likes: int | None = Query(default=None, ge=0, description="Filter by exact like count"),
    dislikes: int | None = Query(default=None, ge=0, description="Filter by exact dislike count"),
    created_at: datetime | None = Query(default=None, description="Return posts created at/after this time"),
    updated_at: datetime | None = Query(default=None, description="Return posts updated at/after this time"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    sort_by: str = Query(default="created_at", description="title|created_at|updated_at|likes|dislikes"),
    sort_order: str = Query(default="desc", description="asc|desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PostByUserResponse:
    likes_subq = (
        select(func.count(PostVote.id))
        .where(and_(PostVote.post_id == Post.id, PostVote.vote_type == LIKE))
        .scalar_subquery()
    )
    dislikes_subq = (
        select(func.count(PostVote.id))
        .where(and_(PostVote.post_id == Post.id, PostVote.vote_type == DISLIKE))
        .scalar_subquery()
    )

    base = (
        select(Post, likes_subq.label("likes_count"), dislikes_subq.label("dislikes_count"))
        .where(Post.user_id == user_id)
    )

    if title:
        base = base.where(Post.title.ilike(f"%{title}%"))
    if content:
        base = base.where(Post.content.ilike(f"%{content}%"))
    if likes is not None:
        base = base.where(likes_subq == likes)
    if dislikes is not None:
        base = base.where(dislikes_subq == dislikes)
    if created_at is not None:
        base = base.where(Post.created_at >= created_at)
    if updated_at is not None:
        base = base.where(Post.updated_at >= updated_at)

    total = db.execute(select(func.count()).select_from(base.subquery())).scalar_one()

    allowed_sort = {
        "title": Post.title,
        "created_at": Post.created_at,
        "updated_at": Post.updated_at,
        "likes": likes_subq,
        "dislikes": dislikes_subq,
    }
    sort_expr = allowed_sort.get(sort_by)
    if sort_expr is None:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Invalid sort_by")

    sort_order_norm = sort_order.lower()
    if sort_order_norm not in {"asc", "desc"}:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Invalid sort_order")
    order_clause = desc(sort_expr) if sort_order_norm == "desc" else sort_expr.asc()

    page_stmt = base.order_by(order_clause).offset((page - 1) * page_size).limit(page_size)
    rows = db.execute(page_stmt).all()
    posts = [r[0] for r in rows]

    post_ids = [p.id for p in posts]
    like_recent: dict[int, list[dict[str, Any]]] = {pid: [] for pid in post_ids}
    dislike_recent: dict[int, list[dict[str, Any]]] = {pid: [] for pid in post_ids}

    if post_ids:
        # Use window function to return top 5 by most recent vote per post.
        like_ranked = (
            select(
                PostVote.post_id.label("post_id"),
                User.id.label("user_id"),
                User.username.label("username"),
                func.row_number()
                .over(partition_by=PostVote.post_id, order_by=PostVote.voted_at.desc())
                .label("rn"),
            )
            .join(User, User.id == PostVote.user_id)
            .where(and_(PostVote.post_id.in_(post_ids), PostVote.vote_type == LIKE))
        ).subquery()
        like_stmt = (
            select(like_ranked.c.post_id, like_ranked.c.user_id, like_ranked.c.username)
            .where(like_ranked.c.rn <= 5)
            .order_by(like_ranked.c.post_id, like_ranked.c.rn)
        )
        like_rows = db.execute(like_stmt).all()
        for post_id, user_id, username in like_rows:
            like_recent[post_id].append({"id": user_id, "username": username})

        dislike_ranked = (
            select(
                PostVote.post_id.label("post_id"),
                User.id.label("user_id"),
                User.username.label("username"),
                func.row_number()
                .over(partition_by=PostVote.post_id, order_by=PostVote.voted_at.desc())
                .label("rn"),
            )
            .join(User, User.id == PostVote.user_id)
            .where(and_(PostVote.post_id.in_(post_ids), PostVote.vote_type == DISLIKE))
        ).subquery()
        dislike_stmt = (
            select(
                dislike_ranked.c.post_id,
                dislike_ranked.c.user_id,
                dislike_ranked.c.username,
            )
            .where(dislike_ranked.c.rn <= 5)
            .order_by(dislike_ranked.c.post_id, dislike_ranked.c.rn)
        )
        dislike_rows = db.execute(dislike_stmt).all()
        for post_id, user_id, username in dislike_rows:
            dislike_recent[post_id].append({"id": user_id, "username": username})

    posts_out: list[PostAggregatesOut] = []
    for post, likes_count, dislikes_count in rows:
        posts_out.append(
            PostAggregatesOut(
                id=post.id,
                user_id=post.user_id,
                post_key=post.post_key,
                title=post.title,
                content=post.content,
                created_at=post.created_at,
                updated_at=post.updated_at,
                likes_count=int(likes_count or 0),
                dislikes_count=int(dislikes_count or 0),
                recently_liked_users=[{"id": u["id"], "username": u["username"]} for u in like_recent.get(post.id, [])],
                recently_disliked_users=[
                    {"id": u["id"], "username": u["username"]} for u in dislike_recent.get(post.id, [])
                ],
            )
        )

    return PostByUserResponse(page=page, page_size=page_size, total=total, posts=posts_out)

@router.post("/posts/{post_id}/vote")
def vote_on_post(
    post_id: int,
    req: VoteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Post not found")

    vote_value = LIKE if req.vote_type == "like" else DISLIKE

    existing = db.execute(
        select(PostVote).where(and_(PostVote.post_id == post_id, PostVote.user_id == current_user.id))
    ).scalar_one_or_none()

    if existing is None:
        pv = PostVote(user_id=current_user.id, post_id=post_id, vote_type=vote_value, voted_at=datetime.utcnow())
        db.add(pv)
    else:
        existing.vote_type = vote_value
        existing.voted_at = datetime.utcnow()

    db.commit()

    likes_count = db.execute(
        select(func.count(PostVote.id)).where(and_(PostVote.post_id == post_id, PostVote.vote_type == LIKE))
    ).scalar_one()
    dislikes_count = db.execute(
        select(func.count(PostVote.id)).where(and_(PostVote.post_id == post_id, PostVote.vote_type == DISLIKE))
    ).scalar_one()

    return {"post_id": post_id, "likes_count": likes_count, "dislikes_count": dislikes_count}


# New with "post_id" and "user_id" in the response
# @router.post("/posts/{post_id}/vote")
# def vote_on_post(
#     post_id: int,
#     req: VoteRequest,
#     user_id: int = Query(..., ge=1, description="ID of the user whose post you want to vote on"),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ) -> dict[str, Any]:
#     # Verify the post exists AND belongs to the specified user
#     post = db.execute(
#         select(Post).where(and_(Post.id == post_id, Post.user_id == user_id))
#     ).scalar_one_or_none()
#     if not post:
#         raise HTTPException(
#             status_code=http_status.HTTP_404_NOT_FOUND,
#             detail=f"Post {post_id} not found for user {user_id}",
#         )

#     vote_value = LIKE if req.vote_type == "like" else DISLIKE

#     existing = db.execute(
#         select(PostVote).where(and_(PostVote.post_id == post_id, PostVote.user_id == current_user.id))
#     ).scalar_one_or_none()

#     if existing is None:
#         pv = PostVote(user_id=current_user.id, post_id=post_id, vote_type=vote_value, voted_at=datetime.utcnow())
#         db.add(pv)
#     else:
#         existing.vote_type = vote_value
#         existing.voted_at = datetime.utcnow()

#     db.commit()

#     likes_count = db.execute(
#         select(func.count(PostVote.id)).where(and_(PostVote.post_id == post_id, PostVote.vote_type == LIKE))
#     ).scalar_one()
#     dislikes_count = db.execute(
#         select(func.count(PostVote.id)).where(and_(PostVote.post_id == post_id, PostVote.vote_type == DISLIKE))
#     ).scalar_one()

#     return {"post_id": post_id, "user_id": user_id, "likes_count": likes_count, "dislikes_count": dislikes_count}


@router.get("/posts/top", response_model=TopPostsResponse)
def get_top_posts(
    vote_type: str = Query(..., description="like|dislike"),
    limit: int = Query(default=10, ge=1, le=50),
    user_id: int | None = Query(default=None, description="Optional: author user id to restrict ranking"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TopPostsResponse:
    vote_type_norm = vote_type.lower()
    if vote_type_norm not in {"like", "dislike"}:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="vote_type must be like|dislike")

    vote_value = LIKE if vote_type_norm == "like" else DISLIKE

    count_expr = func.count(PostVote.id)
    base = (
        select(Post, count_expr.label("score"))
        .join(PostVote, PostVote.post_id == Post.id)
        .where(PostVote.vote_type == vote_value)
    )
    if user_id is not None:
        base = base.where(Post.user_id == user_id)

    # Group by post columns to make Postgres happy.
    base = base.group_by(Post.id, Post.user_id, Post.post_key, Post.title, Post.content, Post.created_at, Post.updated_at)
    base = base.order_by(desc(count_expr), desc(Post.created_at)).limit(limit)

    rows = db.execute(base).all()

    posts_out: list[TopPostOut] = []
    for post, score in rows:
        # Score refers to like_count OR dislike_count depending on vote_type.
        likes_count = score if vote_value == LIKE else 0
        dislikes_count = score if vote_value == DISLIKE else 0
        posts_out.append(
            TopPostOut(
                id=post.id,
                user_id=post.user_id,
                post_key=post.post_key,
                title=post.title,
                content=post.content,
                created_at=post.created_at,
                updated_at=post.updated_at,
                likes_count=likes_count,
                dislikes_count=dislikes_count,
            )
        )

    return TopPostsResponse(vote_type=vote_type_norm, limit=limit, posts=posts_out)

