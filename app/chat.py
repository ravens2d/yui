from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme
from rich.prompt import Prompt

from app.model import Message, Conversation, Contact, Role
from app.completion import complete, Action, ActionType
from app.database import Database


MAX_OLD_MESSAGES = 10


def run_chat(session, contact: Contact, db: Database):
    console = Console(theme=Theme({
        "user": "green",
        "assistant": "cornflower_blue",
        "system": "yellow",
        "timestamp": "dim"
    }))
    console.clear()

    conversation = contact.current_conversation
    messages = conversation.messages[-MAX_OLD_MESSAGES:] if len(conversation.messages) > MAX_OLD_MESSAGES else conversation.messages
    for message in messages:
        print_message(message, console)

    while True:
        try:
            user_input = Prompt.ask("[green]You[/green]")
            print("\033[2A\033[2K", end="")

            message = db.save_message(session=session, role=Role.USER, content=user_input, conversation=conversation, contact=contact)
            print_message(message, console)
            
            response, actions = complete(contact, conversation)
            for action in actions:
                if action.type == ActionType.REMEMBER_FACT:
                    print(f"Remembering fact: {action.fact}")
                    db.save_fact(session=session, content=action.fact, contact=contact)

            response_message = db.save_message(session=session, role=Role.ASSISTANT, content=response, conversation=conversation, contact=contact)
            print_message(response_message, console)
            print()

        except KeyboardInterrupt:
            print()
            break


def print_message(message: Message, console: Console):
    time_str = message.timestamp.strftime("%H:%M:%S")
    title = f"{'You' if message.role == Role.USER else 'Yui'} • [timestamp]{time_str}[/timestamp]"
    style = message.role.lower()
    console.print(Panel(message.content, title=title, style=style, title_align="left", border_style=style))