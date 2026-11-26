"""Places development tools keep rebuildable data, with each tool's own clean-up command to run yourself.

A tool's folder is recognised by the end of its path in the scanned tree, the way clean-up rules are. The size is
the recorded one. FileTree never runs these commands: they ask, skip what is in use and keep their own books,
which deleting the folders behind a tool's back does not.
"""

from __future__ import annotations

import fnmatch
import threading
from dataclasses import dataclass, field

from je_file_tree.core.node import Node
from je_file_tree.core.pacing import give_way


@dataclass(frozen=True, slots=True)
class Tool:
    """One tool's store: where it lies, the command that shows what it holds and the one that cleans it.

    ``clean`` is empty for tools that expire their caches by themselves and have no command for it.
    """

    key: str
    name: str
    folders: tuple[str, ...]
    inspect: str
    clean: str


@dataclass(slots=True)
class ToolUse:
    """What a tool's stores take in the scan."""

    tool: Tool
    nodes: list[Node] = field(default_factory=list)
    size: int = 0
    allocated: int = 0
    incomplete: bool = False


TOOLS: tuple[Tool, ...] = (
    Tool("docker", "Docker", ("Docker/wsl", "AppData/Local/Docker", "/var/lib/docker",
                              "Library/Containers/com.docker.docker"), "docker system df", "docker system prune"),
    Tool("podman", "Podman", (".local/share/containers/storage",), "podman system df", "podman system prune"),
    Tool("pip", "pip", ("AppData/Local/pip/Cache", ".cache/pip", "Library/Caches/pip"), "pip cache info",
         "pip cache purge"),
    Tool("uv", "uv", ("AppData/Local/uv/cache", ".cache/uv"), "uv cache dir", "uv cache prune"),
    Tool("conda", "conda", ("anaconda3/pkgs", "miniconda3/pkgs", "miniforge3/pkgs"), "conda clean --all --dry-run",
         "conda clean --all"),
    Tool("npm", "npm", ("AppData/Local/npm-cache", "AppData/Roaming/npm-cache", ".npm"), "npm cache verify",
         "npm cache clean --force"),
    Tool("yarn", "Yarn", ("AppData/Local/Yarn/Cache", ".cache/yarn", "Library/Caches/Yarn"), "yarn cache dir",
         "yarn cache clean"),
    Tool("pnpm", "pnpm", ("AppData/Local/pnpm/store", ".local/share/pnpm/store", "Library/pnpm/store"),
         "pnpm store path", "pnpm store prune"),
    Tool("cargo", "Cargo", (".cargo/registry", ".cargo/git"), "cargo --version", ""),
    Tool("rustup", "rustup", (".rustup/toolchains",), "rustup toolchain list", "rustup toolchain uninstall <name>"),
    Tool("go", "Go", ("go/pkg/mod", "AppData/Local/go-build", ".cache/go-build", "Library/Caches/go-build"),
         "go env GOMODCACHE GOCACHE", "go clean -cache -modcache"),
    Tool("gradle", "Gradle", (".gradle/caches",), "gradle --status", ""),
    Tool("maven", "Maven", (".m2/repository",), "mvn help:effective-settings",
         "mvn dependency:purge-local-repository"),
    Tool("nuget", "NuGet", (".nuget/packages", "AppData/Local/NuGet/v3-cache"), "dotnet nuget locals all --list",
         "dotnet nuget locals all --clear"),
    Tool("homebrew", "Homebrew", ("Library/Caches/Homebrew", ".cache/Homebrew"), "brew cleanup --dry-run",
         "brew cleanup"),
    Tool("xcode", "Xcode", ("Library/Developer/Xcode/DerivedData", "Library/Developer/CoreSimulator"),
         "xcrun simctl list devices", "xcrun simctl delete unavailable"),
    Tool("huggingface", "Hugging Face", (".cache/huggingface",), "hf cache ls", "hf cache prune"),
    Tool("ollama", "Ollama", (".ollama/models",), "ollama list", "ollama rm <model>"),
)


def dev_tools(root: Node, *, tools: tuple[Tool, ...] = TOOLS,
              cancel: threading.Event | None = None) -> list[ToolUse] | None:
    """What each recognised tool's stores take beneath ``root``, the largest first; None once cancelled."""
    patterns: dict[str, list[tuple[tuple[str, ...], bool, Tool]]] = {}
    for tool in tools:
        for folder in tool.folders:
            parts = tuple(part.casefold() for part in folder.strip("/").split("/"))
            patterns.setdefault(parts[-1], []).append((parts, folder.startswith("/"), tool))
    found: dict[str, ToolUse] = {}
    sources = [(child, _parts(child.path)) for child in root.children if child.is_dir and not child.is_link] \
        if root.path is None else [(root, _parts(root.path))]
    stack = sources
    while stack:
        if cancel is not None and cancel.is_set():
            return None
        give_way()
        folder, above = stack.pop()
        tool = _tool_at(above, patterns)
        if tool is not None:
            _count(found.setdefault(tool.key, ToolUse(tool)), folder)
            continue  # a store inside a store belongs to the outer one
        for child in folder.children:
            if child.is_dir and not child.is_link:
                stack.append((child, (*above, child.name.casefold())))
    return sorted(found.values(), key=lambda use: (-use.allocated, use.tool.name))


def _tool_at(parts: tuple[str, ...], patterns: dict[str, list[tuple[tuple[str, ...], bool, Tool]]]) -> Tool | None:
    for pattern, anchored, tool in patterns.get(parts[-1], ()) if parts else ():
        start = len(parts) - len(pattern)
        if start < 0 or (anchored and start != 0):
            continue
        if all(fnmatch.fnmatchcase(part, wanted) for part, wanted in zip(parts[start:], pattern, strict=True)):
            return tool
    return None


def _parts(path: str | None) -> tuple[str, ...]:
    return tuple(part.casefold() for part in (path or "").replace("\\", "/").split("/") if part)


def _count(use: ToolUse, node: Node) -> None:
    use.nodes.append(node)
    use.size += node.size
    use.allocated += node.allocated
    use.incomplete |= bool(node.error)
