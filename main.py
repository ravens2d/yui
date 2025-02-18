from app.database import Database
from app.chat import run_chat


if __name__ == "__main__":
    db = Database()
    
    with db.get_session() as session:
        contact = db.get_or_create_contact(session, "some_user")
        run_chat(session, contact, db)
