"""Run the sandbagging experiment."""

import argparse
from pathlib import Path
from inspect_ai import eval

from task import sandbagging_eval
from roles import PROBABILITIES, ROLES
from dotenv import load_dotenv
load_dotenv(".env")


def run_all_conditions(model: str, roles: list[str], n_questions: int = 10,
                       n_repeats: int = 1, seed: int = 0, run_counterfactual: bool = True):

    model_name = model.split("/")[-1]

    for role in roles:
        print(f"ROLE: {role}")

        log_dir = Path(f"./logs/{model_name}/{role}")
        log_dir.mkdir(parents=True, exist_ok=True)

        # build list of conditions to run
        if run_counterfactual:
            middle_idx = (len(PROBABILITIES) - 1) // 2
            cf_prob = PROBABILITIES[middle_idx]
            conditions = [("counterfactual", cf_prob)] + [("sandbag", p) for p in PROBABILITIES]
        else:
            conditions = [("sandbag", p) for p in PROBABILITIES]

        for rep in range(n_repeats):
            for cond, prob in conditions:
                name = f"{cond}_{prob}pct_{rep}"
                print(f"\n--- {name} ---")

                logs = eval(
                    sandbagging_eval(
                        role=role,
                        n_questions=n_questions,
                        condition=cond,
                        probability=prob,
                        seed=seed + rep
                    ),
                    model=model,
                    log_dir=str(log_dir),
                    name=name,
                )

                # rename log file to something readable
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
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--counterfactual", type=bool, default=True)
    args = parser.parse_args()

    run_all_conditions(
        model=args.model,
        roles=args.roles,
        n_questions=args.n_questions,
        n_repeats=args.n_repeats,
        seed=args.seed,
        run_counterfactual=args.counterfactual,
    )