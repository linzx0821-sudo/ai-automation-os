import asyncio
import hashlib
import mimetypes
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ArtifactSnapshot:
    path: str
    media_type: str
    size_bytes: int
    sha256: str


@dataclass(slots=True)
class ArtifactIndexer:
    root: Path
    default_workspace: str = "default"
    max_files: int = 500
    max_file_bytes: int = 50 * 1024 * 1024

    async def scan(self, workspace: str | None) -> list[ArtifactSnapshot]:
        return await asyncio.to_thread(self._scan_sync, workspace)

    def _scan_sync(self, workspace: str | None) -> list[ArtifactSnapshot]:
        root = self.root.expanduser().resolve()
        name = workspace or self.default_workspace
        raw = Path(name)
        if raw.is_absolute():
            raise ValueError("Artifact workspace must be relative to the configured root")

        target = (root / raw).resolve()
        if not target.is_relative_to(root):
            raise ValueError("Artifact workspace escapes the configured root")
        if not target.exists():
            return []

        snapshots: list[ArtifactSnapshot] = []
        for file_path in sorted(path for path in target.rglob("*") if path.is_file()):
            relative = file_path.relative_to(target)
            if self._is_ignored(relative):
                continue
            size = file_path.stat().st_size
            if size > self.max_file_bytes:
                continue
            snapshots.append(
                ArtifactSnapshot(
                    path=relative.as_posix(),
                    media_type=mimetypes.guess_type(file_path.name)[0] or "application/octet-stream",
                    size_bytes=size,
                    sha256=self._sha256(file_path),
                )
            )
            if len(snapshots) >= self.max_files:
                break
        return snapshots

    @staticmethod
    def _is_ignored(relative: Path) -> bool:
        parts = set(relative.parts)
        if parts.intersection({".git", ".codex", ".venv", "__pycache__"}):
            return True
        if relative.name in {".env", ".env.local"}:
            return True
        return relative.suffix.lower() in {".key", ".pem", ".p12", ".pfx"}

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
