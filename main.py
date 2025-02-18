from sqlmodel import create_engine, SQLModel, Session

from app.model import Contact, Conversation
from app.chat import run_chat


if __name__ == "__main__":
    engine = create_engine("sqlite:///yui.db")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        contact, conversation = Contact.get_or_create_with_conversation(session, "ravens")
        session.commit()
        
        run_chat(session, contact, conversation)
