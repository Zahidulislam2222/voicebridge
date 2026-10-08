"""Pure ownership guards and independent compensating recovery for deployment tools."""

import posixpath
import stat
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

# The frontend release packager's fixed artifact format, not deployment settings.
FRONTEND_RELEASE_FILES = frozenset(
    {"html/index.html", "compose.yaml", "nginx.conf", "site.caddy", "SHA256SUMS", "release.json"}
)


def frontend_release_inventory(directory: Path) -> None:
    files = {
        file.relative_to(directory).as_posix() for file in directory.rglob("*") if file.is_file()
    }
    if files != FRONTEND_RELEASE_FILES:
        raise ValueError("Frontend release must contain exactly the six packaging artifacts")


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
