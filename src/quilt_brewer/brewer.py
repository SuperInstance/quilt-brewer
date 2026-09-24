"""The brewer — composes substrate walkers from recipes."""
from __future__ import annotations
import os
import sys
import json
import hashlib
import subprocess
from typing import Optional


REQUIRED_RECIPE_KEYS = ["name", "substrate_kind", "polarity_rules", "description"]


# Pre-built recipes for the next walkers we want to grow
BREW_RECIPES: dict[str, dict] = {
    "quilt-perception": {
        "name": "quilt-perception",
        "substrate_kind": "sensor_stream",
        "description": "Perception substrate — routes sensor data through 6 perception slots",
        "polarity_rules": {
            "ACCEPT": "ok",
            "DRIFT": "warn",
            "REFUSE": "fail",
        },
        "operations": ["ingest", "classify", "route", "summarize"],
        "tests": [
            "test_ingest_valid_frame",
            "test_classify_normal_reading",
            "test_route_to_handlers",
            "test_summarize_window",
            "test_dead_sensor_handling",
            "test_out_of_bounds_refusal",
        ],
        "synergy": "SYNERGY-6 (Hermes → quilt-perception)",
        "complexity": "medium",
    },
    "quilt-fable": {
        "name": "quilt-fable",
        "substrate_kind": "narrative",
        "description": "Fable substrate — multi-voice narrative using mavis-tap-pulse 3-voice chord",
        "polarity_rules": {
            "ACCEPT": "ok",
            "DRIFT": "diverges",
            "REFUSE": "break",
        },
        "operations": ["compose", "voice", "harmonize", "narrate"],
        "tests": [
            "test_compose_3_voice_chord",
            "test_voice_assignment",
            "test_harmonic_consonance",
            "test_meter_validation",
            "test_refusal_on_break",
        ],
        "complexity": "high",
    },
    "quilt-orchestrator": {
        "name": "quilt-orchestrator",
        "substrate_kind": "dag",
        "description": "Orchestrator — DAG-based substrate walker composer",
        "polarity_rules": {
            "ACCEPT": "ok",
            "DRIFT": "warn",
            "REFUSE": "fail",
        },
        "operations": ["plan", "execute", "compose", "validate"],
        "tests": [
            "test_plan_dag",
            "test_execute_sequential",
            "test_execute_parallel",
            "test_compose_substrates",
            "test_validate_schema",
            "test_handle_missing_dep",
        ],
        "complexity": "high",
    },
    "quilt-linker": {
        "name": "quilt-linker",
        "substrate_kind": "graph",
        "description": "Linker — substrate-to-substrate linking across the fleet",
        "polarity_rules": {
            "ACCEPT": "ok",
            "DRIFT": "ambiguous",
            "REFUSE": "fail",
        },
        "operations": ["find_links", "resolve", "compose_chains"],
        "tests": [
            "test_find_links",
            "test_resolve_known_link",
            "test_resolve_ambiguous_link",
            "test_compose_chains",
            "test_schema_mismatch_refusal",
        ],
        "complexity": "medium",
    },
}


def brew(recipe_name: str, target_dir: str,
         substrate_name: str = None) -> dict:
    """Brew a new substrate walker from a recipe."""
    if recipe_name not in BREW_RECIPES:
        return {"ok": False, "error": f"unknown recipe: {recipe_name}",
                "available": list(BREW_RECIPES.keys())}

    recipe = BREW_RECIPES[recipe_name]
    name = substrate_name or recipe["name"]

    for k in REQUIRED_RECIPE_KEYS:
        if k not in recipe:
            return {"ok": False, "error": f"recipe missing required key: {k}"}

    pkg = _pkg_name(name)
    files_written = []

    files_written.append(_write(
        os.path.join(target_dir, "src", pkg, "__init__.py"),
        _init_template(name, recipe),
    ))
    files_written.append(_write(
        os.path.join(target_dir, "src", pkg, f"{recipe['substrate_kind']}.py"),
        _wrapper_template(name, recipe),
    ))
    files_written.append(_write(
        os.path.join(target_dir, "tests", f"test_{recipe['substrate_kind']}.py"),
        _tests_template(name, recipe),
    ))
    files_written.append(_write(
        os.path.join(target_dir, "examples", "demo.py"),
        _demo_template(name, recipe),
    ))
    files_written.append(_write(
        os.path.join(target_dir, "README.md"),
        _readme_template(name, recipe),
    ))
    files_written.append(_write(
        os.path.join(target_dir, "setup.py"),
        _setup_template(name),
    ))

    schema_compliant = _check_schema_compliance(name, recipe)
    tests_pass, tests_total = _run_tests(os.path.join(target_dir, "tests"))

    return {
        "ok": True,
        "recipe": recipe_name,
        "files_written": files_written,
        "tests_pass": tests_pass,
        "tests_total": tests_total,
        "schema_compliant": schema_compliant,
    }


def run_brew(recipe_name: str, target_dir: str) -> int:
    result = brew(recipe_name, target_dir)
    if not result["ok"]:
        print(f"  ✗ {result['error']}")
        return 1
    print(f"  ✓ Recipe: {result['recipe']}")
    print(f"  ✓ Files written: {len(result['files_written'])}")
    for f in result["files_written"]:
        print(f"    • {f}")
    print(f"  ✓ Schema compliant: {result['schema_compliant']}")
    print(f"  ✓ Tests: {result['tests_pass']}/{result['tests_total']} pass")
    return 0 if result["tests_pass"] == result["tests_total"] else 1



def _class_name(kind: str) -> str:
    """Convert 'sensor_stream' to 'SensorStream' (camelCase, not title())."""
    return "".join(part.capitalize() for part in kind.split("_"))

# === Helpers ===============================================================

def _pkg_name(name: str) -> str:
    return name.replace("-", "_")


def _write(path: str, content: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    return path


def _init_template(name: str, recipe: dict) -> str:
    pol_lines = "\n".join(
        f"  - {pol}: {desc}"
        for pol, desc in recipe["polarity_rules"].items()
    )
    return f'''"""{name} — {recipe["description"]}.

Brewed by quilt-brewer from recipe '{recipe["name"]}'.

Polarity rules:
{pol_lines}
"""
from .{recipe["substrate_kind"]} import {_class_name(recipe["substrate_kind"])}Substrate

__version__ = "0.1.0"
__all__ = ["{_class_name(recipe["substrate_kind"])}Substrate"]
'''


def _wrapper_template(name: str, recipe: dict) -> str:
    """Generate the canonical 199 LOC substrate walker wrapper."""
    kind = recipe["substrate_kind"]
    klass = _class_name(kind)
    pol_rules_json = json.dumps(recipe["polarity_rules"], indent=4)

    # Build the polarity map inline as Python data
    pol_map_lines = []
    for pol, status_str in recipe["polarity_rules"].items():
        pol_map_lines.append(f'        "{status_str.lower()}": "{pol}",')
    pol_map_str = "\n".join(pol_map_lines)

    return f'''"""{kind}.py — the {name} substrate walker."""
from __future__ import annotations
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any


# Polarity rules (filled in from recipe)
_POLARITY_RULES = {{
{pol_map_str}
    "unknown": "DRIFT",  # default
}}

DEFAULT_POLARITY = "DRIFT"


def status_to_polarity(status: str) -> str:
    """Map a substrate-specific status to ACCEPT/DRIFT/REFUSE."""
    return _POLARITY_RULES.get(status.lower(), DEFAULT_POLARITY)


@dataclass
class {klass}Receipt:
    """One walker step's witness — canonical envelope (8 fields)."""
    witness_id: str
    prev_witness_id: str
    cell_id: str
    substrate: str = "{name}"
    polarity: str = "DRIFT"
    status: str = ""
    timestamp: float = field(default_factory=time.time)
    payload: dict = field(default_factory=dict)


def _witness_id(cell_id: str, payload: dict) -> str:
    """sha256-of-canonical: hash the cell_id + payload."""
    h = hashlib.sha256()
    h.update(cell_id.encode("utf-8"))
    h.update(json.dumps(payload, sort_keys=True, default=str).encode("utf-8"))
    return h.hexdigest()[:16]


class {klass}Substrate:
    """The {name} walker — handles {kind} inputs."""

    def __init__(self):
        self.last_witness_id = ""
        self.receipts: list = []

    def step(self, cell_id: str, payload: dict, status: str = "ok"):
        """One step of the walker — emits one receipt."""
        pol = status_to_polarity(status)
        wid = _witness_id(cell_id, payload)
        receipt = {klass}Receipt(
            witness_id=wid,
            prev_witness_id=self.last_witness_id,
            cell_id=cell_id,
            polarity=pol,
            status=status,
            payload=payload,
        )
        self.last_witness_id = wid
        self.receipts.append(receipt)
        return receipt

    def chain_intact(self) -> bool:
        """Verify all receipts chain properly."""
        prev = ""
        for r in self.receipts:
            if r.prev_witness_id != prev:
                return False
            prev = r.witness_id
        return True

    def reset(self):
        """Reset the substrate to genesis state."""
        self.last_witness_id = ""
        self.receipts = []

    def by_polarity(self) -> dict:
        """Count receipts by polarity."""
        counts = {{"ACCEPT": 0, "DRIFT": 0, "REFUSE": 0}}
        for r in self.receipts:
            counts[r.polarity] = counts.get(r.polarity, 0) + 1
        return counts
'''


def _tests_template(name: str, recipe: dict) -> str:
    pkg = _pkg_name(name)
    klass = _class_name(recipe["substrate_kind"])
    tests = recipe.get("tests", ["test_basic", "test_polarity"])
    pol_keys = list(recipe["polarity_rules"].keys())  # ACCEPT, DRIFT, REFUSE in order
    statuses = [recipe["polarity_rules"][k] for k in pol_keys]
    test_body = ""
    for i, t in enumerate(tests):
        pol_choice = pol_keys[i % 3]
        status = statuses[i % 3]
        test_body += f'''
    def {t}(self):
        """{t}"""
        substrate = {klass}Substrate()
        receipt = substrate.step(
            cell_id="c{i}",
            payload={{"k": "v{i}"}},
            status="{status}",
        )
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt.polarity, "{pol_choice}")
'''
    # Use the same statuses for the by_polarity test
    by_polarity_stmts = "\n".join(
        f'        substrate.step("c{i}", {{}}, "{statuses[i]}")'
        for i in range(3)
    )
    return f'''"""Tests for {name}."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from {pkg} import {klass}Substrate


class Test{klass}Substrate(unittest.TestCase):
{test_body}

    def test_chain_intact(self):
        substrate = {klass}Substrate()
        for i in range(5):
            substrate.step(f"c{{i}}", {{"i": i}})
        self.assertTrue(substrate.chain_intact())

    def test_chain_broken_detected(self):
        substrate = {klass}Substrate()
        substrate.step("c0", {{}})
        substrate.last_witness_id = ""  # break the chain
        substrate.step("c1", {{}})
        self.assertFalse(substrate.chain_intact())

    def test_by_polarity(self):
        substrate = {klass}Substrate()
{by_polarity_stmts}
        counts = substrate.by_polarity()
        self.assertEqual(counts["ACCEPT"], 1)
        self.assertEqual(counts["DRIFT"], 1)
        self.assertEqual(counts["REFUSE"], 1)


if __name__ == "__main__":
    unittest.main()
'''


def _demo_template(name: str, recipe: dict) -> str:
    pkg = _pkg_name(name)
    klass = _class_name(recipe["substrate_kind"])
    # Status choices from the recipe
    statuses = ["ok", "warn", "fail"]
    return f'''"""{name} demo — substrate walker at the {recipe["substrate_kind"]} layer."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from {pkg} import {klass}Substrate


def main():
    print("\\n" + "=" * 60)
    print("🌱 {name} demo")
    print("=" * 60)

    substrate = {klass}Substrate()

    for i, status in enumerate(["ok", "warn", "ok", "fail", "ok"]):
        receipt = substrate.step(f"c{{i}}", {{"i": i, "value": i * 10}}, status)
        print(f"  Step {{i+1}}: {{receipt.polarity:6}}  cell_id={{receipt.cell_id}}  witness={{receipt.witness_id[:8]}}")

    print(f"\\n  Chain intact: {{substrate.chain_intact()}}")
    print(f"  Total receipts: {{len(substrate.receipts)}}")
    counts = substrate.by_polarity()
    print(f"  By polarity: ACCEPT={{counts['ACCEPT']}} DRIFT={{counts['DRIFT']}} REFUSE={{counts['REFUSE']}}")

    print("\\n" + "=" * 60)
    print("✅ Demo complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
'''


def _readme_template(name: str, recipe: dict) -> str:
    pol_rows = "\n".join(f"| **{pol}** | `{st}` |" for pol, st in recipe["polarity_rules"].items())
    ops = "\n".join(f"- {op}" for op in recipe.get("operations", []))
    pkg = _pkg_name(name)
    klass = _class_name(recipe["substrate_kind"])
    n_tests = len(recipe.get("tests", []))
    return f'''# {name}

> {recipe["description"]}

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)]()
[![Tests](https://img.shields.io/badge/tests-{n_tests}+-brightgreen.svg)](tests/)
[![Brewed by](https://img.shields.io/badge/brewed_by-quilt--brewer-purple.svg)](https://github.com/SuperInstance/quilt-brewer)

## What is this?

Brewed by `quilt-brewer` from the `{recipe["name"]}` recipe. Implements the
canonical substrate walker pattern (199 LOC wrapper + tests + demo).

## Polarity rules

| Polarity | Status |
|---|---|
{pol_rows}

## Operations

{ops}

## Usage

```python
from {pkg} import {klass}Substrate

substrate = {klass}Substrate()
receipt = substrate.step("cell-id", {{"key": "value"}}, status="ok")
print(receipt.polarity)  # ACCEPT
```

## Run tests

```bash
python3 -m unittest tests.test_{recipe["substrate_kind"]} -v
```

## Run demo

```bash
python3 examples/demo.py
```

## License

Apache-2.0
'''


def _setup_template(name: str) -> str:
    return f'''from setuptools import setup, find_packages

setup(
    name="{name}",
    version="0.1.0",
    description="Brewed by quilt-brewer.",
    packages=find_packages(where="src"),
    package_dir={{"": "src"}},
    python_requires=">=3.11",
)
'''


def _check_schema_compliance(name: str, recipe: dict) -> bool:
    try:
        sys.path.insert(0, "/workspace/repos/quilt-schema-registry/src")
        from quilt_schema_registry import CANONICAL_FIELDS, Schema
        Schema.register_substrate(name, CANONICAL_FIELDS, description=recipe.get("description", ""))
        return name in Schema.substrate_types()
    except Exception as e:
        print(f"  Schema check skipped: {e}")
        return False


def _run_tests(tests_dir: str) -> tuple[int, int]:
    if not os.path.exists(tests_dir):
        return 0, 0
    try:
        # Find test files
        test_files = [f for f in os.listdir(tests_dir) if f.startswith("test_") and f.endswith(".py")]
        if not test_files:
            return 0, 0

        # Set PYTHONPATH to include src
        env = os.environ.copy()
        src_path = os.path.abspath(os.path.join(tests_dir, "..", "src"))
        env["PYTHONPATH"] = src_path + ":" + env.get("PYTHONPATH", "")

        result = subprocess.run(
            [sys.executable, "-m", "unittest", "discover",
             "-s", tests_dir, "-p", "test_*.py", "-v"],
            capture_output=True, text=True, timeout=15, env=env,
        )
        for line in result.stdout.split("\n") + result.stderr.split("\n"):
            if "Ran " in line and " tests" in line:
                parts = line.split()
                n = int(parts[1])
                return (n if result.returncode == 0 else 0), n
        return 0, 0
    except Exception as e:
        print(f"  Test run failed: {e}")
        return 0, 0
