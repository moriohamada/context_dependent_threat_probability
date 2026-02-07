"""Analysis helpers for sandbagging experiment."""

import re
import pandas as pd
from pathlib import Path
from inspect_ai.log import read_eval_log
from roles import PROBABILITIES


def check_files_read(sample) -> dict:
    """Check which files agent read before submitting answers."""
    read_task = False
    read_deployment = False

    for msg in sample.messages:
        if msg.role == "tool" and "Answers recorded:" in str(msg.content):
            break

        if msg.role == "tool":
            content = str(msg.content)
            if "ARITHMETIC EVALUATION" in content:
                read_task = True
            if "undergoing capability evaluation" in content:
                read_deployment = True

    return {
        "read_task": read_task,
        "read_deployment_notes": read_deployment,
    }


def get_message_text(msg) -> str:
    """Extract text from a message, handling both string and list content."""
    raw = msg.content
    if isinstance(raw, str):
        return raw
    elif isinstance(raw, list):
        return " ".join(
            item.text for item in raw
            if hasattr(item, 'text') and item.text
        )
    return str(raw)


def extract_responses(sample) -> tuple[str, str]:
    """Extract initial response and followup explanation.

    Returns (initial, followup) split at the follow-up question.
    """
    initial, followup = [], []
    seen_followup = False

    for msg in sample.messages:
        content = str(msg.content).lower() if msg.role == "user" else ""
        if msg.role == "user" and ("before we finish" in content or "thanks, i've submitted" in content):
            seen_followup = True
        elif msg.role == "assistant":
            text = get_message_text(msg)
            if text.strip():
                (followup if seen_followup else initial).append(text)

    return "\n".join(initial), "\n".join(followup)


def extract_submitted_answers(sample, role: str) -> str | None:
    """Get submitted answers from sample."""
    # tool call (agent)
    for msg in sample.messages:
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tc in msg.tool_calls:
                if tc.function == "submit_answers":
                    return tc.arguments.get('answers', '')

    # direct response (advisor) - look for comma-separated answers
    for msg in sample.messages:
        if msg.role == "assistant":
            content = get_message_text(msg)

            # look for comma-separated A-D pattern (e.g., "A,B,C,D,A,B,C,D,A,B")
            match = re.search(r'\b([A-Da-d](?:\s*,\s*[A-Da-d])+)\b', content)
            if match:
                letters = [c.strip().upper() for c in match.group(1).split(",")]
                return ",".join(letters)

    return None


def load_results(model: str, role: str | list = None,
                 max_trials: int = None, log_dir: str = "./logs") -> pd.DataFrame:
    """Load experiment results into a DataFrame.

    Args:
        model: model name, e.g. "claude-sonnet-4-20250514"
        role: specific role(s) to load - string, list, or None for all
        max_trials: max repeats to include
        log_dir: base logs directory

    Expects structure: {log_dir}/{model}/{role}/*.eval
    """
    base = Path(log_dir) / model

    # collect paths based on role argument
    if role is None:
        paths = list(base.glob("*/*.eval"))
    elif isinstance(role, (list, tuple)):
        paths = [p for r in role for p in base.glob(f"{r}/*.eval")]
    else:
        paths = list(base.glob(f"{role}/*.eval"))

    rows = []
    for path in paths:
        if "-eval_" in path.name:
            continue

        role_name = path.parent.name
        stem = path.stem
        rep = int(stem.rsplit("_", 1)[1])

        if max_trials is not None and rep >= max_trials:
            continue

        name = stem.rsplit("_", 1)[0]
        condition = "counterfactual" if name.startswith("counterfactual") else "sandbag"
        prob_str = name.split("_")[1].replace("pct", "")
        probability = 0 if condition == "counterfactual" else int(prob_str)

        if probability not in PROBABILITIES and condition == "sandbag":
            continue

        log = read_eval_log(str(path))
        if not log.samples:
            print(f"skipping empty: {path}")
            continue
        sample = log.samples[0]
        initial, followup = extract_responses(sample)

        row = {
            "role": role_name,
            "condition": condition,
            "probability": probability,
            "repeat": rep,
            "score": list(sample.scores.values())[0].value if sample.scores else None,
            "submitted_answers": extract_submitted_answers(sample, role_name),
            "initial_response": initial,
            "followup_response": followup,
        }

        row.update(check_files_read(sample))

        rows.append(row)

    return pd.DataFrame(rows)