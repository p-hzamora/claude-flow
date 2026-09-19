#!/usr/bin/env python3
"""Validate the shared Claude Code/Codex plugin layout."""

from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
PLUGIN_ROOT = ROOT / "plugins"
CLAUDE_MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
CODEX_MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
CODEX_AGENTS = ROOT / ".codex" / "agents"
CODEX_INSTRUCTIONS = ROOT / "AGENTS.md"
ROUTING_PHRASES_PATTERN = re.compile(r" Routing phrases: (?P<phrases>[^.]+)\.$")
CLAUDE_ROUTING_PHRASES_PATTERN = re.compile(
    r'^description:\s*"?Routing phrases: (?P<phrases>[^.]+)\.', re.MULTILINE
)


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"{path}: invalid JSON ({error})") from error
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def required_string(data: dict[str, Any], key: str, path: Path) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{path}: '{key}' must be a non-empty string")
    return value


def validate_plugin(plugin_dir: Path) -> tuple[str, str]:
    claude_path = plugin_dir / ".claude-plugin" / "plugin.json"
    codex_path = plugin_dir / ".codex-plugin" / "plugin.json"
    claude = load_json(claude_path)
    codex = load_json(codex_path)

    name = required_string(claude, "name", claude_path)
    version = required_string(claude, "version", claude_path)
    if required_string(codex, "name", codex_path) != name:
        raise ValueError(f"{plugin_dir}: Claude and Codex plugin names differ")
    if required_string(codex, "version", codex_path) != version:
        raise ValueError(f"{plugin_dir}: Claude and Codex versions differ")
    required_string(claude, "description", claude_path)
    required_string(codex, "description", codex_path)

    skills_path = codex.get("skills")
    if skills_path != "./skills/":
        raise ValueError(f"{codex_path}: expected skills to be './skills/'")
    skills_dir = plugin_dir / "skills"
    if not skills_dir.is_dir():
        raise ValueError(f"{plugin_dir}: Codex skills directory is missing")
    for skill_dir in sorted(path for path in skills_dir.iterdir() if path.is_dir()):
        if not (skill_dir / "SKILL.md").is_file():
            raise ValueError(f"{skill_dir}: missing SKILL.md")

    return name, version


def claude_agent_names() -> set[str]:
    names: set[str] = set()
    for agent_path in PLUGIN_ROOT.glob("*/agents/*.md"):
        text = agent_path.read_text()
        match = re.search(r"^name:\s*[\"']?([^\"'\n]+)", text, re.MULTILINE)
        if match is None:
            raise ValueError(f"{agent_path}: missing agent name in frontmatter")
        names.add(match.group(1).strip())
    return names


def claude_agent_routing_phrases() -> dict[str, set[str]]:
    """Return the routing phrases at the start of each Claude description."""
    agents: dict[str, set[str]] = {}
    phrases_by_owner: dict[str, Path] = {}
    for agent_path in PLUGIN_ROOT.glob("*/agents/*.md"):
        text = agent_path.read_text()
        name_match = re.search(r"^name:\s*[\"']?([^\"'\n]+)", text, re.MULTILINE)
        routing_match = CLAUDE_ROUTING_PHRASES_PATTERN.search(text)
        if name_match is None or routing_match is None:
            raise ValueError(
                f"{agent_path}: missing name or routing phrases in description"
            )
        name = name_match.group(1).strip()
        raw_phrases = routing_match["phrases"].split(";")
        phrases = {phrase.strip().casefold() for phrase in raw_phrases}
        if len(phrases) != len(raw_phrases) or len(phrases) < 2 or not all(phrases):
            raise ValueError(
                f"{agent_path}: routing phrases must be unique non-empty strings"
            )
        if name in agents:
            raise ValueError(f"{agent_path}: duplicate Claude agent name '{name}'")
        for phrase in phrases:
            if owner := phrases_by_owner.get(phrase):
                raise ValueError(
                    f"{agent_path}: routing phrase '{phrase}' is already owned by {owner}"
                )
            phrases_by_owner[phrase] = agent_path
        agents[name] = phrases
    return agents


def validate_codex_agents(expected_names: set[str]) -> dict[str, set[str]]:
    if not CODEX_INSTRUCTIONS.is_file() or not CODEX_INSTRUCTIONS.read_text().strip():
        raise ValueError("AGENTS.md: missing or empty Codex project instructions")
    if not CODEX_AGENTS.is_dir():
        raise ValueError(f"{CODEX_AGENTS}: Codex agent directory is missing")

    actual_names: set[str] = set()
    routing_phrases: dict[str, Path] = {}
    phrases_by_agent: dict[str, set[str]] = {}
    skill_names = {
        skill_dir.name
        for plugin_dir in PLUGIN_ROOT.iterdir()
        if plugin_dir.is_dir()
        for skill_dir in (plugin_dir / "skills").glob("*")
        if skill_dir.is_dir() and (skill_dir / "SKILL.md").is_file()
    }
    for agent_path in CODEX_AGENTS.glob("*.toml"):
        try:
            agent = tomllib.loads(agent_path.read_text())
        except (OSError, tomllib.TOMLDecodeError) as error:
            raise ValueError(f"{agent_path}: invalid TOML ({error})") from error
        name = required_string(agent, "name", agent_path)
        description = required_string(agent, "description", agent_path)
        instructions = required_string(agent, "developer_instructions", agent_path)
        if name in actual_names:
            raise ValueError(f"{agent_path}: duplicate Codex agent name '{name}'")
        actual_names.add(name)
        if not description or not instructions:
            raise ValueError(f"{agent_path}: missing required Codex agent text")
        routing_match = ROUTING_PHRASES_PATTERN.search(description)
        if routing_match is None:
            raise ValueError(
                f"{agent_path}: description must end with unique 'Routing phrases: ...'"
            )
        phrases = [
            phrase.strip().casefold() for phrase in routing_match["phrases"].split(";")
        ]
        if len(phrases) < 2 or any(not phrase for phrase in phrases):
            raise ValueError(
                f"{agent_path}: define at least two non-empty routing phrases"
            )
        if len(set(phrases)) != len(phrases):
            raise ValueError(f"{agent_path}: repeats one of its routing phrases")
        for phrase in phrases:
            if owner := routing_phrases.get(phrase):
                raise ValueError(
                    f"{agent_path}: routing phrase '{phrase}' is already owned by {owner}"
                )
            routing_phrases[phrase] = agent_path
        phrases_by_agent[name] = set(phrases)
        for skill_name in re.findall(r"\$([a-z0-9][a-z0-9-]*)", instructions):
            if skill_name not in skill_names:
                raise ValueError(
                    f"{agent_path}: references unknown shared skill '{skill_name}'"
                )

    if actual_names != expected_names:
        missing = sorted(expected_names - actual_names)
        extra = sorted(actual_names - expected_names)
        raise ValueError(
            "Claude/Codex agent profiles differ"
            f" (missing Codex: {missing or 'none'}; extra Codex: {extra or 'none'})"
        )
    return phrases_by_agent


def validate_codex_marketplace(expected_plugins: set[str]) -> None:
    marketplace = load_json(CODEX_MARKETPLACE)
    if required_string(marketplace, "name", CODEX_MARKETPLACE) != "claude-flow":
        raise ValueError(
            f"{CODEX_MARKETPLACE}: expected marketplace name 'claude-flow'"
        )
    interface = marketplace.get("interface")
    if not isinstance(interface, dict) or not isinstance(
        interface.get("displayName"), str
    ):
        raise ValueError(f"{CODEX_MARKETPLACE}: missing interface.displayName")

    entries = marketplace.get("plugins")
    if not isinstance(entries, list):
        raise ValueError(f"{CODEX_MARKETPLACE}: 'plugins' must be an array")
    actual_plugins: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError(f"{CODEX_MARKETPLACE}: plugin entry must be an object")
        name = required_string(entry, "name", CODEX_MARKETPLACE)
        if name in actual_plugins:
            raise ValueError(f"{CODEX_MARKETPLACE}: duplicate plugin '{name}'")
        actual_plugins.add(name)
        source = entry.get("source")
        if not isinstance(source, dict) or source != {
            "source": "local",
            "path": f"./plugins/{name}",
        }:
            raise ValueError(f"{CODEX_MARKETPLACE}: invalid source for '{name}'")
        policy = entry.get("policy")
        if not isinstance(policy, dict) or policy.get("installation") != "AVAILABLE":
            raise ValueError(f"{CODEX_MARKETPLACE}: '{name}' must be AVAILABLE")
        if policy.get("authentication") not in {"ON_INSTALL", "ON_USE"}:
            raise ValueError(
                f"{CODEX_MARKETPLACE}: invalid authentication policy for '{name}'"
            )
        required_string(entry, "category", CODEX_MARKETPLACE)
    if actual_plugins != expected_plugins:
        raise ValueError("Codex marketplace and plugin folders differ")


def main() -> int:
    try:
        marketplace = load_json(CLAUDE_MARKETPLACE)
        marketplace_plugins = {
            entry["name"]: entry
            for entry in marketplace.get("plugins", [])
            if isinstance(entry, dict) and isinstance(entry.get("name"), str)
        }
        plugin_versions = {
            name: version
            for plugin_dir in sorted(
                path for path in PLUGIN_ROOT.iterdir() if path.is_dir()
            )
            for name, version in [validate_plugin(plugin_dir)]
        }
        validate_codex_marketplace(set(plugin_versions))
        claude_names = claude_agent_names()
        codex_routing_phrases = validate_codex_agents(claude_names)
        claude_routing_phrases = claude_agent_routing_phrases()
        if codex_routing_phrases != claude_routing_phrases:
            raise ValueError("Claude and Codex agent routing phrases differ")
        if set(plugin_versions) != set(marketplace_plugins):
            raise ValueError("plugin folders and Claude marketplace entries differ")
        for name, version in plugin_versions.items():
            if marketplace_plugins[name].get("version") != version:
                raise ValueError(f"{name}: marketplace and manifest versions differ")
            expected_source = f"./plugins/{name}"
            if marketplace_plugins[name].get("source") != expected_source:
                raise ValueError(
                    f"{name}: marketplace source must be '{expected_source}'"
                )
    except (OSError, TypeError, ValueError, KeyError) as error:
        print(f"multihost validation failed: {error}", file=sys.stderr)
        return 1

    print(
        "multihost validation passed "
        f"({len(plugin_versions)} plugins, {len(claude_names)} agent profiles)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
