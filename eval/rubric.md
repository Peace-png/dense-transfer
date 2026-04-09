# Eval Rubric

How we score whether a compressed response actually preserves operational understanding.

## The core question

> Given only this response as context, can a downstream model successfully implement, debug, or extend the concept?

That's the test. Not "does it sound smart." Not "does it cover everything." **Can the next agent in the pipeline do its job from this alone.**

## The four scoring axes

Each response is scored 0–1 on four dimensions. The final score is the unweighted average.

### 1. Implementability (0–1)

Can a competent downstream model produce working code from this context alone?

- **1.0** — All necessary code, types, and parameters present. Downstream model produces a working implementation on first try.
- **0.5** — Core idea present but missing details (e.g. exact loss formulation, hyperparameter ranges). Downstream model produces working code on second try after one clarification.
- **0.0** — Insufficient detail. Downstream model either fails or hallucinates the missing pieces.

### 2. Debuggability (0–1)

If the downstream implementation fails, does the context contain enough information to diagnose why?

- **1.0** — Failure modes explicitly named with their causes. Downstream model can match observed failure to documented cause.
- **0.5** — Some failure modes mentioned but not linked to causes. Downstream model can guess but not verify.
- **0.0** — No failure modes named. Downstream model has to start debugging from scratch.

### 3. Justifiability (0–1)

If asked "why this design choice and not another," can the downstream model answer?

- **1.0** — Non-obvious choices have explicit rationale tied to a failure they prevent. Downstream model can defend the design.
- **0.5** — Choices listed but rationale missing or hand-wavy. Downstream model can describe but not defend.
- **0.0** — Choices presented as facts without rationale. Downstream model can only repeat them.

### 4. Recall (0–1)

After 24 hours, what fraction of the operational content does a human reader retain when asked to summarise?

- **1.0** — The KEY (intuition / metaphor) plus all four section labels. Reader can reconstruct the gist.
- **0.5** — KEY only, section structure forgotten.
- **0.0** — Nothing operational retained.

This is the only axis that benefits from the metaphor in KEY. It's also the only axis where humans, not models, are the judges.

## How to run the eval

1. Pick a question from `tasks.json`.
2. Generate three responses: default mode, code-only compression, dense transfer.
3. Count tokens for each (use the model's actual tokeniser, not word count).
4. For each response, run the four downstream tasks:
   - **Implementability**: feed the response to a small judge model with the prompt *"Using only the context above, write working code that implements [concept]."* Score the output.
   - **Debuggability**: feed the response plus a synthetic bug report. Prompt: *"Using only the context above, identify the most likely cause."* Score against ground truth.
   - **Justifiability**: feed the response plus a design challenge. Prompt: *"Using only the context above, defend [specific choice] against [alternative]."* Score the argument.
   - **Recall**: human reviewer reads the response, waits 24 hours, writes a summary. Score against the original.
5. Average the four scores. Record token count and final score in `results.json`.

## What this rubric is NOT measuring

- **Eloquence.** Pretty prose loses to ugly accuracy every time.
- **Completeness in absolute terms.** A response that covers 100% of a topic at 10,000 tokens loses to one covering 90% at 500 tokens. The metric is operational utility *per token*.
- **Whether a human enjoys reading it.** Different problem.

## Known limitations

- The judge model has biases. Run with at least two different judge models and compare.
- Downstream task quality is the actual ground truth and it's expensive to measure. The judge-model approach is a proxy. Treat it as such.
- Recall scores require humans and 24 hours. Most automated runs skip this and report a 3-axis average instead. That's fine — note it in `results.json`.
