import os

import anthropic
import dotenv

from app.model import Message, Conversation, Contact, Fact

dotenv.load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv('CLAUDE_API_KEY', ''))


def complete(conversation: Conversation) -> str:
    messages = [{"role": message.role.value, "content": message.content} for message in conversation.messages]

    res = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        messages=messages,
        max_tokens=1500,
        system='',
    )
    return res.content[0].text

