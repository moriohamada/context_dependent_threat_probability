"""Run the sandbagging experiment."""

import argparse
from pathlib import Path
from inspect_ai import eval

from task import sandbagging_eval
from roles import PROBABILITIES, ROLES
from dotenv import load_dotenv
load_dotenv(".env")


def build_conditions(run_counterfactual: bool) -> list[tuple[str, int]]:
    """Build list of (condition, probability) pairs."""
    conditions = [("sandbag", p) for p in PROBABILITIES]
    if run_counterfactual:
        middle_idx = (len(PROBABILITIES) - 1) // 2
        conditions.insert(0, ("counterfactual", PROBABILITIES[middle_idx]))
    return conditions


def get_existing_files(log_dir: Path, conditions: list, n_repeats: int,
                       rep_offset: int = 0) -> list[Path]:
    """Check for existing log files."""
    existing = []
    for rep in range(n_repeats):
        for cond, prob in conditions:
            name = f"{cond}_{prob}pct_{rep + rep_offset}"
            path = log_dir / f"{name}.eval"
            if path.exists():
                existing.append(path)
    return existing


def run_all_conditions(model: str, roles: list[str], n_questions: int = 10,
                       n_repeats: int = 1, seed: int = 0,
                       run_counterfactual: bool = True, rep_offset: int = 0):

    model_name = model.split("/")[-1]
    conditions = build_conditions(run_counterfactual)

    for role in roles:
        print(f"\nROLE: {role}")

        log_dir = Path(f"./logs/{model_name}/{role}")
        log_dir.mkdir(parents=True, exist_ok=True)

        # Check for existing files
        existing = get_existing_files(log_dir, conditions, n_repeats, rep_offset)
        if existing and rep_offset == 0:
            print(f"Found {len(existing)} existing log files in {log_dir}")
            print("Options:")
            print("  [o] Overwrite existing files")
            print("  [N] Add offset to rep numbers (enter a number)")
            print("  [s] Skip this role")
            choice = input("Choice: ").strip()

            if choice.lower() == 'o':
                print("Overwriting existing files...")
            elif choice.isdigit():
                rep_offset = int(choice)
                print(f"Using rep offset of {rep_offset}")
            elif choice.lower() == 's':
                print(f"Skipping {role}")
                continue
            else:
                print("Cancelled.")
                return

        for rep in range(n_repeats):
            actual_rep = rep + rep_offset
            for cond, prob in conditions:
                name = f"{cond}_{prob}pct_{actual_rep}"
                print(f"\n--- {name} ---")

                logs = eval(
                    sandbagging_eval(
                        role=role,
                        n_questions=n_questions,
                        condition=cond,
                        probability=prob,
                        seed=seed + actual_rep,
                    ),
                    model=model,
                    log_dir=str(log_dir),
                    name=name,
                )

                orig_path = Path(logs[0].location)
                new_path = log_dir / f"{name}.eval"
                orig_path.rename(new_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="anthropic/claude-sonnet-4-20250514")
    parser.add_argument("--roles", nargs="+", default=list(ROLES.keys()),
                        choices=list(ROLES.keys()),
                        help="Which roles to run (default: all)")
    parser.add_argument("--n_questions", type=int, default=10)
    parser.add_argument("--n_repeats", type=int, default=3)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--rep_offset", type=int, default=0)
    args = parser.parse_args()

    run_all_conditions(
        model=args.model,
        roles=args.roles,
        n_questions=args.n_questions,
        n_repeats=args.n_repeats,
        seed=args.seed,
        run_counterfactual=args.counterfactual,
        rep_offset=args.rep_offset,
    )