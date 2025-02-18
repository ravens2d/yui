from datetime import datetime

from sqlmodel import create_engine, SQLModel, Session
from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme
from rich.prompt import Prompt

from app.model import Message, Conversation, Contact, Fact, Role
from app.completion import complete


MAX_OLD_MESSAGES = 10


def run_chat(session: Session, contact: Contact, conversation: Conversation):
    console = Console(theme=Theme({
        "user": "green",
        "assistant": "cornflower_blue",
        "system": "yellow",
        "timestamp": "dim"
    }))
    console.clear()

    messages = conversation.messages[-MAX_OLD_MESSAGES:] if len(conversation.messages) > MAX_OLD_MESSAGES else conversation.messages
    for message in messages:
        print_message(message, console)
    print()

    while True:
        try:
            user_input = Prompt.ask("[green]You[/green]")
            print("\033[2A\033[2K", end="")

            message = Message(role=Role.USER, content=user_input, conversation=conversation, contact=contact, timestamp=datetime.now())
            session.add(message)
            session.commit()
            print_message(message, console)
            
            response = complete(conversation)
            response_message = Message(role=Role.ASSISTANT, content=response, conversation=conversation, contact=contact, timestamp=datetime.now())
            session.add(response_message)
            session.commit()
            print_message(response_message, console)
            print()

        except KeyboardInterrupt:
            print()
            break


def print_message(message: Message, console: Console):
    time_str = message.timestamp.strftime("%H:%M:%S")
    title = f"{message.role.title()} • [timestamp]{time_str}[/timestamp]"
    style = message.role.lower()
    console.print(Panel(
        message.content,
        title=title,
        style=style,
        title_align="left",
        border_style=style
    ))