from datetime import datetime
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, field_validator
from sqlmodel import Field, Session, SQLModel, create_engine, select


TaskStatus = Literal["new", "in_progress", "completed"]
DeadlineSort = Literal["asc", "desc"]


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    login: str = Field(index=True, unique=True)
    password: str


class UserBase(BaseModel):
    login: str
    password: str

    @field_validator("login")
    @classmethod
    def validate_login(cls, login: str):
        if not login.strip():
            raise ValueError("Логин не может быть пустым")
        return login

    @field_validator("password")
    @classmethod
    def validate_password(cls, password: str):
        if not password.strip():
            raise ValueError("Пароль не может быть пустым")
        return password


class UserId(BaseModel):
    id: int
    login: str


class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    priority: int
    deadline: datetime
    description: str | None = None
    status: str = Field(default="new", index=True)

    user_id: int = Field(foreign_key="user.id", index=True)


class TaskBase(BaseModel):
    title: str
    priority: int
    deadline: datetime
    description: str | None = None
    status: TaskStatus = "new"

    @field_validator("title")
    @classmethod
    def validate_title(cls, title: str):
        if not title.strip():
            raise ValueError("Название задачи не может быть пустым")

        return title

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, priority: int):
        if priority < 1 or priority > 5:
            raise ValueError("Приоритет должен быть числом от 1 до 5")

        return priority


class TaskId(TaskBase):
    id: int


class TaskUpdate(BaseModel):
    id: int
    title: str | None = None
    priority: int | None = None
    deadline: datetime | None = None
    description: str | None = None
    status: TaskStatus | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, title: str | None):
        if title is not None and not title.strip():
            raise ValueError("Название задачи не может быть пустым")

        return title

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, priority: int | None):
        if priority is not None and (priority < 1 or priority > 5):
            raise ValueError("Приоритет должен быть числом от 1 до 5")

        return priority

engine = create_engine("sqlite:///database.db", echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

app = FastAPI()

security = HTTPBasic()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

def get_current_user(
    credentials: HTTPBasicCredentials = Depends(security),
):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.login == credentials.username)).first()

        if not user or user.password != credentials.password:
            raise HTTPException(
                status_code=401,
                detail="Неверный логин или пароль",
                headers={"WWW-Authenticate": "Basic"},
            )
        return user

@app.post("/register/")
def register_user(user: UserBase):
    with Session(engine) as session:
        existing_user = session.exec(
            select(User).where(User.login == user.login)
        ).first()

        if existing_user:
            raise HTTPException(status_code=409, detail="Пользователь с таким логином уже существует",)

        db_user = User(login=user.login, password=user.password)

        session.add(db_user)
        session.commit()
        session.refresh(db_user)

        return UserId(id=db_user.id, login=db_user.login)

@app.post("/tasks/")
def create_task(task: TaskBase, current_user: User = Depends(get_current_user),):
    with Session(engine) as session:
        db_task = Task(
            title=task.title,
            priority=task.priority,
            deadline=task.deadline,
            description=task.description,
            status=task.status,
            user_id=current_user.id
        )

        session.add(db_task)
        session.commit()
        session.refresh(db_task)

        return TaskId(
            id=db_task.id,
            title=db_task.title,
            priority=db_task.priority,
            deadline=db_task.deadline,
            description=db_task.description,
            status=db_task.status
        )

@app.get("/tasks/")
def read_tasks(task_status: TaskStatus | None = Query(default=None, alias="status"), sort_deadline: DeadlineSort | None = Query(default=None),current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        statement = select(Task).where(Task.user_id == current_user.id)

        if task_status is not None:
            statement = statement.where(Task.status == task_status)

        if sort_deadline == "asc":
            statement = statement.order_by(Task.deadline)

        if sort_deadline == "desc":
            statement = statement.order_by(Task.deadline.desc())

        tasks = session.exec(statement).all()
        return tasks

@app.get("/tasks/{task_id}")
def read_task(task_id: int, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        task = session.exec(
            select(Task).where(
                Task.id == task_id,
                Task.user_id == current_user.id,
            )).first()

        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена")

        return task


@app.put("/tasks/")
def update_task(task_update: TaskUpdate, current_user: User = Depends(get_current_user),):
    with Session(engine) as session:
        task = session.exec(
            select(Task).where(
                Task.id == task_update.id,
                Task.user_id == current_user.id,
            )).first()

        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена")

        update_data = task_update.model_dump(exclude_unset=True)
        update_data.pop("id")

        for field_name, field_value in update_data.items():
            setattr(task, field_name, field_value)

        session.add(task)
        session.commit()
        session.refresh(task)

        return task


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        task = session.exec(
            select(Task).where(
                Task.id == task_id,
                Task.user_id == current_user.id,
            )).first()

        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена")

        session.delete(task)
        session.commit()

        return {"detail": "Задача успешно удалена"}