"""quilt-brewer — grow new substrate walkers from recipes.

The fleet has 9 walkers. Growing a new one used to take 2-3 hours of
designing the wrapper, writing tests, and demoing. The brewer makes this
fast: you give it a recipe in plain English, it produces a substrate
walker file that matches the canonical pattern.

A recipe has:
  - name: the substrate's canonical name
  - substrate_kind: what kind of substrate it walks (corpus, problem, fleet, ...)
  - receipts_field: what each receipt looks like (the 8-field envelope)
  - witnesses_strategy: how to compute witness_id (sha256-of-canonical, etc)
  - polarity_rules: how to determine ACCEPT/DRIFT/REFUSE
  - description: human-readable what & why

The brewer:
  1. Composes the canonical 199 LOC wrapper + 130 LOC tests + 50 LOC demo
  2. Validates the output against quilt-schema-registry
  3. Writes to the target path
  4. Runs the tests
  5. Reports

Substrate walker pattern at the 6th layer:
  vibe / cu_substrate / routing / LP / organism / trace / snapshot /
  schema / → brewer (this): walks recipes, grows new walkers
"""
from .brewer import brew, BREW_RECIPES, run_brew

__version__ = "0.1.0"
__all__ = ["brew", "BREW_RECIPES", "run_brew"]
