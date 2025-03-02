import asyncio

from app.repository import Repository
from app.controller import ChatController
from app.gateway import CompletionGateway


async def main():
    async with Repository() as repository:
        completion_gateway = CompletionGateway(repository=repository)
        chat_controller = ChatController(repository=repository, completion_gateway=completion_gateway)

        contact = await repository.get_or_create_contact('ravens')

        await chat_controller.run_chat(contact=contact)


if __name__ == "__main__":
    asyncio.run(main())