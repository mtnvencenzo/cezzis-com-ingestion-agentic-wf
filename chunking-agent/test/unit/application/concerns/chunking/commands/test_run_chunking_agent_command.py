import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cocktails_chunking_agent.application.concerns.chunking.commands.run_chunking_agent_command import (
    RunChunkingAgentCommand,
    RunChunkingAgentCommandHandler,
)

SPAWN = (
    "cocktails_chunking_agent.application.concerns.chunking.commands.run_chunking_agent_command.spawn_consumers_async"
)


def _handler(enabled: bool) -> RunChunkingAgentCommandHandler:
    app_options = MagicMock(enabled=enabled, num_consumers=1)
    return RunChunkingAgentCommandHandler(app_options, MagicMock())


class TestRunChunkingAgentCommandHandler:
    def test_a_disabled_agent_stays_running_without_consuming(self) -> None:
        async def run():
            with patch(SPAWN, new=AsyncMock()) as spawn:
                task = asyncio.create_task(_handler(enabled=False).handle(RunChunkingAgentCommand()))
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
            result = asyncio.run(_handler(enabled=True).handle(RunChunkingAgentCommand()))

        assert result is True
        spawn.assert_awaited_once()
