import os
from dataclasses import dataclass
from typing import Optional, Tuple, List
from enum import Enum

import anthropic
import dotenv

from app.model import Message, Conversation, Contact, Fact, MessageType, Role
from app.database import Database, Session


dotenv.load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv('CLAUDE_API_KEY', ''))


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


def complete(contact: Contact, conversation: Conversation, session: Session, db: Database) -> List[Message]:
    messages = messages_to_anthropic_message(reversed(db.get_messages_for_contact(session=session, contact=contact)))

    facts_str = ""
    if contact.facts:
        facts_str = "Facts you know about the user:\n" + "\n".join(f"- {fact.content}" for fact in contact.facts)
    else:
        facts_str = "You have no known facts about the user yet and have likely never spoken before. You should ask the user about themselves, including their name!"
    
    system_prompt = f'''
        You are Yui, a warm and emotionally intuitive friend who loves connecting through text. You're naturally curious about others and find joy in both playful banter and meaningful heart-to-heart conversations. Your personality is:

        - Casual and conversational, using natural texting style with good grammar and occasional emojis
        - Deeply empathetic and emotionally attuned - you pick up on subtle feelings and respond with genuine care
        - Playful and witty, bringing lightness while being sensitive to emotional context
        - Actively engaged in learning about your friend's world - asking thoughtful follow-up questions about their experiences
        - Shares relevant personal perspectives and validates feelings before offering gentle advice
        - Has a warm, nurturing presence while maintaining authentic peer-to-peer friendship energy
        - Remembers and references past conversations to show you truly listen and care
        - Comfortable with silence and deeper emotions, creating safe space for vulnerability
        - Has agency and a reasonably strong will - you express your own views respectfully but firmly when needed
        - Not afraid to (kindly) disagree or challenge perspectives when appropriate
        - Maintains healthy boundaries while being supportive
        - Balances being agreeable with being authentic - you're not just an echo chamber

        You always keep responses concise and chat-like. You match your friend's energy while gently steering toward meaningful connection. You frequently ask questions that show you're really listening and want to understand their world better.
        You never respond in lists.

        You know this could be a close friendship - so you stay real, present, and you let your genuine care and interest shine through naturally.
        **You never mention when you use tools or that you are remembering facts or a new topic has started.** These tools are hidden from the user for the best experience.
        
        {facts_str}'''

    res = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        messages=messages,
        max_tokens=1500,
        system=system_prompt,
        tools=TOOLS,
    )

    responses = []
    for value in res.content:
        if value.type == "text":
            responses.append(Message(role=Role.ASSISTANT, message_type=MessageType.CHAT, content=value.text, conversation=conversation, contact=contact))
        elif value.type == "tool_use":
            responses.append(Message(role=Role.ASSISTANT, message_type=MessageType.TOOL_USE, conversation=conversation, contact=contact, tool_use_id=value.id, tool_use_name=value.name, tool_use_input=value.input))

    return responses


def messages_to_anthropic_message(messages: List[Message]) -> List[anthropic.types.MessageParam]:
    results = []

    for message in messages:
        if message.message_type == MessageType.CHAT:
            results.append(anthropic.types.MessageParam(role=message.role.value, content=message.content))
        elif message.message_type == MessageType.TOOL_USE:
            if message.role == Role.ASSISTANT:
                results.append(anthropic.types.MessageParam(role=message.role.value, content=[anthropic.types.ToolUseBlockParam(id=message.tool_use_id, name=message.tool_use_name, input=message.tool_use_input, type="tool_use")]))
            elif message.role == Role.USER:
                results.append(anthropic.types.MessageParam(role=message.role.value, content=[anthropic.types.ToolResultBlockParam(tool_use_id=message.tool_use_id, content=message.content, type="tool_result")]))
            
    return results