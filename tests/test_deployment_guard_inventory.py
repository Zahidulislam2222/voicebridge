"""Release inventory guards for the optional immutable artwork artifact."""

import hashlib
import json
from pathlib import Path

import pytest

from tools.deployment_safety import (
    FRONTEND_RELEASE_FILES,
    FRONTEND_RELEASE_WITH_ARTWORK,
    frontend_release_inventory,
    frontend_release_manifest,
)


@pytest.mark.parametrize("names", [FRONTEND_RELEASE_FILES, FRONTEND_RELEASE_WITH_ARTWORK])
def test_exact_frontend_inventories_are_accepted(tmp_path: Path, names: frozenset[str]) -> None:
    for name in names:
        file = tmp_path / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(b"fixture")
    frontend_release_inventory(tmp_path)
    frontend_release_inventory(tmp_path, "html/voice-sculpture.png" in names)


@pytest.mark.parametrize("extra", ["html/debug.json", "secret.env", "html/other.png"])
def test_unapproved_artifacts_are_rejected(tmp_path: Path, extra: str) -> None:
    for name in FRONTEND_RELEASE_WITH_ARTWORK | {extra}:
        file = tmp_path / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(b"fixture")
    with pytest.raises(ValueError, match="exactly"):
        frontend_release_inventory(tmp_path)


def test_manifest_rejects_missing_or_tampered_artwork(tmp_path: Path) -> None:
    names = FRONTEND_RELEASE_WITH_ARTWORK - {"SHA256SUMS", "release.json"}
    hashes = {}
    for name in sorted(names):
        file = tmp_path / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(b"approved")
        hashes[name] = hashlib.sha256(file.read_bytes()).hexdigest()
    (tmp_path / "release.json").write_text(json.dumps({"releaseId": "release-1", "files": hashes}))
    (tmp_path / "SHA256SUMS").write_text(
        "\n".join(f"{value}  {name}" for name, value in hashes.items()) + "\n"
    )
    frontend_release_manifest(tmp_path, "release-1", True)
    artwork = tmp_path / "html/voice-sculpture.png"
    artwork.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="hash"):
        frontend_release_manifest(tmp_path, "release-1", True)
    artwork.unlink()
    with pytest.raises(ValueError, match="exactly"):
        frontend_release_manifest(tmp_path, "release-1", True)
