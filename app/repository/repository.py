from datetime import datetime, UTC
from typing import List
from sqlmodel import create_engine, SQLModel, Session, select

from app.model import Contact, Conversation, Message, Role, Fact

class Repository:
    def __init__(self, db_url: str = "sqlite:///yui.db"):
        self.engine = create_engine(db_url)
        SQLModel.metadata.create_all(self.engine)
        self.session = Session(self.engine)

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
        self.engine.dispose()

    def save_message(self, message: Message) -> Message:
        self.session.add(message)
        self.session.commit()
        return message

    def save_messages(self, messages: List[Message]) -> List[Message]:
        self.session.add_all(messages)
        self.session.commit()
        return messages

    def get_or_create_contact(self, name: str) -> Contact:
        contact = self.session.exec(select(Contact).where(Contact.name == name)).first()
        
        if contact is None:
            contact = Contact(name=name)
            self.session.add(contact)
            self.session.flush()
        
        if not contact.conversations or contact.current_conversation.end_time is not None:
            new_conversation = Conversation(contact=contact)
            self.session.add(new_conversation)
            self.session.commit()
        
        return contact 
    
    def save_fact(self, fact: Fact) -> Fact:
        self.session.add(fact)
        self.session.commit()
        return fact

    def create_conversation(self, contact: Contact) -> Conversation:
        if contact.current_conversation:
            contact.current_conversation.end_time = datetime.now(tz=UTC)
            self.session.add(contact.current_conversation)
        
        conversation = Conversation(contact=contact)
        self.session.add(conversation)
        self.session.commit()
        return conversation

    def save_conversation(self, conversation: Conversation) -> Conversation:
        self.session.add(conversation)
        self.session.commit()
        return conversation

    def get_conversations_for_contact(self, contact: Contact) -> List[Conversation]:
        return self.session.exec(select(Conversation).where(Conversation.contact == contact).order_by(Conversation.start_time.desc())).all()

    def get_messages_for_contact(self, contact: Contact, limit: int = 50) -> List[Message]:
        return self.session.exec(select(Message).where(Message.contact == contact).order_by(Message.timestamp.desc()).limit(limit)).all()
    
    def get_facts_for_contact(self, contact: Contact) -> List[Fact]:
        return self.session.exec(select(Fact).where(Fact.contact == contact)).all() 
    
    def get_messages_for_conversation(self, conversation: Conversation) -> List[Message]:
        return self.session.exec(select(Message).where(Message.conversation == conversation).order_by(Message.timestamp.desc())).all()
