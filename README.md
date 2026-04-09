# Dense Transfer

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE) [![GitHub](https://img.shields.io/badge/GitHub-Peace--png%2Fdense--transfer-181717?logo=github)](https://github.com/Peace-png/dense-transfer) [![Status](https://img.shields.io/badge/status-v0.1_early-orange)](https://github.com/Peace-png/dense-transfer)

**Strip ceremony. Keep claims.**

A prompt protocol and eval harness for getting LLMs to deliver maximum signal per token without losing accuracy.

> **Status: v0.1 -- early.** The prompt protocol works in daily use for the author. The eval harness is implemented but the verified-models table is empty until contributors run it. Token counts in the examples are real measurements of the *dense* outputs only -- the bloated baselines are illustrative excerpts of the kind of prose this protocol is designed to replace, not measured comparisons. Treat this repo as a tool to try and a methodology to verify, not a benchmark to cite.

---

## The problem

Default LLM output is often bloated. Not because models can't be concise -- because a lot of training data is academic and corporate prose that spends most of its tokens on throat-clearing. "It is important to note that...", "Notwithstanding these challenges...", multi-paragraph recaps of what you just asked.

When you're piloting an LLM orchestra -- passing context between agents, building long pipelines, running on a token budget -- that ceremony is tax. It costs money, eats context windows, and buries the signal.

The standard fix is "compress to code + a metaphor." That works for raw token count but tends to throw away the *why* behind decisions, the failure modes, and the cost model. Downstream agents end up with code they can run but can't debug.

## The fix (proposed)

A four-section output structure that aims to preserve everything operational while deleting everything ceremonial:

1. **CODE / MATH** -- the operational truth
2. **WHY** -- non-obvious decisions and what fails without them
3. **FAILURE MODES** -- where it breaks, cost model, escape hatches
4. **KEY** -- one-paragraph intuition that survives forgetting the math

Plus one writing rule that does most of the work:

> Every sentence must either assert something falsifiable, explain a non-obvious decision, or flag a failure mode. If it does none of those three, cut it.

That's the whole protocol. The full text lives in [`PROMPT.md`](PROMPT.md).

## What's verified, what isn't

**Verified by the author in daily use:**
- The protocol produces well-structured output across Claude, GPT-4 class models, and GLM via the `claude` CLI / Z.AI compat endpoint.
- Frontier instruction-tuned models follow the four-section structure first try.
- Output is subjectively shorter and easier to act on for coding, architecture, and technical Q&A tasks.

**Not yet measured (the harness exists, numbers are pending):**
- Exact token reduction percentages across models.
- Whether downstream operational accuracy is preserved, dropped, or improved vs default mode.
- How smaller local models (under ~7B) handle the protocol without few-shot examples.
- Sensitivity to judge-model bias in the eval rubric.

If you run the harness against any model, please PR your results. Verified numbers will be added to the table below as they come in.

## When to use it

- Coding explanations and architecture writeups
- Agent-to-agent context handoff in pipelines
- Technical documentation
- Research synthesis where someone will act on the output
- Anywhere a competent reader is being talked down to by default LLM output

## When NOT to use it

- Creative writing, narrative, scripts (the ceremony IS the craft)
- Investigative reporting where the audit trail is the deliverable
- Emotional or supportive conversation
- First-time learning by a beginner (reverse the order: KEY first, then CODE)
- Anything where the reader explicitly wants the long version

This matters. Dense Transfer is a tool, not a religion. It's designed for one specific failure mode of default LLM output. It is not a universal style guide.

## Quick start

1. Copy the prompt block from [`PROMPT.md`](PROMPT.md) into the system prompt of any instruction-tuned LLM.
2. Ask a technical question.
3. Compare to your usual default output.

For pipelines:

```python
import re
from pathlib import Path

raw = Path("PROMPT.md").read_text()
SYSTEM_PROMPT = re.search(r"```\n(.*?)\n```", raw, re.DOTALL).group(1)
# pass into your client of choice
```

## Model compatibility

Works in principle with any instruction-tuned model that accepts a system prompt. The eval harness speaks the OpenAI chat completions format, which covers:

| Provider | base_url |
|---|---|
| OpenAI | (default) |
| DeepSeek | `https://api.deepseek.com/v1` |
| Z.AI / GLM | `https://api.z.ai/api/coding/paas/v4` |
| Together | `https://api.together.xyz/v1` |
| Groq | `https://api.groq.com/openai/v1` |
| Ollama (local) | `http://localhost:11434/v1` |
| vLLM (local) | `http://localhost:8000/v1` |
| llama.cpp server | `http://localhost:8080/v1` |

Compliance quality is expected to scale with model capability. Frontier models are expected to follow the four-section structure cleanly; smaller local models (under ~7B parameters) may drift back into ceremony or skip sections -- a few-shot variant of the prompt may help, and adding one is on the v0.2 roadmap. None of this is measured yet.

### Verified models

*Empty until contributors run the harness. PRs welcome.*

| Model | Token reduction vs default | Operational accuracy | Judge model | Run by |
|-------|----------------------------|----------------------|-------------|--------|
| --     | --                          | --                    | --           | --      |

## Run the harness

```bash
cd eval
pip install -r requirements.txt

# Pick your provider:
export OPENAI_API_KEY=sk-...
python harness.py --model gpt-4o --task all

# Or a local Ollama model:
export OLLAMA_KEY=dummy
python harness.py --model qwen3:4b --base-url http://localhost:11434/v1 --api-key-env OLLAMA_KEY --task all
```

The harness runs each test question through three modes (default, code-only, dense), counts tokens, then asks a judge model to score downstream usability. Results land in `eval/results.json`.

**Caveats up front:**
- Token counts use `tiktoken` cl100k_base, which is accurate for OpenAI-family models and approximate for others. The *ratios* between modes are reliable; absolute counts for non-OpenAI models will drift 5-15%.
- The judge model has biases. Run with at least two different judges (`--judge-model`) and compare. Self-judging tends to score upward.
- The rubric measures three axes by default (implementability, debuggability, justifiability). The fourth axis (24-hour human recall) requires humans and is documented in `eval/rubric.md` but not automated.

## Repo layout

```
dense-transfer/
├── README.md           ← you are here
├── PROMPT.md           ← the protocol, copy-pasteable
├── examples/
│   ├── transformer.md      ← what dense output looks like for ML concepts
│   ├── debugging.md        ← the alternate hypothesis-first format
│   ├── architecture.md     ← architecture decision writeup
│   └── research.md         ← research synthesis
├── eval/
│   ├── harness.py          ← runs the comparison against any OAI-compat endpoint
│   ├── rubric.md           ← how downstream accuracy is scored
│   ├── tasks.json          ← the test questions
│   ├── requirements.txt
│   └── results.json        ← placeholder until contributors run the harness
└── LICENSE             ← MIT
```

## Contributing

Two things specifically wanted:

1. **Measured results** from running the harness against any model. PR a `results_<model>.json` and the model goes on the verified table.
2. **More worked examples** in domains I haven't covered (distributed systems, frontend, biology, finance, security). Each example should show what dense output looks like for that domain.

What's not wanted: PRs that add ceremony to the prompt itself. The whole point is the floor, not the ceiling.

## Honest limitations

- The protocol is one author's working hypothesis, refined in daily use across several months. It is not the result of a controlled study.
- "Dense Transfer beats default output on accuracy" is a hope, not a measured finding. The harness exists specifically to test that hope.
- The four-section structure may overfit to ML and engineering content. Domains with different epistemic structures (legal reasoning, medical diagnosis, historical analysis) may need a different shape entirely.
- The KEY section's value depends on the metaphor being good. Bad metaphors actively hurt recall. Models vary at generating good ones.
- Ceremony is sometimes signal. The "when not to use it" list is not exhaustive.

If any of these turn out to be larger problems than I think they are, I'd rather find out from a thoughtful issue than from a confident benchmark falling apart later.

## Author

**Peace-png** ([github.com/Peace-png](https://github.com/Peace-png))

## Star this repo

If Dense Transfer saves you tokens or improves your agent pipelines, consider starring the repo. It helps others find it.

---

## License

MIT. Use it, fork it, ship it inside your own tools. No attribution required.
