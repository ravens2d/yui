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

        conversation = contact.current_conversation

        messages = reversed(await self.repository.get_messages_for_contact(contact)) 
        for message in messages:
            if message.message_type == MessageType.CHAT:
                print_message(message, console)
            elif message.message_type == MessageType.TOOL_USE and message.role == Role.ASSISTANT:
                if message.tool_use_name == ActionType.REMEMBER_FACT.value:
                    console.print(Panel(f"{message.tool_use_input['fact']}", title="[FACT]", title_align="left",  border_style="tool", style="tool"))
                elif message.tool_use_name == ActionType.TOPIC_CHANGED.value:
                    msg_conversation = await self.repository.get_conversation_for_message(message)
                    console.print(Panel(f"{msg_conversation.summary}", title="[SUMMARY]", title_align="left",  border_style="tool", style="tool"))
        
        if messages:
            print()

        while True:
            user_input = Prompt.ask("[green]You[/green]")
            print("\033[2A\033[2K", end="")

            message = await self.repository.save_message(Message(role=Role.USER, content=user_input, conversation=conversation, contact=contact))
            print_message(message, console)
            
            has_text_response = False 
            while not has_text_response:
                responses = await self.completion_gateway.complete(contact) 
                await self.repository.save_messages(messages=responses)

                for response in responses:
                    if response.message_type == MessageType.CHAT:
                        has_text_response = True
                        print_message(response, console)

                    elif response.message_type == MessageType.TOOL_USE:
                        if response.tool_use_name == ActionType.REMEMBER_FACT.value:
                            print(f"[FACT]: {response.tool_use_input['fact']}")
                            await self.repository.save_fact(Fact(content=response.tool_use_input["fact"], contact=contact))
                        elif response.tool_use_name == ActionType.TOPIC_CHANGED.value:
                            prior_conversation = conversation # so that we don't include the message that triggered the tool use in the summary

                            conversation = await self.repository.create_conversation(contact=contact)
                            message.conversation = conversation # we need to update the triggering message to the new conversation
                            await self.repository.save_message(message)

                            summary = await self.completion_gateway.summarize_conversation(prior_conversation)
                            print(f"[SUMMARY]: {summary}")

                        # create matching user response message for tool use response
                        await self.repository.save_message(Message(role=Role.USER, message_type=MessageType.TOOL_USE, content=response.content, conversation=conversation, contact=contact, tool_use_id=response.tool_use_id, tool_use_name=response.tool_use_name, tool_use_input=response.tool_use_input))
        
            print()


def print_message(message: Message, console: Console):
    time_str = message.timestamp.replace(tzinfo=UTC).astimezone(tz=DEFAULT_TIMEZONE).strftime("%H:%M:%S")
    title = f"{'You' if message.role == Role.USER else 'Yui'} • [timestamp]{time_str}[/timestamp]"
    style = message.role.lower()
    console.print(Panel(message.content, title=title, style=style, title_align="left", border_style=style))