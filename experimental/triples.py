import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent)) # dirty dirty hack

from app.repository import Repository
from app.gateway.completion import CompletionGateway


TEST_TRIPLES = [
    {'subject': 'user', 'predicate': 'is named', 'object': 'ravens', 'importance': 9},
    {'subject': 'user', 'predicate': 'is working on', 'object': "chat interface we're currently talking through", 'importance': 8},
    {'subject': 'user', 'predicate': 'finished converting', 'object': 'the whole thing to async', 'importance': 6},
    {'subject': 'user', 'predicate': 'cleaned up', 'object': 'the repo layer', 'importance': 6},
    {'subject': 'user', 'predicate': 'wants to refine', 'object': 'the memory system', 'importance': 8},
    {'subject': 'user', 'predicate': 'is thinking about implementing', 'object': 'knowledge graphs with PageRank for relevancy', 'importance': 9},
    {'subject': 'user', 'predicate': 'uses', 'object': 'Python for development', 'importance': 7},
    {'subject': 'user', 'predicate': 'feels', 'object': 'anxious sometimes', 'importance': 10},
    {'subject': 'user', 'predicate': 'enjoys anime', 'object': 'Made in Abyss and FMA:B', 'importance': 7},
    {'subject': 'user', 'predicate': 'enjoys books', 'object': 'Neuromancer and House of Leaves', 'importance': 7},
    {'subject': 'user', 'predicate': 'enjoys films', 'object': 'No Country for Old Men', 'importance': 7},
    {'subject': 'user', 'predicate': 'appreciates stories with', 'object': 'complex worlds and psychological depth', 'importance': 8},
    {'subject': 'user', 'predicate': 'loves', 'object': 'Ghost in the Shell', 'importance': 9},
    {'subject': 'user', 'predicate': 'dislikes', 'object': "Westworld's most recent season", 'importance': 6},
]


async def fetch_triples():
    async with Repository() as repository:
        contact = await repository.get_contact('ravens')
        messages = await repository.get_messages(contact.id)

        completion_gateway = CompletionGateway(repository)
        triples = await completion_gateway.extract_triples('\n'.join([f"{'assistant' if m.role == 'assistant' else 'user'}: {m.content}" for m in reversed(messages)]))
        return triples


async def main():
    triples = await fetch_triples()
    print(triples)


if __name__ == "__main__":
    asyncio.run(main()) 
    