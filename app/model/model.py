from datetime import datetime, UTC
from typing import Optional, List
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship, JSON
import uuid


class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class MessageType(str, Enum):
    CHAT = "chat"
    TOOL_USE = "tool_use"


class Message(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    role: Role
    content: str = ""

    message_type: MessageType = MessageType.CHAT
    tool_use_id: Optional[str] = None
    tool_use_name: Optional[str] = None
    tool_use_input: Optional[dict] = Field(default=None, sa_type=JSON)

    conversation_id: str = Field(foreign_key="conversation.id")
    conversation: "Conversation" = Relationship(back_populates="messages")

    contact_id: str = Field(foreign_key="contact.id")
    contact: "Contact" = Relationship(back_populates="messages")


class Conversation(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    start_time: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    end_time: Optional[datetime] = None
    summary: Optional[str] = None

    messages: List["Message"] = Relationship(back_populates="conversation", sa_relationship_kwargs={"order_by": "Message.timestamp"})
    
    contact_id: str = Field(foreign_key="contact.id")
    contact: "Contact" = Relationship(back_populates="conversations")


class Fact(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    content: str

    contact_id: str = Field(foreign_key="contact.id")
    contact: "Contact" = Relationship(back_populates="facts")


class Contact(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str

    messages: List["Message"] = Relationship(back_populates="contact", sa_relationship_kwargs={"order_by": "Message.timestamp.desc()"})
    conversations: List["Conversation"] = Relationship(back_populates="contact", sa_relationship_kwargs={"order_by": "Conversation.start_time.desc()"})
    facts: List["Fact"] = Relationship(back_populates="contact")

    @property
    def current_conversation(self) -> Optional[Conversation]:
        return self.conversations[0] if self.conversations else None