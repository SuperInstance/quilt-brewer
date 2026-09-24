# 🍺 quilt-brewer

> Grow new substrate walkers from recipes. The substrate walker at the recipe layer.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)]()
[![Tests](https://img.shields.io/badge/tests-13/13-brightgreen.svg)](tests/test_brewer.py)
[![Recipes](https://img.shields.io/badge/recipes-4-yellow.svg)](src/quilt_brewer/brewer.py)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

## What is this?

The fleet has 9 substrate walkers. Growing a new one used to take 2-3 hours
of designing the wrapper, writing tests, and demoing. **`quilt-brewer`** makes
this fast: you give it a recipe in plain English, it produces a substrate
walker file that matches the canonical pattern.

The brewer is itself a substrate walker:

```
vibe / cu_substrate / routing / LP / organism / trace / snapshot /
schema / → brewer (this): walks recipes, grows new walkers
```

## What a recipe looks like

```python
BREW_RECIPES["quilt-perception"] = {
    "name": "quilt-perception",
    "substrate_kind": "sensor_stream",
    "description": "Routes sensor data through 6 perception slots",
    "polarity_rules": {
        "ACCEPT": "ok",
        "DRIFT": "warn",
        "REFUSE": "fail",
    },
    "operations": ["ingest", "classify", "route", "summarize"],
    "tests": ["test_ingest", "test_classify", "test_route", ...],
}
```

## Usage

### Brew a substrate from a built-in recipe

```python
from quilt_brewer import run_brew

run_brew("quilt-perception", "/tmp/output")
# ✓ Recipe: quilt-perception
# ✓ Files written: 6
# ✓ Schema compliant: True
# ✓ Tests: 9/9 pass
```

This generates:
- `src/quilt_perception/__init__.py`
- `src/quilt_perception/sensor_stream.py` (the 199 LOC wrapper)
- `tests/test_sensor_stream.py` (130 LOC tests)
- `examples/demo.py` (50 LOC demo)
- `README.md`, `setup.py`

### CLI

```bash
python3 -m quilt_brewer brew quilt-perception /tmp/output
```

## Built-in recipes

| Recipe | Substrate kind | Complexity | Used by |
|---|---|---|---|
| `quilt-perception` | sensor_stream | medium | SYNERGY-6 (Hermes) |
| `quilt-fable` | narrative | high | multi-voice fables |
| `quilt-orchestrator` | dag | high | DAG-based composer |
| `quilt-linker` | graph | medium | substrate-to-substrate linking |

## The pattern (199 LOC + 130 LOC tests + 50 LOC demo)

Every brewed substrate follows this structure:

```python
@dataclass
class {Kind}Receipt:
    """Canonical 8-field witness envelope."""
    witness_id: str
    prev_witness_id: str
    cell_id: str
    substrate: str = "{name}"
    polarity: str = "DRIFT"
    status: str = ""
    timestamp: float = field(default_factory=time.time)
    payload: dict = field(default_factory=dict)


class {Kind}Substrate:
    def step(self, cell_id, payload, status) -> {Kind}Receipt:
        pol = status_to_polarity(status)
        wid = _witness_id(cell_id, payload)
        # ... emit receipt ...

    def chain_intact(self) -> bool: ...
    def reset(self): ...
    def by_polarity(self) -> dict: ...
```

## Schema compliance

Every brewed substrate is automatically registered with
**quilt-schema-registry** as a compliant substrate. This means:

- Its receipts have all 8 canonical fields
- Its witness chain is verifiable
- It composes with the rest of the fleet out of the box

## Why this matters

The substrate walker pattern has been re-derived ~8 times across the fleet.
The brewer codifies the pattern so that:

1. New walkers are guaranteed to comply with the canonical envelope
2. They chain with the rest of the fleet
3. They have tests + demo by default
4. Schema drift is impossible to introduce

A new walker can be grown from a recipe in <30 seconds. The pattern is
**ship-able as code**.

## Related

- [quilt-seed](https://github.com/SuperInstance/quilt-seed) — the substrate
- [quilt-schema-registry](https://github.com/SuperInstance/quilt-schema-registry) — the canonical contract
- [quilt-trace](https://github.com/SuperInstance/quilt-trace) — the visualizer
- [quilt-organism](https://github.com/SuperInstance/quilt-organism) — the walker
- [quilt-fleet-snapshot](https://github.com/SuperInstance/quilt-fleet-snapshot) — fleet state

## License

Apache-2.0
