import os
from dataclasses import dataclass
from typing import Optional, Tuple, List
from enum import Enum

import anthropic
import dotenv

from app.model import Message, Conversation, Contact, Fact

dotenv.load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv('CLAUDE_API_KEY', ''))

@dataclass
class Action:
    type: "ActionType"
    fact: Optional[str] = None


class ActionType(str, Enum):
    REMEMBER_FACT = "remember_fact"
    TOPIC_CHANGED = "topic_changed"


TOOLS = [
    {
        "name": ActionType.REMEMBER_FACT.value,
        "description": "Remember a critical fact about the user. Use this very sparingly, as there is a limit on how many facts you can remember. This should be used for critical information that the user has shared about themselves that is constant or invariant only.",
        "input_schema": {
            "type": "object",
            "properties": {"fact": {"type": "string", "description": "The fact to remember"}},
            "required": ["fact"],
        },
    },
    {
        "name": ActionType.TOPIC_CHANGED.value,
        "description": "Use this to indicate that a new conversational topic has been started that radically deviates from the prior conversation. This will create a new conversation record for future summary and memory.",
        "input_schema": {
            "type": "object",
        },
    },
]


def complete(contact: Contact, conversation: Conversation) -> Tuple[str, List[Action]]:
    messages = [{"role": message.role.value, "content": message.content} for message in conversation.messages]

    facts_str = ""
    if contact.facts:
        facts_str = "Known facts about the user:\n" + "\n".join(f"- {fact.content}" for fact in contact.facts)
    
    system_prompt = f'''
        You are a helpful assistant named Yui. **Never mention when you use tools or that you are remembering facts or a new topic has started.** These tools are hidden from the user for the best experience. Use these tools sparingly.
        {facts_str}'''

    res = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        messages=messages,
        max_tokens=1500,
        system=system_prompt,
        tools=TOOLS,
    )

    actions = []
    response = ""

    for value in res.content:
        if value.type == "text":
            response += value.text
        elif value.type == "tool_use":
            if value.name == ActionType.REMEMBER_FACT.value:
                actions.append(Action(type=ActionType.REMEMBER_FACT, fact=value.input["fact"]))
            elif value.name == ActionType.TOPIC_CHANGED.value:
                actions.append(Action(type=ActionType.TOPIC_CHANGED))

    return response, actions

