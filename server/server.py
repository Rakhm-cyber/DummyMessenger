import sqlalchemy
import psycopg2

from datetime import datetime
from typing import Annotated
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import create_engine, text, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from fastapi import FastAPI, Body
from pydantic import BaseModel


engine = create_async_engine("postgresql+asyncpg://postgres:1@localhost:5432/postgres", echo=True)


class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    message_count: Mapped[str] = mapped_column(Integer, nullable=False, default=0)

class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    message: Mapped[str] = mapped_column(String, nullable=False)
    message_date: Mapped[DateTime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    user: Mapped[User] = relationship("User", back_populates="messages")

class Messagetype(BaseModel):
    name: str
    message: str

@asynccontextmanager
async def lifespan(app: FastAPI):

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

app = FastAPI(lifespan=lifespan)


@app.post("/")
async def ret(user_message: Messagetype):
    async with engine.begin() as conn:
        user_result =await conn.execute(
            text("""
            INSERT INTO users (name, message_count)
            VALUES (:name, 1)
            ON CONFLICT (name) DO UPDATE
              SET message_count = users.message_count + 1
            RETURNING id, message_count;
        """),
            {"name": user_message.name}
        )

        user_row = user_result.fetchone()
        user_id = user_row.id
        new_msg_count = user_row.message_count

        message_result = await conn.execute(
            text("""
                INSERT INTO messages (user_id, message, sequence_number)
                VALUES (:user_id, :message, :sequence_number)
                RETURNING id
            """),
            {
                "user_id": user_id,
                "message": user_message.message,
                "sequence_number": new_msg_count
            }
        )
        message_info = message_result.fetchone()
        current_message_id = message_info.id
        history_result =await conn.execute(
            text("""
                SELECT m.id,
                       u.name,
                       m.message,
                       m.message_date,
                       m.sequence_number,
                       u.message_count
                FROM messages m
                JOIN users u ON m.user_id = u.id
                WHERE u.id = :user_id and m.id <= :current_message_id
                ORDER BY m.id DESC
                LIMIT 10
            """),
            {"user_id": user_id, "current_message_id": current_message_id}
        )
        rows = history_result.fetchall()
        response_messages = []
        for row in rows:
            response_messages.append({
                "id": row.id,
                "name": row.name,
                "message": row.message,
                "message_date": row.message_date.isoformat(),
                "sequence_number": row.sequence_number,
                "user_message_count": row.message_count
            })

        return {"messages": response_messages}





