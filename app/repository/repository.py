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

    async def save_message(self, message: Message) -> Message:
        async with self.session() as session:
            session.add(message)
            await session.commit()
            return message

    async def save_messages(self, messages: List[Message]) -> List[Message]:
        async with self.session() as session:
            session.add_all(messages)
            await session.commit()  
            return messages

    async def get_or_create_contact(self, name: str) -> Contact:
        async with self.session() as session:
            result = await session.exec(select(Contact).where(Contact.name == name))
            contact = result.first()
            
            if contact is None:
                contact = Contact(name=name)
                session.add(contact)
                await session.flush()
            
            await session.refresh(contact, ['conversations'])
 
            if not contact.conversations or contact.current_conversation.end_time is not None:
                new_conversation = Conversation(contact=contact)
                session.add(new_conversation)
                await session.commit()
        
        return contact 
    
    async def save_fact(self, fact: Fact) -> Fact:
        async with self.session() as session:
            session.add(fact)
            await session.commit()
            return fact

    async def create_conversation(self, contact: Contact) -> Conversation:
        async with self.session() as session:
            if contact.current_conversation:
                contact.current_conversation.end_time = datetime.now(tz=UTC)
                session.add(contact.current_conversation)
        
            conversation = Conversation(contact=contact)
            session.add(conversation)
            await session.commit()  
            return conversation

    async def save_conversation(self, conversation: Conversation) -> Conversation:
        async with self.session() as session:
            await session.merge(conversation)
            await session.commit()
            return conversation

    async def get_conversations_for_contact(self, contact: Contact) -> List[Conversation]:
        async with self.session() as session:
            await session.merge(contact)
            result = await session.exec(select(Conversation).where(Conversation.contact == contact).order_by(Conversation.start_time.desc()))
            return result.all()

    async def get_messages_for_contact(self, contact: Contact, limit: int = 50) -> List[Message]:
        async with self.session() as session:
            await session.merge(contact)
            result = await session.exec(select(Message).where(Message.contact == contact).order_by(Message.timestamp.desc()).limit(limit))
            return result.all()
    
    async def get_facts_for_contact(self, contact: Contact) -> List[Fact]:
        async with self.session() as session:
            await session.merge(contact)
            result = await session.exec(select(Fact).where(Fact.contact == contact))
            return result.all() 
    
    async def get_messages_for_conversation(self, conversation: Conversation) -> List[Message]:
        async with self.session() as session:
            await session.merge(conversation)
            result = await session.exec(select(Message).where(Message.conversation == conversation).order_by(Message.timestamp.desc()))
            return result.all()
 
    async def get_conversation_for_message(self, message: Message) -> Conversation:
        async with self.session() as session:
            await session.merge(message)
            result = await session.exec(select(Conversation).where(Conversation.messages.contains(message)))
            return result.first()
