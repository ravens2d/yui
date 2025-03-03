from datetime import datetime, UTC
from typing import List, AsyncGenerator
from contextlib import asynccontextmanager

from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

from app.model import Contact, Conversation, Message, Fact


class Repository:
    def __init__(self, db_url: str = "sqlite+aiosqlite:///yui.db"):
        self.engine = create_async_engine(db_url)
        self.async_session_maker = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
     
    async def initialize_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    async def __aenter__(self):
        await self.initialize_db()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.engine.dispose()

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        session = self.async_session_maker()
        try:
            yield session
        except:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def get_contact(self, name: str) -> Contact:
        async with self.session() as session:
            result = await session.exec(select(Contact).where(Contact.name == name))
            return result.first()
    
    async def create_contact(self, name: str) -> Contact:
        async with self.session() as session:
            contact = Contact(name=name)
            session.add(contact)
            await session.commit()
            return contact

    async def get_conversation(self, contact_id: str) -> Conversation:
        async with self.session() as session:
            result = await session.exec(select(Conversation).where(Conversation.contact_id == contact_id).order_by(Conversation.start_time.desc()))
            return result.first()
        
    async def get_conversations(self, contact_id: str) -> List[Conversation]:
        async with self.session() as session:
            result = await session.exec(select(Conversation).where(Conversation.contact_id == contact_id).order_by(Conversation.start_time.desc()))
            return result.all()

    async def create_conversation(self, contact_id: str) -> Conversation:
        async with self.session() as session:
            conversation = Conversation(contact_id=contact_id)
            session.add(conversation)
            await session.commit()
            return conversation
    
    async def update_conversation(self, conversation: Conversation) -> Conversation:
        async with self.session() as session:
            await session.merge(conversation)
            await session.commit()
            return conversation

    async def get_messages(self, contact_id: str) -> List[Message]:
        async with self.session() as session:
            result = await session.exec(select(Message).where(Message.contact_id == contact_id).order_by(Message.timestamp.desc()))
            return result.all()
    
    async def create_message(self, message: Message) -> Message:
        async with self.session() as session:
            session.add(message)
            await session.commit()
            return message
    
    async def create_messages(self, messages: List[Message]) -> List[Message]:
        async with self.session() as session:
            session.add_all(messages)
            await session.commit()
            return messages

    async def get_facts(self, contact_id: str) -> List[Fact]:
        async with self.session() as session:
            result = await session.exec(select(Fact).where(Fact.contact_id == contact_id))
            return result.all()
    
    async def create_fact(self, fact: Fact) -> Fact:
        async with self.session() as session:
            session.add(fact)
            await session.commit()
            return fact
    
    async def get_messages_for_conversation(self, conversation_id: str) -> List[Message]:
        async with self.session() as session:
            result = await session.exec(select(Message).where(Message.conversation_id == conversation_id).order_by(Message.timestamp.desc()))
            return result.all()
    
    async def get_conversation_for_message(self, message_id: str) -> Conversation:
        async with self.session() as session:
            result = await session.exec(select(Conversation).where(Conversation.id == Message.conversation_id))
            return result.first()
