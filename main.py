from datetime import datetime
from typing import Literal
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, field_validator
from sqlalchemy import or_
from sqlmodel import Field, Session, SQLModel, create_engine, select

PostStatus = Literal["draft", "published"]
SortOrder = Literal["asc", "desc"]

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    login: str = Field(index=True, unique=True)
    password: str
    role: str = Field(default="reader", index=True)

class UserBase(BaseModel):
    login: str
    password: str

    @field_validator("login")
    @classmethod
    def validate_login(cls, login: str):
        if not login.strip():
            raise ValueError("Пустой логин")
        return login.strip()

    @field_validator("password")
    @classmethod
    def validate_password(cls, password: str):
        if not password.strip():
            raise ValueError("Пустой пароль")
        return password

class UserId(BaseModel):
    id: int
    login: str
    role: str

class Category(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)

class CategoryBase(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, name: str):
        if not name.strip():
            raise ValueError("Пустое название")
        return name.strip().lower()

class CategoryId(CategoryBase):
    id: int

class CategoryUpdate(BaseModel):
    name: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, name: str | None):
        if name is not None and not name.strip():
            raise ValueError("Пустое название")
        if name is None:
            return name
        return name.strip().lower()

class Post(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    author_id: int = Field(foreign_key="user.id", index=True)
    category_id: int = Field(foreign_key="category.id", index=True)
    title: str = Field(index=True)
    content: str
    publication_date: datetime = Field(default_factory=datetime.utcnow, index=True)
    status: str = Field(default="draft", index=True)

class PostBase(BaseModel):
    title: str
    content: str
    category_id: int
    status: PostStatus = "draft"

    @field_validator("title")
    @classmethod
    def validate_title(cls, title: str):
        if not title.strip():
            raise ValueError("Пустой заголовок")
        return title.strip()

    @field_validator("content")
    @classmethod
    def validate_content(cls, content: str):
        if not content.strip():
            raise ValueError("Пустой текст")
        return content.strip()

    @field_validator("category_id")
    @classmethod
    def validate_category_id(cls, category_id: int):
        if category_id <= 0:
            raise ValueError("Неверная категория")
        return category_id

class PostId(PostBase):
    id: int
    author_id: int
    publication_date: datetime
    likes_count: int

class PostUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    category_id: int | None = None
    status: PostStatus | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, title: str | None):
        if title is not None and not title.strip():
            raise ValueError("Пустой заголовок")
        if title is None:
            return title
        return title.strip()

    @field_validator("content")
    @classmethod
    def validate_content(cls, content: str | None):
        if content is not None and not content.strip():
            raise ValueError("Пустой текст")
        if content is None:
            return content
        return content.strip()

    @field_validator("category_id")
    @classmethod
    def validate_category_id(cls, category_id: int | None):
        if category_id is not None and category_id <= 0:
            raise ValueError("Неверная категория")
        return category_id

class Comment(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    post_id: int = Field(foreign_key="post.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    text: str
    date: datetime = Field(default_factory=datetime.utcnow, index=True)

class CommentBase(BaseModel):
    post_id: int
    text: str

    @field_validator("post_id")
    @classmethod
    def validate_post_id(cls, post_id: int):
        if post_id <= 0:
            raise ValueError("Неверная статья")
        return post_id

    @field_validator("text")
    @classmethod
    def validate_text(cls, text: str):
        if not text.strip():
            raise ValueError("Пустой комментарий")
        return text.strip()

class CommentId(CommentBase):
    id: int
    user_id: int
    date: datetime

class CommentUpdate(BaseModel):
    text: str | None = None

    @field_validator("text")
    @classmethod
    def validate_text(cls, text: str | None):
        if text is not None and not text.strip():
            raise ValueError("Пустой комментарий")
        if text is None:
            return text
        return text.strip()

class PostLike(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    post_id: int = Field(foreign_key="post.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    date: datetime = Field(default_factory=datetime.utcnow)

engine = create_engine("sqlite:///database.db")

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def seed_data():
    with Session(engine) as session:
        if session.exec(select(User)).first():
            return
        reader = User(login="reader", password="123", role="reader")
        author = User(login="author", password="123", role="author")
        moderator = User(login="moderator", password="123", role="moderator")
        tech = Category(name="tech")
        life = Category(name="life")
        session.add(reader)
        session.add(author)
        session.add(moderator)
        session.add(tech)
        session.add(life)
        session.commit()
        session.refresh(reader)
        session.refresh(author)
        session.refresh(tech)
        session.refresh(life)
        post_1 = Post(author_id=author.id, category_id=tech.id, title="первая статья", content="опубликованная статья.", status="published")
        post_2 = Post(author_id=author.id, category_id=life.id, title="черновик", content="черновик.", status="draft")
        session.add(post_1)
        session.add(post_2)
        session.commit()
        session.refresh(post_1)
        comment = Comment(post_id=post_1.id, user_id=reader.id, text="хорошая статья")
        like = PostLike(post_id=post_1.id, user_id=reader.id)
        session.add(comment)
        session.add(like)
        session.commit()

app = FastAPI()
security = HTTPBasic()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(status_code=400, content=jsonable_encoder({"detail": exc.errors()}))

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    seed_data()

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.login == credentials.username)).first()
        if not user or user.password != credentials.password:
            raise HTTPException(status_code=401, detail="Ошибка входа", headers={"WWW-Authenticate": "Basic"})
        return user

def check_role(user: User, allowed_roles: list[str]):
    if user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Нет прав")

def get_likes_count(session: Session, post_id: int):
    return len(session.exec(select(PostLike).where(PostLike.post_id == post_id)).all())

def post_to_response(session: Session, post: Post):
    return PostId(id=post.id, author_id=post.author_id, category_id=post.category_id, title=post.title, content=post.content, publication_date=post.publication_date, status=post.status, likes_count=get_likes_count(session, post.id))

def can_read_post(user: User, post: Post):
    if post.status == "published":
        return True
    if user.role == "moderator":
        return True
    if user.role == "author" and post.author_id == user.id:
        return True
    return False

@app.post("/register/")
def register_user(user: UserBase):
    with Session(engine) as session:
        existing_user = session.exec(select(User).where(User.login == user.login)).first()
        if existing_user:
            raise HTTPException(status_code=409, detail="Логин занят")
        db_user = User(login=user.login, password=user.password, role="reader")
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return UserId(id=db_user.id, login=db_user.login, role=db_user.role)

@app.get("/login/")
def login(current_user: User = Depends(get_current_user)):
    return UserId(id=current_user.id, login=current_user.login, role=current_user.role)

@app.post("/api/categories")
def create_category(category: CategoryBase, current_user: User = Depends(get_current_user)):
    check_role(current_user, ["moderator"])
    with Session(engine) as session:
        existing_category = session.exec(select(Category).where(Category.name == category.name)).first()
        if existing_category:
            raise HTTPException(status_code=409, detail="Уже есть")
        db_category = Category(name=category.name)
        session.add(db_category)
        session.commit()
        session.refresh(db_category)
        return CategoryId(id=db_category.id, name=db_category.name)

@app.get("/api/categories")
def read_categories(current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        return session.exec(select(Category)).all()

@app.get("/api/categories/{category_id}")
def read_category(category_id: int, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        category = session.get(Category, category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Не найдено")
        return category

@app.put("/api/categories/{category_id}")
def update_category(category_id: int, category_update: CategoryUpdate, current_user: User = Depends(get_current_user)):
    check_role(current_user, ["moderator"])
    with Session(engine) as session:
        category = session.get(Category, category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Не найдено")
        update_data = category_update.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="Нет данных")
        if "name" in update_data:
            existing_category = session.exec(select(Category).where(Category.name == update_data["name"])).first()
            if existing_category and existing_category.id != category.id:
                raise HTTPException(status_code=409, detail="Уже есть")
        for field_name, field_value in update_data.items():
            setattr(category, field_name, field_value)
        session.add(category)
        session.commit()
        session.refresh(category)
        return category

@app.delete("/api/categories/{category_id}")
def delete_category(category_id: int, current_user: User = Depends(get_current_user)):
    check_role(current_user, ["moderator"])
    with Session(engine) as session:
        category = session.get(Category, category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Не найдено")
        post_with_category = session.exec(select(Post).where(Post.category_id == category_id)).first()
        if post_with_category:
            raise HTTPException(status_code=409, detail="Есть статьи")
        session.delete(category)
        session.commit()
        return {"detail": "Удалено"}

@app.post("/api/posts")
def create_post(post: PostBase, current_user: User = Depends(get_current_user)):
    check_role(current_user, ["author", "moderator"])
    with Session(engine) as session:
        category = session.get(Category, post.category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Не найдено")
        db_post = Post(author_id=current_user.id, category_id=post.category_id, title=post.title, content=post.content, status=post.status)
        session.add(db_post)
        session.commit()
        session.refresh(db_post)
        return post_to_response(session, db_post)

@app.get("/api/posts")
def read_posts(page: int = Query(default=1, ge=1), limit: int = Query(default=10, ge=1, le=100), category: str | None = Query(default=None), status: PostStatus | None = Query(default=None), sort_popularity: SortOrder | None = Query(default=None), sort_date: SortOrder | None = Query(default=None), current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        statement = select(Post)
        if category is not None:
            db_category = session.exec(select(Category).where(Category.name == category.strip().lower())).first()
            if not db_category:
                return {"page": page, "limit": limit, "total": 0, "items": []}
            statement = statement.where(Post.category_id == db_category.id)
        if status is not None:
            statement = statement.where(Post.status == status)
        if current_user.role == "reader":
            statement = statement.where(Post.status == "published")
        if current_user.role == "author":
            statement = statement.where(or_(Post.status == "published", Post.author_id == current_user.id))
        if sort_date == "asc":
            statement = statement.order_by(Post.publication_date)
        if sort_date == "desc":
            statement = statement.order_by(Post.publication_date.desc())
        posts = session.exec(statement).all()
        post_responses = [post_to_response(session, post) for post in posts]
        if sort_popularity == "asc":
            post_responses.sort(key=lambda post: post.likes_count)
        if sort_popularity == "desc":
            post_responses.sort(key=lambda post: post.likes_count, reverse=True)
        total = len(post_responses)
        start = (page - 1) * limit
        end = start + limit
        return {"page": page, "limit": limit, "total": total, "items": post_responses[start:end]}

@app.get("/api/posts/{post_id}")
def read_post(post_id: int, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        post = session.get(Post, post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Не найдено")
        if not can_read_post(current_user, post):
            raise HTTPException(status_code=403, detail="Нет доступа")
        return post_to_response(session, post)

@app.put("/api/posts/{post_id}")
def update_post(post_id: int, post_update: PostUpdate, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        post = session.get(Post, post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Не найдено")
        if current_user.role != "moderator" and post.author_id != current_user.id:
            raise HTTPException(status_code=403, detail="Нет прав")
        update_data = post_update.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="Нет данных")
        if "category_id" in update_data:
            category = session.get(Category, update_data["category_id"])
            if not category:
                raise HTTPException(status_code=404, detail="Не найдено")
        for field_name, field_value in update_data.items():
            setattr(post, field_name, field_value)
        if update_data.get("status") == "published":
            post.publication_date = datetime.utcnow()
        session.add(post)
        session.commit()
        session.refresh(post)
        return post_to_response(session, post)

@app.delete("/api/posts/{post_id}")
def delete_post(post_id: int, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        post = session.get(Post, post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Не найдено")
        if current_user.role != "moderator" and post.author_id != current_user.id:
            raise HTTPException(status_code=403, detail="Нет прав")
        comments = session.exec(select(Comment).where(Comment.post_id == post_id)).all()
        likes = session.exec(select(PostLike).where(PostLike.post_id == post_id)).all()
        for comment in comments:
            session.delete(comment)
        for like in likes:
            session.delete(like)
        session.delete(post)
        session.commit()
        return {"detail": "Удалено"}

@app.post("/api/comments")
def create_comment(comment: CommentBase, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        post = session.get(Post, comment.post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Не найдено")
        if not can_read_post(current_user, post):
            raise HTTPException(status_code=403, detail="Нет доступа")
        db_comment = Comment(post_id=comment.post_id, user_id=current_user.id, text=comment.text)
        session.add(db_comment)
        session.commit()
        session.refresh(db_comment)
        return CommentId(id=db_comment.id, post_id=db_comment.post_id, user_id=db_comment.user_id, text=db_comment.text, date=db_comment.date)

@app.get("/api/comments")
def read_comments(post_id: int | None = Query(default=None), page: int = Query(default=1, ge=1), limit: int = Query(default=10, ge=1, le=100), current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        statement = select(Comment)
        if post_id is not None:
            post = session.get(Post, post_id)
            if not post:
                raise HTTPException(status_code=404, detail="Не найдено")
            if not can_read_post(current_user, post):
                raise HTTPException(status_code=403, detail="Нет доступа")
            statement = statement.where(Comment.post_id == post_id)
        comments = session.exec(statement.order_by(Comment.date.desc())).all()
        comment_responses = []
        for comment in comments:
            post = session.get(Post, comment.post_id)
            if post and can_read_post(current_user, post):
                comment_responses.append(CommentId(id=comment.id, post_id=comment.post_id, user_id=comment.user_id, text=comment.text, date=comment.date))
        total = len(comment_responses)
        start = (page - 1) * limit
        end = start + limit
        return {"page": page, "limit": limit, "total": total, "items": comment_responses[start:end]}

@app.get("/api/comments/{comment_id}")
def read_comment(comment_id: int, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        comment = session.get(Comment, comment_id)
        if not comment:
            raise HTTPException(status_code=404, detail="Не найдено")
        post = session.get(Post, comment.post_id)
        if not post or not can_read_post(current_user, post):
            raise HTTPException(status_code=403, detail="Нет доступа")
        return comment

@app.put("/api/comments/{comment_id}")
def update_comment(comment_id: int, comment_update: CommentUpdate, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        comment = session.get(Comment, comment_id)
        if not comment:
            raise HTTPException(status_code=404, detail="Не найдено")
        if current_user.role != "moderator" and comment.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Нет прав")
        update_data = comment_update.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="Нет данных")
        for field_name, field_value in update_data.items():
            setattr(comment, field_name, field_value)
        session.add(comment)
        session.commit()
        session.refresh(comment)
        return comment

@app.delete("/api/comments/{comment_id}")
def delete_comment(comment_id: int, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        comment = session.get(Comment, comment_id)
        if not comment:
            raise HTTPException(status_code=404, detail="Не найдено")
        if current_user.role != "moderator" and comment.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Нет прав")
        session.delete(comment)
        session.commit()
        return {"detail": "Удалено"}

@app.post("/api/posts/{post_id}/likes")
def like_post(post_id: int, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        post = session.get(Post, post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Не найдено")
        if not can_read_post(current_user, post):
            raise HTTPException(status_code=403, detail="Нет доступа")
        existing_like = session.exec(select(PostLike).where(PostLike.post_id == post_id, PostLike.user_id == current_user.id)).first()
        if existing_like:
            raise HTTPException(status_code=409, detail="Уже есть")
        like = PostLike(post_id=post_id, user_id=current_user.id)
        session.add(like)
        session.commit()
        session.refresh(like)
        return {"detail": "Добавлено", "post_id": post_id, "likes_count": get_likes_count(session, post_id)}

@app.delete("/api/posts/{post_id}/likes")
def unlike_post(post_id: int, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        like = session.exec(select(PostLike).where(PostLike.post_id == post_id, PostLike.user_id == current_user.id)).first()
        if not like:
            raise HTTPException(status_code=404, detail="Не найдено")
        session.delete(like)
        session.commit()
        return {"detail": "Удалено", "post_id": post_id, "likes_count": get_likes_count(session, post_id)}

@app.get("/api/posts/{post_id}/likes")
def read_post_likes(post_id: int, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        post = session.get(Post, post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Не найдено")
        if not can_read_post(current_user, post):
            raise HTTPException(status_code=403, detail="Нет доступа")
        return {"post_id": post_id, "likes_count": get_likes_count(session, post_id)}