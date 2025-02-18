from typing import List

import anthropic

from app.model import Message, MessageType, Role, Contact


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


def anthropic_messages_to_message(messages: List[anthropic.types.MessageParam], contact: Contact) -> Message:
    res = []
    for message in messages:
        if message.type == "text":
            res.append(Message(role=Role.ASSISTANT, message_type=MessageType.CHAT, content=message.text, conversation=contact.current_conversation, contact=contact))
        elif message.type == "tool_use":
            res.append(Message(role=Role.ASSISTANT, message_type=MessageType.TOOL_USE, conversation=contact.current_conversation, contact=contact, tool_use_id=message.id, tool_use_name=message.name, tool_use_input=message.input))
    return res
