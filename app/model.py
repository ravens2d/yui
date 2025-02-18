from datetime import datetime, UTC
from typing import Optional, List, Tuple
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship, select, Session
import uuid


class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class Conversation(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    start_time: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    end_time: Optional[datetime] = None
    summary: Optional[str] = None

    messages: List["Message"] = Relationship(back_populates="conversation")
    
    contact_id: str = Field(foreign_key="contact.id")
    contact: "Contact" = Relationship(back_populates="conversations")


class Message(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    role: Role
    content: str

    conversation_id: str = Field(foreign_key="conversation.id")
    conversation: Conversation = Relationship(back_populates="messages")

    contact_id: str = Field(foreign_key="contact.id")
    contact: "Contact" = Relationship(back_populates="messages")


class Fact(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    content: str
    contact_id: str = Field(foreign_key="contact.id")
    contact: "Contact" = Relationship(back_populates="facts")


class Contact(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str

    messages: List["Message"] = Relationship(back_populates="contact")
    conversations: List["Conversation"] = Relationship(back_populates="contact")
    facts: List["Fact"] = Relationship(back_populates="contact")

    @classmethod
    def get_or_create_with_conversation(cls, session: Session, name: str) -> Tuple["Contact", Conversation]:
        contact = session.exec(select(Contact).where(Contact.name == name)).first()
        
        if contact is None:
            contact = Contact(name=name)
            session.add(contact)
            session.flush()
        
        latest_conversation = session.exec(
            select(Conversation)
            .where(Conversation.contact_id == contact.id)
            .order_by(Conversation.start_time.desc())
        ).first()
        
        if latest_conversation is None or latest_conversation.end_time is not None:
            latest_conversation = Conversation(contact=contact)
            session.add(latest_conversation)
        
        return contact, latest_conversation