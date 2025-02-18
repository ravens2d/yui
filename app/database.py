from datetime import datetime
from typing import Tuple
from sqlmodel import create_engine, SQLModel, Session, select

from app.model import Contact, Conversation, Message, Role

class Database:
    def __init__(self, db_url: str = "sqlite:///yui.db"):
        self.engine = create_engine(db_url)
        SQLModel.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        return Session(self.engine)

    def save_message(self, session: Session, role: Role, content: str, conversation: Conversation, contact: Contact) -> Message:
        message = Message(
            role=role,
            content=content,
            conversation=conversation,
            contact=contact,
            timestamp=datetime.now()
        )
        session.add(message)
        session.commit()
        return message

    def get_or_create_contact(self, session: Session, name: str) -> Contact:
        contact = session.exec(select(Contact).where(Contact.name == name)).first()
        
        if contact is None:
            contact = Contact(name=name)
            session.add(contact)
            session.flush()
        
        if not contact.conversations or contact.current_conversation.end_time is not None:
            new_conversation = Conversation(contact=contact)
            session.add(new_conversation)
            session.commit()
        
        return contact 