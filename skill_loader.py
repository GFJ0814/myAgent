import re
from pathlib import Path
from typing import Any


SKILL_FILE_NAME = "SKILL.md"
SKILLS_ROOT = Path(__file__).resolve().parent / "skills"


def load_skills(skills_root: Path | None = None) -> dict[str, dict[str, Any]]:
    root = skills_root or SKILLS_ROOT
    if not root.exists():
        return {}

    skills: dict[str, dict[str, Any]] = {}
    for skill_dir in _collect_candidate_dirs(root):
        skill_file = skill_dir / SKILL_FILE_NAME
        metadata, instructions = _read_skill_definition(skill_file)

        if not _is_enabled(metadata):
            continue

        name = _resolve_skill_name(skill_dir, metadata)
        if name in skills:
            continue

        description = _resolve_description(instructions, metadata, name)
        skills[name] = {
            "kind": "skill",
            "name": name,
            "path": str(skill_dir),
            "description": description,
            "instructions": instructions.strip(),
            "metadata": metadata,
            "schema": {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task": {
                                "type": "string",
                                "description": "The task this skill should complete.",
                            }
                        },
                        "required": ["task"],
                    },
                },
            },
        }

    return skills


def _collect_candidate_dirs(root: Path) -> list[Path]:
    candidates: list[Path] = []
    seen: set[Path] = set()

    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue

        if _is_skill_dir(child):
            resolved = child.resolve()
            if resolved not in seen:
                candidates.append(child)
                seen.add(resolved)

        for nested in sorted(child.iterdir()):
            if not nested.is_dir() or nested.name.startswith("."):
                continue
            if _is_skill_dir(nested):
                resolved = nested.resolve()
                if resolved not in seen:
                    candidates.append(nested)
                    seen.add(resolved)

    return candidates


def _is_skill_dir(path: Path) -> bool:
    return (path / SKILL_FILE_NAME).is_file()


def _read_skill_definition(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    normalized = text.replace("\r\n", "\n")
    match = re.match(r"^---\n(.*?)\n---\n?(.*)$", normalized, re.DOTALL)
    if not match:
        return {}, normalized

    frontmatter, body = match.groups()
    return _parse_frontmatter(frontmatter), body


def _parse_frontmatter(frontmatter: str) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    current_key: str | None = None

    for raw_line in frontmatter.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("- ") and current_key:
            metadata.setdefault(current_key, [])
            metadata[current_key].append(_parse_scalar(line[2:].strip()))
            continue

        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        current_key = key.strip()
        parsed_value = value.strip()
        if parsed_value:
            metadata[current_key] = _parse_scalar(parsed_value)
        else:
            metadata[current_key] = []

    return metadata


def _parse_scalar(value: str) -> Any:
    if value.startswith(("'", '"')) and value.endswith(("'", '"')) and len(value) >= 2:
        value = value[1:-1]

    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered.isdigit():
        return int(lowered)
    return value


def _is_enabled(metadata: dict[str, Any]) -> bool:
    enabled = metadata.get("enabled", True)
    return bool(enabled) is True


def _resolve_skill_name(skill_dir: Path, metadata: dict[str, Any]) -> str:
    name = metadata.get("name") or skill_dir.name
    return str(name).strip().replace(" ", "_")


def _resolve_description(
    instructions: str, metadata: dict[str, Any], fallback_name: str
) -> str:
    if metadata.get("description"):
        return str(metadata["description"]).strip()

    for line in instructions.splitlines():
        text = line.strip()
        if not text:
            continue
        if text.startswith("# "):
            return text[2:].strip()
        return text

    return f"Execute the {fallback_name} skill."
