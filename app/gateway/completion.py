import os
from typing import List
from enum import Enum
from datetime import datetime

import anthropic
import dotenv

from app.repository import Repository
from app.model import Contact, Message, Conversation, MessageType
from app.mapper import messages_to_anthropic_message, anthropic_messages_to_messages
from app.prompts import get_chat_system_prompt, get_facts_prompt, get_prior_conversations_prompt, BASE_SYSTEM_PROMPT
from app.constants import DEFAULT_TIMEZONE, UTC


dotenv.load_dotenv()
client = anthropic.AsyncAnthropic(api_key=os.getenv('CLAUDE_API_KEY', ''))


class ActionType(str, Enum):
    REMEMBER_FACT = "remember_fact"
    TOPIC_CHANGED = "topic_changed"


TOOLS = [
    {
        "name": ActionType.REMEMBER_FACT.value,
        "description": "Remember a critical fact about the user. Use this sparingly, as there is a limit on how many facts you can remember. This should be used for critical information that the user has shared about themselves that is constant or invariant only.",
        "input_schema": {
            "type": "object",
            "properties": {"fact": {"type": "string", "description": "The fact to remember"}},
            "required": ["fact"],
        },
    },
    {
        "name": ActionType.TOPIC_CHANGED.value,
        "description": "The topic of the conversation has changed. This should be only at a natural break in the conversation, when the user has changed the topic of the conversation, or when you have lost track of the topic.",
        "input_schema": {
            "type": "object",
        },
    },
]


class CompletionGateway():
    def __init__(self, repository: Repository):
        self.repository = repository
    
    async def complete(self, contact: Contact, conversation: Conversation) -> List[Message]:
        db_messages = await self.repository.get_messages(contact.id)
        messages = messages_to_anthropic_message(reversed(db_messages))

        facts = get_facts_prompt(await self.repository.get_facts(contact.id))
        conversations = await self.repository.get_conversations(contact.id)
        conversations_with_summaries = [c for c in reversed(conversations) if c.summary]
        prior_conversations = get_prior_conversations_prompt(conversations_with_summaries)
        current_time = datetime.now(tz=DEFAULT_TIMEZONE).strftime('%B %d, %Y at %I:%M %p PT')
        system_prompt = get_chat_system_prompt(facts, prior_conversations, current_time)

        res = await client.messages.create(
            model="claude-3-7-sonnet-latest",
            messages=messages,
            max_tokens=1500,
            system=system_prompt,
            tools=TOOLS,
        )
        return anthropic_messages_to_messages(res.content, contact.id, conversation.id)

    async def summarize_conversation(self, conversation: Conversation) -> str:
        db_messages = await self.repository.get_messages_for_conversation(conversation.id)
        db_messages = [m for m in db_messages if m.message_type == MessageType.CHAT] # filter out tool use
        messages = messages_to_anthropic_message(reversed(db_messages))
        
        system_prompt = f'''
        {BASE_SYSTEM_PROMPT}

        summarize the following conversation in one to two sentences from your perspective for your own memory.'''
        messages.append(anthropic.types.MessageParam(role="user", content="summarize the conversation in one to two sentences from your perspective for your own memory.")) # we have to end on a user message i guess lol

        res = await client.messages.create(
            model="claude-3-5-sonnet-20240620",
            messages=messages,
            max_tokens=1500,
            system=system_prompt,
        )

        conversation.end_time = datetime.now(tz=UTC)
        conversation.summary = res.content[0].text
        await self.repository.update_conversation(conversation)
        return conversation.summary