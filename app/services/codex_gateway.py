from dataclasses import dataclass
from typing import Protocol
from uuid import uuid4

from openai_codex import AsyncCodex, Sandbox

from app.core.config import Settings
from app.services.workspace import WorkspaceManager


@dataclass(slots=True)
class CodexRunResult:
    thread_id: str
    final_response: str


class CodexGateway(Protocol):
    async def start(self, goal: str, workspace: str | None = None) -> CodexRunResult: ...

    async def resume(
        self, thread_id: str, instruction: str, workspace: str | None = None
    ) -> CodexRunResult: ...


class StubCodexGateway:
    """Deterministic interface-compatible adapter for tests and local API work."""

    async def start(self, goal: str, workspace: str | None = None) -> CodexRunResult:
        return CodexRunResult(
            thread_id=f"stub:{uuid4()}",
            final_response="Codex gateway is running in stub mode.",
        )

    async def resume(
        self, thread_id: str, instruction: str, workspace: str | None = None
    ) -> CodexRunResult:
        return CodexRunResult(
            thread_id=thread_id,
            final_response="Codex gateway is running in stub mode.",
        )


@dataclass(slots=True)
class SDKCodexGateway:
    settings: Settings
    workspaces: WorkspaceManager

    async def _authenticate(self, codex: AsyncCodex) -> None:
        if self.settings.codex_api_key is not None:
            await codex.login_api_key(self.settings.codex_api_key.get_secret_value())

    async def start(self, goal: str, workspace: str | None = None) -> CodexRunResult:
        cwd = await self.workspaces.prepare(workspace)
        async with AsyncCodex() as codex:
            await self._authenticate(codex)
            kwargs: dict[str, object] = {
                "cwd": str(cwd),
                "sandbox": Sandbox.workspace_write,
            }
            if self.settings.codex_model:
                kwargs["model"] = self.settings.codex_model
            thread = await codex.thread_start(**kwargs)
            result = await thread.run(goal)
            return CodexRunResult(thread_id=thread.id, final_response=result.final_response)

    async def resume(
        self, thread_id: str, instruction: str, workspace: str | None = None
    ) -> CodexRunResult:
        cwd = await self.workspaces.prepare(workspace)
        async with AsyncCodex() as codex:
            await self._authenticate(codex)
            kwargs: dict[str, object] = {
                "cwd": str(cwd),
                "sandbox": Sandbox.workspace_write,
            }
            if self.settings.codex_model:
                kwargs["model"] = self.settings.codex_model
            thread = await codex.thread_resume(thread_id, **kwargs)
            result = await thread.run(instruction)
            return CodexRunResult(thread_id=thread.id, final_response=result.final_response)


def build_codex_gateway(settings: Settings) -> CodexGateway:
    if settings.codex_backend == "sdk":
        return SDKCodexGateway(
            settings=settings,
            workspaces=WorkspaceManager(
                root=settings.codex_workspace_root,
                default_name=settings.codex_default_workspace,
            ),
        )
    return StubCodexGateway()
