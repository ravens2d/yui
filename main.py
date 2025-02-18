from app.database import Database
from app.chat import run_chat


if __name__ == "__main__":
    db = Database()
    
    with db.get_session() as session:
        contact, conversation = db.get_or_create_contact_with_conversation(session, "ravens")
        run_chat(session, contact, conversation, db)
