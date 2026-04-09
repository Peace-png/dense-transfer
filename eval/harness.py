"""
Dense Transfer eval harness.

Runs the same task through three prompt modes (default, code-only, dense),
counts tokens, and scores downstream usability via a judge model.

Usage:
    python harness.py --model claude-sonnet-4-6 --task transformer
    python harness.py --model deepseek-chat --task all
    python harness.py --model qwen3-4b --base-url http://localhost:11434/v1 --task transformer

The harness speaks the OpenAI-compatible API format, which works with:
- OpenAI (default base_url)
- Anthropic via their OAI-compat endpoint
- DeepSeek, Z.AI / GLM, Together, Groq, Fireworks
- Local: Ollama, vLLM, llama.cpp server

Outputs results to results.json (or --output PATH).
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

try:
    from openai import OpenAI
except ImportError:
    print("Missing dependency. Run: pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)

try:
    import tiktoken
    _ENC = tiktoken.get_encoding("cl100k_base")
    def count_tokens(text: str) -> int:
        return len(_ENC.encode(text))
except ImportError:
    # Fallback: ~1.35 tokens per word for English prose
    def count_tokens(text: str) -> int:
        return int(len(text.split()) * 1.35)


REPO_ROOT = Path(__file__).parent.parent
TASKS_PATH = Path(__file__).parent / "tasks.json"
PROMPT_PATH = REPO_ROOT / "PROMPT.md"


# ---------- prompts ----------

def load_dense_prompt() -> str:
    raw = PROMPT_PATH.read_text()
    match = re.search(r"```\n(.*?)\n```", raw, re.DOTALL)
    if not match:
        raise ValueError(f"Could not extract prompt code block from {PROMPT_PATH}")
    return match.group(1)


DEFAULT_PROMPT = (
    "You are a helpful assistant. Provide thorough, well-structured, "
    "academically rigorous explanations."
)

CODE_ONLY_PROMPT = (
    "You are operating in CODE-ONLY mode. Respond with code or equations "
    "and one short metaphor. No prose explanations, no rationale, no "
    "failure modes. Maximum compression."
)


# ---------- model client ----------

def make_client(base_url: str | None, api_key_env: str) -> OpenAI:
    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise RuntimeError(
            f"Set {api_key_env} environment variable. "
            f"For local models without auth, set it to 'dummy'."
        )
    kwargs: dict[str, Any] = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAI(**kwargs)


def call_model(client: OpenAI, model: str, system: str, user: str) -> str:
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.3,
        max_tokens=4096,
    )
    return resp.choices[0].message.content or ""


# ---------- judge ----------

JUDGE_PROMPT_TEMPLATE = """\
You are an evaluator scoring a context document for downstream operational utility.

CONTEXT DOCUMENT:
---
{context}
---

DOWNSTREAM TASK:
{downstream_task}

Score the context document on a scale of 0.0 to 1.0 for whether it contains
sufficient information to perform the downstream task. Use these anchors:

- 1.0: All necessary information present. A competent agent could perform
  the task on first try with no clarification.
- 0.5: Core idea present but key details missing. Agent could perform the
  task with one round of clarification.
- 0.0: Insufficient information. Agent would have to start from scratch
  or hallucinate.

Respond with ONLY a JSON object in this exact format:
{{"score": 0.0, "reasoning": "one sentence"}}
"""


def judge_response(
    client: OpenAI,
    judge_model: str,
    context: str,
    downstream_task: str,
) -> dict:
    raw = call_model(
        client,
        judge_model,
        "You are a strict evaluator. Respond only with valid JSON.",
        JUDGE_PROMPT_TEMPLATE.format(context=context, downstream_task=downstream_task),
    )
    # Strip code fences if present
    cleaned = re.sub(r"```(?:json)?\n?|\n?```", "", raw).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"score": 0.0, "reasoning": f"judge returned invalid JSON: {raw[:200]}"}


# ---------- main loop ----------

def run_task(
    client: OpenAI,
    model: str,
    judge_model: str,
    task: dict,
    dense_prompt: str,
) -> dict:
    print(f"\n=== Task: {task['id']} ===", file=sys.stderr)

    modes = {
        "default": DEFAULT_PROMPT,
        "code_only": CODE_ONLY_PROMPT,
        "dense": dense_prompt,
    }

    results = {}
    for mode_name, system_prompt in modes.items():
        print(f"  generating {mode_name}...", file=sys.stderr)
        response = call_model(client, model, system_prompt, task["question"])
        token_count = count_tokens(response)

        print(f"  scoring {mode_name} ({token_count} tokens)...", file=sys.stderr)
        scores = {}
        for axis in ("implementation", "debug", "justify"):
            key = f"downstream_{axis}_task"
            judgement = judge_response(client, judge_model, response, task[key])
            scores[axis] = judgement

        avg = sum(s["score"] for s in scores.values()) / len(scores)

        results[mode_name] = {
            "token_count": token_count,
            "scores": scores,
            "average_score": round(avg, 3),
            "tokens_per_score_point": round(token_count / max(avg, 0.01), 1),
            "response": response,
        }

    return {"task_id": task["id"], "domain": task["domain"], "modes": results}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Model name to test")
    parser.add_argument("--judge-model", default=None, help="Judge model (defaults to --model)")
    parser.add_argument("--base-url", default=None, help="OpenAI-compat base URL")
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY", help="Env var holding API key")
    parser.add_argument("--task", default="all", help="Task ID or 'all'")
    parser.add_argument("--output", default="results.json")
    args = parser.parse_args()

    client = make_client(args.base_url, args.api_key_env)
    judge_model = args.judge_model or args.model
    dense_prompt = load_dense_prompt()
    tasks = json.loads(TASKS_PATH.read_text())["tasks"]

    if args.task != "all":
        tasks = [t for t in tasks if t["id"] == args.task]
        if not tasks:
            print(f"No task with id '{args.task}'", file=sys.stderr)
            sys.exit(1)

    all_results = []
    for task in tasks:
        all_results.append(run_task(client, args.model, judge_model, task, dense_prompt))

    output = {
        "model": args.model,
        "judge_model": judge_model,
        "results": all_results,
        "summary": summarise(all_results),
    }
    Path(args.output).write_text(json.dumps(output, indent=2))
    print(f"\nWrote {args.output}", file=sys.stderr)
    print_summary(output["summary"])


def summarise(all_results: list) -> dict:
    summary = {}
    for mode in ("default", "code_only", "dense"):
        tokens = [r["modes"][mode]["token_count"] for r in all_results]
        scores = [r["modes"][mode]["average_score"] for r in all_results]
        summary[mode] = {
            "avg_tokens": round(sum(tokens) / len(tokens)),
            "avg_score": round(sum(scores) / len(scores), 3),
        }
    base_tokens = summary["default"]["avg_tokens"]
    for mode in ("code_only", "dense"):
        reduction = 1 - (summary[mode]["avg_tokens"] / base_tokens)
        summary[mode]["reduction_vs_default"] = f"{reduction * 100:.1f}%"
    return summary


def print_summary(summary: dict):
    print("\n" + "=" * 60, file=sys.stderr)
    print("SUMMARY", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"{'mode':<12} {'tokens':>8} {'score':>8} {'reduction':>12}", file=sys.stderr)
    for mode, stats in summary.items():
        reduction = stats.get("reduction_vs_default", "—")
        print(
            f"{mode:<12} {stats['avg_tokens']:>8} {stats['avg_score']:>8.3f} {reduction:>12}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
