import asyncio
from dataclasses import dataclass
from pathlib import Path


class WorkspaceError(RuntimeError):
    pass


@dataclass(slots=True)
class WorkspaceManager:
    root: Path
    default_name: str = "default"

    async def prepare(self, requested: str | None = None) -> Path:
        root = self.root.expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)

        name = requested or self.default_name
        raw = Path(name)
        if raw.is_absolute():
            raise WorkspaceError("Workspace must be a relative path inside the workspace root")

        workspace = (root / raw).resolve()
        if not workspace.is_relative_to(root):
            raise WorkspaceError("Workspace escapes the configured workspace root")

        workspace.mkdir(parents=True, exist_ok=True)
        if not (workspace / ".git").exists():
            process = await asyncio.create_subprocess_exec(
                "git",
                "-C",
                str(workspace),
                "init",
                "--quiet",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await process.communicate()
            if process.returncode != 0:
                raise WorkspaceError(
                    f"Unable to initialize workspace git repository: {stderr.decode().strip()}"
                )

        return workspace
