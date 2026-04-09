# Example: Research Synthesis

**Topic:** "Summarise the current state of the art on RLHF alternatives for language model alignment."

| Section | Tokens (cl100k_base) | Status |
|---|---|---|
| Bloated baseline | varies by model | illustrative excerpt below — not a measured response |
| Dense version (below) | **771** | measured |

> **Note on this example**: research synthesis is the closest the four-section format gets to its limits. Citations need to survive compression — they're claims, not ceremony. The dense version below keeps every paper reference; it cuts the throat-clearing around them. The specific paper list and characterisations are the author's working understanding as of early 2026 and should be verified against the original papers before being cited anywhere serious. This is a format demonstration, not an authoritative survey.

---

## Bloated version (illustrative excerpt of the kind of prose this protocol replaces)

> Reinforcement Learning from Human Feedback (RLHF) has emerged in recent years as one of the most prominent techniques for aligning large language models with human preferences and values. The technique, popularised by OpenAI's work on InstructGPT and subsequently used in the training of ChatGPT, involves a multi-stage pipeline in which human annotators rank model outputs, a reward model is trained on these rankings, and the language model is then fine-tuned using reinforcement learning to maximise the reward...

A typical version in this register continues by walking through each paper one at a time in chronological order with no synthesis across them.

---

## Dense version (full)

### CODE (the landscape)

```
RLHF alternatives, working understanding as of early 2026:

1. DPO        (Direct Preference Optimization)        — Rafailov et al. 2023
2. IPO        (Identity Preference Optimization)      — Azar et al. 2023
3. KTO        (Kahneman-Tversky Optimization)         — Ethayarajh et al. 2024
4. ORPO       (Odds Ratio Preference Optimization)    — Hong et al. 2024
5. SimPO      (Simple Preference Optimization)        — Meng et al. 2024
6. Constitutional AI / RLAIF                          — Bai et al. 2022 (Anthropic)
7. SPIN       (Self-Play Fine-Tuning)                 — Chen et al. 2024
```

### WHY (what each one is doing differently)

- **DPO**: skips the reward model entirely. Reformulates RLHF as a classification loss directly on preference pairs. Why it matters: removes the unstable RL step. Why it spread fast: simpler to implement, no PPO tuning hell.
- **IPO**: addresses a DPO failure mode where the model overfits to deterministic preferences and pushes log-ratios to extremes. Adds a regulariser. Use when DPO collapses.
- **KTO**: doesn't need pairwise data. Works with binary "good/bad" labels per output. Why it matters: pairwise preference data is expensive; binary labels are cheaper to collect at scale.
- **ORPO**: folds the SFT and preference stages into a single loss. Saves a full training pass. Quality has been reported as competitive with DPO at lower compute.
- **SimPO**: removes DPO's reference-model dependency. Length-normalised reward. Cheaper at training time, reported gains on some benchmarks.
- **Constitutional AI / RLAIF**: replaces human feedback with model-generated feedback against a written set of principles. Why it matters: scales past the human-annotation bottleneck. Anthropic's production approach.
- **SPIN**: bootstraps from SFT data alone, no preference data at all. Self-play between current and previous model checkpoints. Use when you have SFT data but no preference data.

### FAILURE MODES (the honest landscape)

- **DPO and family can overfit on small preference datasets**. The "RLHF is hard" problem hasn't been solved, just relocated. Watch eval loss, not just train loss.
- **No method dominates on all benchmarks**. Reported wins depend on the eval suite. The "best" choice depends on which bottleneck you care about most: cost, compute, data type, stability.
- **All preference-based methods inherit the biases of the preference data**. Switching from PPO to DPO doesn't fix bad annotators.
- **RLAIF / Constitutional AI is only as good as the constitution**. The principles become the thing you have to get right. The hard problem moves up a level, it doesn't disappear.
- **None of these address the deeper question** of what "alignment" means when the preference signal itself encodes contested values. That's a research question, not an engineering one.

### KEY

The trajectory has been to remove components from the original RLHF pipeline one at a time. DPO removed the reward model. KTO removed the pairwise requirement. SPIN removed the preference data. RLAIF removed the human. What remains is the question of whose values the model is being aligned to — and no method has touched that.

---

## What got cut from the bloated style and why

- **Definition of RLHF**: the reader asked about alternatives to RLHF. They know what RLHF is.
- **One-paragraph-per-paper walk-through**: replaced with the comparison list in WHY. Same information, denser.
- **"Future work" speculation**: not in the question.
- **Hedge-heavy "while X has shown promise, it remains to be seen..."**: replaced with concrete failure modes. Hedges hide claims; failure modes state them.

What was kept: every paper, every author, every year. Citations are claims, and claims survive compression.
