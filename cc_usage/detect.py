"""Auto-detect the Claude Code sessions directory for a given project path."""

import re
from pathlib import Path


def encode_project_path(p: Path) -> str:
    """
    Replicate Claude Code's project-dir naming scheme.

    Every non-alphanumeric character is replaced with a hyphen.

    Windows:  C:\\Users\\foo\\My Project (v2)  ->  C--Users-foo-My-Project--v2-
    Unix:     /home/foo/my-project             ->  home-foo-my-project
    """
    return re.sub(r"[^a-zA-Z0-9]", "-", str(p.resolve()))


def sessions_dir_for(project_path: Path | None = None) -> Path:
    """
    Return ~/.claude/projects/<encoded> for the given (or current) project.

    Falls back to a case-insensitive directory scan to handle drive-letter
    case differences (Claude Code sometimes uses 'c' vs 'C' on Windows).
    """
    target = Path(project_path).resolve() if project_path else Path.cwd().resolve()
    encoded = encode_project_path(target)
    projects_root = Path.home() / ".claude" / "projects"

    direct = projects_root / encoded
    if direct.exists():
        return direct

    # Case-insensitive fallback
    if projects_root.exists():
        encoded_lower = encoded.lower()
        for candidate in projects_root.iterdir():
            if candidate.is_dir() and candidate.name.lower() == encoded_lower:
                return candidate

    return direct  # not found — caller reports the error
