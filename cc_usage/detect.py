"""Auto-detect the Claude Code sessions directory for a given project path."""

import sys
from pathlib import Path


def encode_project_path(p: Path) -> str:
    """
    Replicate Claude Code's project-dir naming scheme.

    Windows:  C:\\Users\\foo\\bar  →  C--Users-foo-bar
    Unix:     /home/foo/bar       →  home-foo-bar
    """
    s = str(p.resolve())
    if sys.platform == "win32":
        s = s.replace(":\\", "--").replace("\\", "-")
    else:
        s = s.lstrip("/").replace("/", "-")
    return s


def sessions_dir_for(project_path: Path | None = None) -> Path:
    """Return ~/.claude/projects/<encoded> for the given (or current) project."""
    target = Path(project_path).resolve() if project_path else Path.cwd().resolve()
    encoded = encode_project_path(target)
    return Path.home() / ".claude" / "projects" / encoded
