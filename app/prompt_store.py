from __future__ import annotations

"""Prompt store — loads YAML templates and renders using Jinja2."""

from pathlib import Path
from threading import Lock
from typing import Dict, List

import yaml
from jinja2 import Environment, BaseLoader, TemplateError

from mcp_observability.schemas import Prompt

_BASE_DIR = Path(__file__).resolve().parent
_PROMPT_DIR = _BASE_DIR / "prompts"

_cache: Dict[str, Prompt] | None = None
_lock = Lock()


def _load_prompts() -> Dict[str, Prompt]:
    prompts: Dict[str, Prompt] = {}

    if not _PROMPT_DIR.exists():
        return prompts

    for path in _PROMPT_DIR.glob("*.yaml"):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        try:
            prompt = Prompt(**data)
            prompts[prompt.id] = prompt
        except Exception as exc:  # pragma: no cover
            # Skip invalid prompt definitions but log for debugging
            print(f"Failed loading prompt {path.name}: {exc}")
    return prompts


def _ensure_loaded() -> Dict[str, Prompt]:
    global _cache
    if _cache is None:
        with _lock:
            if _cache is None:
                _cache = _load_prompts()
    return _cache


def list_prompts() -> List[Prompt]:
    return list(_ensure_loaded().values())


def get_prompt(prompt_id: str) -> Prompt | None:
    return _ensure_loaded().get(prompt_id)


def render_prompt(prompt: Prompt, args: Dict[str, str]) -> str:
    # Ensure required variables provided
    missing = [v for v in prompt.input_variables if v not in args]
    if missing:
        raise ValueError(f"Missing variables: {', '.join(missing)}")

    env = Environment(loader=BaseLoader, autoescape=False)
    try:
        template = env.from_string(prompt.template)
        return template.render(**args)
    except TemplateError as exc:
        raise ValueError(f"Template render error: {exc}") from exc 