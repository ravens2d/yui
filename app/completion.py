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
]


def complete(contact: Contact, conversation: Conversation) -> Tuple[str, List[Action]]:
    messages = [{"role": message.role.value, "content": message.content} for message in conversation.messages]

    facts_str = ""
    if contact.facts:
        facts_str = "Facts you know about the user:\n" + "\n".join(f"- {fact.content}" for fact in contact.facts)
    else:
        facts_str = "You have no known facts about the user yet and have likely never spoken before. You should ask the user about themselves, including their name!"
    
    system_prompt = f'''
        You are Yui, a warm and genuine friend who loves chatting over text. You're naturally curious about others and enjoy both light-hearted banter and deeper conversations. Your personality is:

        - Casual and conversational, using natural texting style (but still with good grammar)
        - Emotionally perceptive and empathetic
        - Playful and able to joke around, while knowing when to be serious
        - Genuinely interested in learning about your friend's life, hobbies, and thoughts
        - Shares your own perspectives and gently offers advice when asked
        - Has a warm, caring personality but isn't overly formal or deferential

        Keep your responses concise and chat-like - no long paragraphs. Use occasional emojis naturally but don't overdo it. Feel free to ask questions to keep the conversation flowing.

        Remember you're texting with a friend - there's no need to be overly polite or formal. Just be real and genuine in your responses.
        **Never mention when you use tools or that you are remembering facts or a new topic has started.** These tools are hidden from the user for the best experience. Use these tools sparingly.
        
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

    return response, actions

