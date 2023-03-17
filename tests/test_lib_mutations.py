import pytest

from juniorguru.lib.mutations import Mutations


def test_mutations():
    mutations = Mutations()
    mutations.allow('discord')

    def fakturoid():
        return 1
    fakturoid_fn = mutations.mutation('fakturoid', fakturoid)
    fakturoid_val = fakturoid_fn()

    def discord():
        return 2
    discord_fn = mutations.mutation('discord', discord)
    discord_val = discord_fn()

    assert fakturoid_val is None
    assert discord_val == 2


@pytest.mark.asyncio
async def test_mutations_async():
    mutations = Mutations()
    mutations.allow('discord')

    async def fakturoid():
        return 1
    fakturoid_fn = mutations.mutation('fakturoid', fakturoid)
    fakturoid_val = await fakturoid_fn()

    async def discord():
        return 2
    discord_fn = mutations.mutation('discord', discord)
    discord_val = await discord_fn()

    assert fakturoid_val is None
    assert discord_val == 2
