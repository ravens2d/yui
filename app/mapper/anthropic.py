from typing import List

import anthropic

from app.model import Message, MessageType, Role, Contact


def messages_to_anthropic_message(messages: List[Message]) -> List[anthropic.types.MessageParam]:
    results = []

    for i, message in enumerate(messages):
        cache_control = None
        if i == len(messages) - 1:
            cache_control = {"type": "ephemeral"}

        if message.message_type == MessageType.CHAT:
            results.append(anthropic.types.MessageParam(role=message.role.value, content=[anthropic.types.TextBlockParam(type="text", text=message.content, cache_control=cache_control)]))
        elif message.message_type == MessageType.TOOL_USE:
            if message.role == Role.ASSISTANT:
                results.append(anthropic.types.MessageParam(role=message.role.value, content=[anthropic.types.ToolUseBlockParam(id=message.tool_use_id, name=message.tool_use_name, input=message.tool_use_input, type="tool_use", cache_control=cache_control)]))
            elif message.role == Role.USER:
                results.append(anthropic.types.MessageParam(role=message.role.value, content=[anthropic.types.ToolResultBlockParam(tool_use_id=message.tool_use_id, content=message.content, type="tool_result", cache_control=cache_control)]))
    
    return results


def anthropic_messages_to_messages(messages: List[anthropic.types.MessageParam], contact_id: str, conversation_id: str) -> List[Message]:
    res = []
    for message in messages:
        if message.type == "text":
            res.append(Message(role=Role.ASSISTANT, message_type=MessageType.CHAT, content=message.text, contact_id=contact_id, conversation_id=conversation_id))
        elif message.type == "tool_use":
            res.append(Message(role=Role.ASSISTANT, message_type=MessageType.TOOL_USE, contact_id=contact_id, conversation_id=conversation_id, tool_use_id=message.id, tool_use_name=message.name, tool_use_input=message.input))
    return res
