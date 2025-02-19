import sqlalchemy
import psycopg2

from datetime import datetime
from typing import Annotated
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import create_engine, text
from fastapi import FastAPI, Body
from pydantic import BaseModel


engine = create_async_engine("postgresql+asyncpg://postgres:1@localhost:5432/postgres", echo=True)


class Message(BaseModel):
    name: str
    message: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.connect() as con:
        await con.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(80) UNIQUE NOT NULL,
                message_count INTEGER NOT NULL DEFAULT 0  
            )
        """))
        await con.execute(text("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                message TEXT NOT NULL,
                message_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                sequence_number INTEGER NOT NULL,
                UNIQUE (user_id, sequence_number)
            )
        """))
        await con.commit()

    yield

app = FastAPI(lifespan=lifespan)


@app.post("/")
async def ret(user_message: Message):
    async with engine.begin() as conn:
        user_result =await conn.execute(
            text("""
                WITH locked AS (    
                    SELECT id, message_count 
                    FROM users 
                    WHERE name = :name 
                    FOR UPDATE
                ),
                updated AS (
                    UPDATE users
                    SET message_count = locked.message_count + 1
                    FROM locked
                    WHERE users.id = locked.id
                    RETURNING users.id, users.message_count
                ),
                inserted AS (
                    INSERT INTO users (name, message_count)
                    SELECT :name, 1
                    WHERE NOT EXISTS (SELECT 1 FROM locked)
                    RETURNING id, message_count
                )
                SELECT id, message_count FROM updated
                UNION ALL
                SELECT id, message_count FROM inserted;
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
