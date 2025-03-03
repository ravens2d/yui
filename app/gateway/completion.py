import os
from typing import List
from enum import Enum
from datetime import datetime, timedelta

import anthropic
import dotenv

from app.repository import Repository
from app.model import Contact, Message, Conversation, MessageType
from app.mapper import messages_to_anthropic_message, anthropic_messages_to_messages
from app.prompts import get_chat_system_prompt, get_facts_prompt, get_prior_conversations_prompt, BASE_SYSTEM_PROMPT
from app.constants import DEFAULT_TIMEZONE, UTC


dotenv.load_dotenv()
client = anthropic.AsyncAnthropic(api_key=os.getenv('CLAUDE_API_KEY', ''))
MODEL_NAME = "claude-3-7-sonnet-latest"

class ActionType(str, Enum):
    REMEMBER_FACT = "remember_fact"
    TOPIC_CHANGED = "topic_changed"
    REQUIRES_FOLLOW_UP = "requires_follow_up"
    EXTRACT_TRIPLES = "extract_triples"

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
    {
        "name": ActionType.REQUIRES_FOLLOW_UP.value,
        "description": "Signals that you want to send an additional message after this one without waiting for user input. Use this when you want to split your message into multiple natural messages, specifically for longer messages or natural breaks, similar to texting. The system will immediately prompt you for your follow-up message after htis one is sent. After this call completes, immediately provide the follow up message in the next turn.",
        "input_schema": {
            "type": "object",
        },
    }
]

CORPUS_TOOLS = [
    {
        "name": ActionType.EXTRACT_TRIPLES.value,
        "description": "Extract the triples from the conversation. Only include novel information that you do not already understand or know implicitly. Focus on important details about the user that may boost EQ for future responses. The importance score should be a number from 1-10, where 1 is not important and 10 is very important, and should reflect the future importance of the information to you in terms of EQ.",
        "input_schema": {
            "type": "object",
            "properties": {"triples": {"type": "array", "items": {"type": "object", "properties": {
                "subject": {"type": "string"},
                "predicate": {"type": "string"},
                "object": {"type": "string"},
                "importance": {"type": "integer", "minimum": 1, "maximum": 10}
            }, "required": ["subject", "predicate", "object", "importance"]}, "description": "The triples to extract from the conversation as objects with subject, predicate, object and importance score from 1-10"}},
            "required": ["triples"],
        },
    },
]


class CompletionGateway():
    def __init__(self, repository: Repository):
        self.repository = repository
        self.cached_time = None
    
    async def complete(self, contact: Contact, conversation: Conversation) -> List[Message]:
        db_messages = await self.repository.get_messages(contact.id)
        messages = messages_to_anthropic_message(list(reversed(db_messages)))

        facts = get_facts_prompt(await self.repository.get_facts(contact.id))
        conversations = await self.repository.get_conversations(contact.id)
        conversations_with_summaries = [c for c in reversed(conversations) if c.summary]
        prior_conversations = get_prior_conversations_prompt(conversations_with_summaries)
        
        if self.cached_time is None or self.cached_time < datetime.now(tz=DEFAULT_TIMEZONE) - timedelta(minutes=10):
            self.cached_time = datetime.now(tz=DEFAULT_TIMEZONE)

        system_prompt = get_chat_system_prompt(facts, prior_conversations, self.cached_time.strftime('%B %d, %Y at %I:%M %p PT'))

        res = await client.messages.create(
            model=MODEL_NAME,
            tools=TOOLS,
            system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
            messages=messages,
            max_tokens=1500,
        )
        return anthropic_messages_to_messages(res.content, contact.id, conversation.id)

    async def summarize_conversation(self, conversation: Conversation) -> str:
        db_messages = await self.repository.get_messages_for_conversation(conversation.id)
        db_messages = [m for m in db_messages if m.message_type == MessageType.CHAT] # filter out tool use
        messages = messages_to_anthropic_message(list(reversed(db_messages)))
        
        system_prompt = f'''
        {BASE_SYSTEM_PROMPT}

        summarize the following conversation in one to two sentences from your perspective for your own memory.'''
        messages.append(anthropic.types.MessageParam(role="user", content="summarize the conversation in one to two sentences from your perspective for your own memory.")) # we have to end on a user message i guess lol

        res = await client.messages.create(
            model=MODEL_NAME,
            messages=messages,
            max_tokens=1500,
            system=system_prompt,
        )

        conversation.end_time = datetime.now(tz=UTC)
        conversation.summary = res.content[0].text
        await self.repository.update_conversation(conversation)
        return conversation.summary

    async def extract_triples(self, corpus: str) -> List[str]:
        print(corpus)
        res = await client.messages.create(
            model=MODEL_NAME,
            messages=[anthropic.types.MessageParam(role="user", content=corpus)],
            max_tokens=1500,
            system="Please extract the triples from the following corpus. The triples should be in the format of (subject, predicate, object). Respond with only the triples, no other text. Only include novel information that you do not already understand or know implicitly. Focus on important details about the user that may boost EQ for future responses.",
            tools=CORPUS_TOOLS,
            tool_choice={"type": "tool", "name": ActionType.EXTRACT_TRIPLES.value},
        )
        return res.content[0].input['triples']
    