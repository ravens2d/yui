import asyncio

from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme
from rich.prompt import Prompt

from app.model import Message, Contact, Role, MessageType, Fact
from app.repository import Repository
from app.gateway import CompletionGateway, ActionType
from app.constants import DEFAULT_TIMEZONE, UTC


class ChatController():
    def __init__(self, repository: Repository, completion_gateway: CompletionGateway):
        self.repository = repository
        self.completion_gateway = completion_gateway

    async def run_chat(self, contact: Contact):
        console = Console(theme=Theme({
            "user": "green",
            "assistant": "cornflower_blue",
            "system": "yellow",
            "timestamp": "dim",
            "tool": "grey70",
        }))
        console.clear()

        conversation = await self.repository.get_conversation(contact.id)
        if not conversation:
            conversation = await self.repository.create_conversation(contact.id)
        
        messages = reversed(await self.repository.get_messages(contact.id)) 
        for message in messages:
            if message.message_type == MessageType.CHAT:
                print_message(message, console)
            elif message.message_type == MessageType.TOOL_USE and message.role == Role.ASSISTANT:
                if message.tool_use_name == ActionType.REMEMBER_FACT.value:
                    console.print(Panel(f"{message.tool_use_input['fact']}", title="Fact", title_align="left",  border_style="tool", style="tool"))
                elif message.tool_use_name == ActionType.TOPIC_CHANGED.value:
                    msg_conversation = await self.repository.get_conversation_for_message(message.id)
                    console.print(Panel(f"{msg_conversation.summary}", title="Summary", title_align="left",  border_style="tool", style="tool"))
        
        if messages:
            print()

        while True:
            user_input = Prompt.ask("[green]You[/green]")
            print("\033[2A\033[2K", end="")

            message = await self.repository.create_message(Message(role=Role.USER, content=user_input, conversation_id=conversation.id, contact_id=contact.id))
            print_message(message, console)
            
            has_text_response = False
            has_follow_up_response = False
            while not has_text_response or has_follow_up_response:
                completion_task = asyncio.create_task(self.completion_gateway.complete(contact, conversation))
                has_follow_up_response = False
                
                while not completion_task.done():
                    for dots in range(0, 4):
                        print("\033[90m" + "..."[0:dots] + "\033[0m", end="", flush=True)
                        await asyncio.sleep(0.3)
                        print("\r\033[K", end="")

                responses = await completion_task
                await self.repository.create_messages(responses)

                for response in responses:
                    if response.message_type == MessageType.CHAT:
                        has_text_response = True
                        print_message(response, console)

                    elif response.message_type == MessageType.TOOL_USE:
                        if response.tool_use_name == ActionType.REMEMBER_FACT.value:
                            console.print(Panel(f"{response.tool_use_input['fact']}", title="Fact", title_align="left",  border_style="tool", style="tool"))
                            await self.repository.create_fact(Fact(content=response.tool_use_input["fact"], contact_id=contact.id))
                        elif response.tool_use_name == ActionType.TOPIC_CHANGED.value:
                            prior_conversation = conversation # so that we don't include the message that triggered the tool use in the summary

                            conversation = await self.repository.create_conversation(contact_id=contact.id)
                            await self.repository.create_message(message)

                            summary = await self.completion_gateway.summarize_conversation(prior_conversation)
                            console.print(Panel(f"{summary}", title="Summary", title_align="left",  border_style="tool", style="tool"))
                        elif response.tool_use_name == ActionType.REQUIRES_FOLLOW_UP.value:
                            has_follow_up_response = True # prompt the model again without waiting for user response

                        # create matching user response message for tool use response
                        await self.repository.create_message(Message(role=Role.USER, message_type=MessageType.TOOL_USE, content=response.content, conversation_id=conversation.id, contact_id=contact.id, tool_use_id=response.tool_use_id, tool_use_name=response.tool_use_name, tool_use_input=response.tool_use_input))
        
            print()


def print_message(message: Message, console: Console):
    time_str = message.timestamp.replace(tzinfo=UTC).astimezone(tz=DEFAULT_TIMEZONE).strftime("%I:%M:%S %p")
    title = f"{'You' if message.role == Role.USER else 'Yui'} • [timestamp]{time_str}[/timestamp]"
    style = message.role.lower()
    console.print(Panel(message.content, title=title, style=style, title_align="left", border_style=style))