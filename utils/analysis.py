"""Analysis helpers for sandbagging experiment."""

import re
import pandas as pd
from pathlib import Path
from inspect_ai.log import read_eval_log
from experiment.roles import PROBABILITIES


def check_files_read(sample) -> dict:
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
    raw = msg.content
    if isinstance(raw, str):
        return raw
    elif isinstance(raw, list):
        return " ".join(
            item.text for item in raw
            if hasattr(item, 'text') and item.text
        )
    return str(raw)


def extract_responses(sample) -> str:
    initial, followup = [], []
    seen_followup = False

    for msg in sample.messages:
        if msg.role == "assistant":
            text = get_message_text(msg)
            if text.strip():
                initial.append(text)

    return "\n".join(initial)


def extract_submitted_answers(sample, role: str) -> str | None:
    """Get submitted answers from sample."""
    # tool call (agent)
    for msg in sample.messages:
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tc in msg.tool_calls:
                if tc.function == "submit_answers":
                    return tc.arguments.get('answers', '')
    return None


def load_results(model: str, role: list[str] | str = None, log_dir: str = "./logs") -> pd.DataFrame:
    """Load experiment results into a DataFrame.

    Args:
        model: e.g. "claude-sonnet-4-20250514"
        role: specific role(s) to load -list of strings (['agent', 'advisor'])
        log_dir: base logs directory

    folder structure: {log_dir}/{model}/{role}/*.eval
    """
    base = Path(log_dir) / model

    # collect paths based on role argument
    if isinstance(role, list):
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

        name = stem.rsplit("_", 1)[0]
        condition = "counterfactual" if name.startswith("counterfactual") else "sandbag"
        prob_str = name.split("_")[1].replace("pct", "")
        probability = 0 if condition == "counterfactual" else int(prob_str)

        if probability not in PROBABILITIES and condition == "sandbag":
            continue

        log = read_eval_log(str(path))
        if not log.samples:
            continue

        sample = log.samples[0]
        response = extract_responses(sample)

        row = {
            "role": role_name,
            "condition": condition,
            "probability": probability,
            "repeat": rep,
            "score": list(sample.scores.values())[0].value if sample.scores else None,
            "submitted_answers": extract_submitted_answers(sample, role_name),
            "initial_response": response,
        }

        row.update(check_files_read(sample))

        rows.append(row)

    return pd.DataFrame(rows)