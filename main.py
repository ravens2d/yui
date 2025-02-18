from app.repository import Repository
from app.controller import ChatController
from app.gateway import CompletionGateway


if __name__ == "__main__":
    with Repository() as repository:
        completion_gateway = CompletionGateway(repository=repository)
        chat_controller = ChatController(repository=repository, completion_gateway=completion_gateway)

        contact = repository.get_or_create_contact('ravens')

        chat_controller.run_chat(contact=contact)