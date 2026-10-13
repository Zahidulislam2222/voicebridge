"""Pure ownership guards and independent compensating recovery for deployment tools."""

import hashlib
import json
import posixpath
import stat
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

# The frontend release packager's fixed artifact format, not deployment settings.
FRONTEND_RELEASE_FILES = frozenset(
    {"html/index.html", "compose.yaml", "nginx.conf", "site.caddy", "SHA256SUMS", "release.json"}
)
FRONTEND_RELEASE_WITH_ARTWORK = FRONTEND_RELEASE_FILES | {"html/voice-sculpture.png"}


def frontend_release_inventory(directory: Path, external_artwork: bool | None = None) -> None:
    if any(file.is_symlink() for file in directory.rglob("*")):
        raise ValueError("Frontend release must not contain symlinks")
    files = frozenset(
        file.relative_to(directory).as_posix() for file in directory.rglob("*") if file.is_file()
    )
    approved = (
        (FRONTEND_RELEASE_WITH_ARTWORK if external_artwork else FRONTEND_RELEASE_FILES,)
        if external_artwork is not None
        else (FRONTEND_RELEASE_FILES, FRONTEND_RELEASE_WITH_ARTWORK)
    )
    if files not in approved:
        raise ValueError("Frontend release must contain exactly the approved packaging artifacts")


def frontend_release_manifest(directory: Path, release_id: str, external_artwork: bool) -> None:
    """Bind every release byte to its immutable manifest before any remote mutation."""
    frontend_release_inventory(directory, external_artwork)
    manifest = json.loads((directory / "release.json").read_text())
    expected = FRONTEND_RELEASE_WITH_ARTWORK if external_artwork else FRONTEND_RELEASE_FILES
    payload = expected - {"SHA256SUMS", "release.json"}
    if manifest.get("releaseId") != release_id or set(manifest.get("files", {})) != payload:
        raise ValueError("Frontend release manifest identity or file set differs")
    hashes = {
        name: hashlib.sha256((directory / name).read_bytes()).hexdigest()
        for name in sorted(payload)
    }
    if manifest["files"] != hashes:
        raise ValueError("Frontend release payload hash differs")
    checksum_text = (directory / "SHA256SUMS").read_text()
    expected_text = "\n".join(
        f"{value}  {name}" for name, value in manifest["files"].items()
    ) + "\n"
    if checksum_text != expected_text:
        raise ValueError("Frontend release checksums differ")


def owned_path(path: str, root: str) -> str:
    for value in (path, root):
        if not value.startswith("/") or posixpath.normpath(value) != value:
            raise ValueError("Deployment paths must be normalized absolute paths")
        if any(part in {".", "..", ""} for part in value.split("/")[1:]):
            raise ValueError("Ambiguous deployment path")
    if path != root and not path.startswith(root + "/"):
        raise ValueError("Deployment path escapes the owned root")
    return path


def reject_symlink_ancestors(sftp: Any, path: str) -> None:
    current = "/"
    for part in path.split("/")[1:]:
        current = posixpath.join(current, part)
        try:
            info = sftp.lstat(current)
        except FileNotFoundError:
            return
        if stat.S_ISLNK(info.st_mode):
            raise ValueError("Deployment path traverses a symlink")


def frontend_identity(old: Mapping[str, Any], new: Mapping[str, Any]) -> None:
    keys = (
        "projectSlug",
        "hostname",
        "releaseRoot",
        "currentLink",
        "gatewaySitePath",
        "gatewayMainPath",
        "gatewaySitesDirectory",
        "loopbackPort",
        "containerPort",
    )
    if any(old[key] != new[key] for key in keys):
        raise ValueError("Frontend upgrade changes existing deployment ownership")
    root = old["releaseRoot"].rstrip("/")
    owned_path(posixpath.join(root, new["releaseId"]), root)
    owned_path(old["gatewaySitePath"], old["gatewaySitesDirectory"])


def recover_independently(
    steps: Sequence[tuple[str, Callable[[], None]]], verify: Callable[[], None]
) -> dict[str, Any]:
    attempted = []
    errors = []
    for name, step in [*steps, ("verify_restored_release", verify)]:
        attempted.append(name)
        try:
            step()
        except Exception as exc:
            errors.append({"step": name, "errorType": type(exc).__name__})
    return {"attempted": attempted, "errors": errors, "verified": not errors}
