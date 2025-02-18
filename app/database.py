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

    def get_or_create_contact_with_conversation(self, session: Session, name: str) -> Tuple[Contact, Conversation]:
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
            session.commit()
        
        return contact, latest_conversation 