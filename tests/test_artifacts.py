import hashlib

import pytest

from app.services.artifact_indexer import ArtifactIndexer


@pytest.mark.asyncio
async def test_artifact_indexer_hashes_outputs_and_skips_secrets(tmp_path) -> None:
    workspace = tmp_path / "investment" / "acme"
    research = workspace / "research"
    research.mkdir(parents=True)
    report = research / "report.md"
    report.write_text("# Research\nEvidence first.\n", encoding="utf-8")
    (workspace / ".env").write_text("SECRET=do-not-index", encoding="utf-8")
    git_dir = workspace / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text("ignored", encoding="utf-8")

    snapshots = await ArtifactIndexer(root=tmp_path).scan("investment/acme")

    assert len(snapshots) == 1
    snapshot = snapshots[0]
    assert snapshot.path == "research/report.md"
    assert snapshot.media_type == "text/markdown"
    assert snapshot.size_bytes == report.stat().st_size
    assert snapshot.sha256 == hashlib.sha256(report.read_bytes()).hexdigest()


@pytest.mark.asyncio
async def test_artifact_indexer_rejects_workspace_escape(tmp_path) -> None:
    with pytest.raises(ValueError, match="escapes"):
        await ArtifactIndexer(root=tmp_path).scan("../outside")
