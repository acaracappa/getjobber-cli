"""Guards against runtime dependencies that only resolve via dev extras.

1.2.0 shipped importing `click` without declaring it. It was present in
development only because `black` requires it, so tests, CI and a local
`pip install -e ".[dev]"` all passed while the published wheel had no
commands at all.
"""

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "getjobber_cli"
PYPROJECT = ROOT / "pyproject.toml"

STDLIB = set(sys.stdlib_module_names)
FIRST_PARTY = {"getjobber_cli"}


def declared_runtime_requirements():
    text = PYPROJECT.read_text()
    block = re.search(r"^dependencies = \[(.*?)^\]", text, re.MULTILINE | re.DOTALL)
    assert block, "could not find [project] dependencies"
    names = re.findall(r'"\s*([A-Za-z0-9._-]+)', block.group(1))
    return {n.lower().replace("_", "-") for n in names}


def imported_top_level_modules():
    found = set()
    for path in SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                found.add(node.module.split(".")[0])
    return found


# Distributions whose import name differs from the package name.
IMPORT_TO_DIST = {
    "yaml": "pyyaml",
    "requests_oauthlib": "requests-oauthlib",
    "requests_toolbelt": "requests-toolbelt",
    "typing_extensions": "typing-extensions",
    "gql": "gql",
}


def test_every_third_party_import_is_declared():
    declared = declared_runtime_requirements()
    missing = []
    for module in sorted(imported_top_level_modules()):
        if module in STDLIB or module in FIRST_PARTY or module.startswith("_"):
            continue
        dist = IMPORT_TO_DIST.get(module, module.lower().replace("_", "-"))
        if dist not in declared:
            missing.append(f"{module} (expected dependency '{dist}')")
    assert (
        not missing
    ), "source imports packages that are not declared runtime dependencies: " + ", ".join(missing)


def test_click_specifically_is_declared():
    """Typer >= 0.26 does not depend on click; we import it directly."""
    assert "click" in declared_runtime_requirements()
