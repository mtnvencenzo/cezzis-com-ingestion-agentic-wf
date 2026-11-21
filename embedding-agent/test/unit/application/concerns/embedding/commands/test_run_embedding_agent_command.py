import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cocktails_embedding_agent.application.concerns.embedding.commands.run_embedding_agent_command import (
    RunEmbeddingAgentCommand,
    RunEmbeddingAgentCommandHandler,
)

SPAWN = "cocktails_embedding_agent.application.concerns.embedding.commands.run_embedding_agent_command.spawn_consumers_async"


def _handler(enabled: bool) -> RunEmbeddingAgentCommandHandler:
    app_options = MagicMock(enabled=enabled, num_consumers=1)
    return RunEmbeddingAgentCommandHandler(app_options, MagicMock())


class TestRunEmbeddingAgentCommandHandler:
    def test_a_disabled_agent_stays_running_without_consuming(self) -> None:
        async def run():
            with patch(SPAWN, new=AsyncMock()) as spawn:
                task = asyncio.create_task(_handler(enabled=False).handle(RunEmbeddingAgentCommand()))
                await asyncio.sleep(0.1)

                # Still running (not exited, which would crash-loop the pod), and nothing was consumed
                assert not task.done()
                spawn.assert_not_called()

                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await task

        asyncio.run(run())

    def test_an_enabled_agent_consumes(self) -> None:
        with patch(SPAWN, new=AsyncMock()) as spawn:
            result = asyncio.run(_handler(enabled=True).handle(RunEmbeddingAgentCommand()))

        assert result is True
        spawn.assert_awaited_once()
