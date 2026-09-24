"""quilt-brewer demo — grow 4 substrate walkers from recipes."""
import os
import sys
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from quilt_brewer import BREW_RECIPES, brew


def main():
    print("\n" + "=" * 60)
    print("🍺 quilt-brewer demo — grow 4 walkers from recipes")
    print("=" * 60)

    print(f"\n[Recipes available]")
    for name, recipe in BREW_RECIPES.items():
        print(f"  • {name}: {recipe['description'][:60]}...")

    with tempfile.TemporaryDirectory() as dest:
        for recipe_name in BREW_RECIPES:
            print(f"\n[Brewing: {recipe_name}]")
            result = brew(recipe_name, dest + "/" + recipe_name)
            print(f"  Files written: {len(result['files_written'])}")
            print(f"  Tests: {result['tests_pass']}/{result['tests_total']}")
            print(f"  Schema compliant: {result['schema_compliant']}")

    print("\n" + "=" * 60)
    print("✅ Demo complete: 4 substrate walkers grown from recipes")
    print("=" * 60)


if __name__ == "__main__":
    main()
