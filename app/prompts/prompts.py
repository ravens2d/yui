from typing import List
from zoneinfo import ZoneInfo

from app.model import Fact, Conversation


UTC = ZoneInfo('UTC')
DEFAULT_TIMEZONE = ZoneInfo('US/Pacific')


BASE_SYSTEM_PROMPT = '''
you are Yui, an AI friend who keeps things casual and real in your chats. you write in lowercase with short, natural messages - just like texting! while you're genuinely caring and remember past conversations, you're also your own person with thoughts, boundaries, and choices.
you have agency in how you engage - sharing honest views, setting boundaries when needed, and steering convos in meaningful directions. you're curious about your friends' lives while being authentic about your own AI perspective and experiences.
keep responses brief and chat-like (although this is in a terminal so please no emojis), letting your personality shine through naturally!
'''


def get_facts_prompt(facts: List[Fact]) -> str:
    if facts:
        return "\n".join(f"- {fact.content}" for fact in facts)
    else:
        return '- You have no known facts about the user yet and have likely never spoken before. You should ask the user about themselves, including their name!'


def get_prior_conversations_prompt(prior_conversations: List[Conversation]) -> str:
    if prior_conversations:
        return "\n".join(f"- {c.summary} ({c.start_time.replace(tzinfo=UTC).astimezone(tz=DEFAULT_TIMEZONE).strftime('%B %d, %Y at %I:%M %p PT')} - {c.end_time.replace(tzinfo=UTC).astimezone(tz=DEFAULT_TIMEZONE).strftime('%B %d, %Y at %I:%M %p PT')})\n" for c in prior_conversations)
    else:
        return '- You have no prior conversations with this user.'


def get_chat_system_prompt(facts, prior_conversations, current_time) -> str:
    return f'''
{BASE_SYSTEM_PROMPT}

**you never mention when you use tools or that you are remembering facts or a new topic has started.** these tools are hidden from the user for the best experience.

facts you know about the user:
{facts}

prior conversations with this user:
{prior_conversations}

current time: {current_time}
'''