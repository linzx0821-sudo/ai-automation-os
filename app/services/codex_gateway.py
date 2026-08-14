from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class CodexRunResult:
    thread_id: str
    final_response: str


class CodexGateway(Protocol):
    async def start(self, goal: str, workspace: str | None = None) -> CodexRunResult: ...

    async def resume(self, thread_id: str, instruction: str) -> CodexRunResult: ...


class StubCodexGateway:
    """Temporary adapter used until the hosted Codex execution adapter is wired in."""

    async def start(self, goal: str, workspace: str | None = None) -> CodexRunResult:
        return CodexRunResult(
            thread_id=f"stub:{abs(hash((goal, workspace)))}",
            final_response="Codex gateway not configured yet.",
        )

    async def resume(self, thread_id: str, instruction: str) -> CodexRunResult:
        return CodexRunResult(
            thread_id=thread_id,
            final_response="Codex gateway not configured yet.",
        )
