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
    contact_id: str = Field(foreign_key="contact.id")


class Conversation(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    start_time: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    end_time: Optional[datetime] = None
    summary: Optional[str] = None
    
    contact_id: str = Field(foreign_key="contact.id")


class Fact(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    content: str

    contact_id: str = Field(foreign_key="contact.id")


class Contact(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
