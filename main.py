import asyncio
import signal
import sys

from app.repository import Repository
from app.controller import ChatController
from app.gateway import CompletionGateway


def handle_sigint(sig, frame):
    print("")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_sigint)


async def main():
    async with Repository() as repository:
        completion_gateway = CompletionGateway(repository=repository)
        chat_controller = ChatController(repository=repository, completion_gateway=completion_gateway)

        contact = await repository.get_or_create_contact('ravens')

        await chat_controller.run_chat(contact=contact)


if __name__ == "__main__":
    asyncio.run(main())