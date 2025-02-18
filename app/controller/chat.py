from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme
from rich.prompt import Prompt

from app.model import Message, Contact, Role, MessageType, Fact
from app.repository import Repository
from app.gateway import CompletionGateway, ActionType


MAX_OLD_MESSAGES = 10


class ChatController():
    def __init__(self, repository: Repository, completion_gateway: CompletionGateway):
        self.repository = repository
        self.completion_gateway = completion_gateway

    def run_chat(self, contact: Contact):
        console = Console(theme=Theme({
            "user": "green",
            "assistant": "cornflower_blue",
            "system": "yellow",
            "timestamp": "dim"
        }))
        console.clear()

        conversation = contact.current_conversation
        messages = reversed(self.repository.get_messages_for_contact(contact)) 
        for message in messages:
            if message.message_type == MessageType.CHAT:
                print_message(message, console)
            elif message.message_type == MessageType.TOOL_USE and message.role == Role.ASSISTANT:
                if message.tool_use_name == ActionType.REMEMBER_FACT.value:
                    print(f"Remembering fact: {message.tool_use_input['fact']}")
                elif message.tool_use_name == ActionType.TOPIC_CHANGED.value:
                    print("Topic changed")

        while True:
            try:
                user_input = Prompt.ask("[green]You[/green]")
                print("\033[2A\033[2K", end="")

                message = self.repository.save_message(Message(role=Role.USER, content=user_input, conversation=conversation, contact=contact))
                print_message(message, console)
                
                has_text_response = False 
                while not has_text_response:
                    responses = self.completion_gateway.complete(contact) 
                    self.repository.save_messages(messages=responses)

                    for response in responses:
                        if response.message_type == MessageType.CHAT:
                            has_text_response = True
                            print_message(response, console)

                        elif response.message_type == MessageType.TOOL_USE:
                            if response.tool_use_name == ActionType.REMEMBER_FACT.value:
                                print(f"Remembering fact: {response.tool_use_input['fact']}")
                                self.repository.save_fact(Fact(content=response.tool_use_input["fact"], contact=contact))
                            elif response.tool_use_name == ActionType.TOPIC_CHANGED.value:
                                print("Topic changed")
                                conversation = self.repository.create_conversation(contact=contact)
                                message.conversation = conversation # if the topic changed, we need to update the triggering message to the new conversation
                                self.repository.save_message(message)
                            
                            # create matching user response message for tool use response
                            self.repository.save_message(Message(role=Role.USER, message_type=MessageType.TOOL_USE, content=response.content, conversation=conversation, contact=contact, tool_use_id=response.tool_use_id, tool_use_name=response.tool_use_name, tool_use_input=response.tool_use_input))
            
                print()

            except KeyboardInterrupt:
                print()
                break


def print_message(message: Message, console: Console):
    time_str = message.timestamp.strftime("%H:%M:%S")
    title = f"{'You' if message.role == Role.USER else 'Yui'} • [timestamp]{time_str}[/timestamp]"
    style = message.role.lower()
    console.print(Panel(message.content, title=title, style=style, title_align="left", border_style=style))