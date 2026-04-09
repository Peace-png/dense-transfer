# Example: Transformer Self-Attention

**Topic:** Explain the self-attention mechanism in transformers.

This example shows what a Dense Transfer response *looks like* for an ML concept. It is not a measured comparison — to get measured numbers for your model, run `eval/harness.py`.

| Section | Tokens (cl100k_base) | Status |
|---|---|---|
| Bloated baseline | varies by model | illustrative excerpt below — not a measured response |
| Dense version (below) | **487** | measured |

A typical academic treatment of this topic runs 1,500–2,500 words. The dense version below carries the operational content of that treatment in roughly one-fifth the space. Whether your model's *default* output is closer to the academic style or already concise is exactly what the harness measures.

---

## Bloated version (illustrative excerpt of the kind of prose this protocol replaces)

> The Transformer architecture, first introduced in the seminal paper *"Attention Is All You Need"* by Vaswani et al. (2017), represents a paradigmatic shift in the design of neural network architectures for sequence-to-sequence modelling tasks. Prior to its introduction, the field of natural language processing was largely dominated by recurrent neural networks and their gated variants, including Long Short-Term Memory networks and Gated Recurrent Units. While these architectures demonstrated considerable efficacy across a range of sequence modelling tasks, they were fundamentally constrained by their sequential computational nature...

A full version in this register typically continues for eight numbered sections, an abstract, and a summary. Almost none of it is wrong. Most of it is ceremony.

---

## Dense version (full)

### CODE

```python
import numpy as np

def attention(Q, K, V):
    d_k = Q.shape[-1]
    scores = (Q @ K.T) / np.sqrt(d_k)   # scale stops softmax saturating as d_k grows
    return softmax(scores) @ V          # weighted blend of V by Q-K relevance

# Q = what each token is looking for
# K = what each token offers
# V = what each token actually contributes
# Stack ~96 of these with learned projections + FFN + residuals = GPT-4-class model.
```

### WHY

- **sqrt(d_k) scaling**: without it, dot products grow with dimensionality, softmax saturates, gradients die. Training collapses — not cosmetic.
- **Multi-head**: run attention in parallel across N subspaces, concat, project. Each head learns a different relation type (syntax, coreference, long-range). One head can't do all jobs because softmax forces a single distribution per head.
- **Positional encoding added to inputs**: attention is order-blind. Without PE, "dog bites man" = "man bites dog".
- **Residuals + LayerNorm around every sublayer**: gradient highway. Depth past ~6 layers stops training without them.
- **Decoder-only + causal mask** (modern LLMs): same primitive, mask future tokens, train next-token prediction on raw text at scale. That's the entire GPT lineage.

### FAILURE MODES

- **O(n²·d) cost**: quadratic in sequence length. The reason context windows are expensive. Sparse/linear variants (Longformer, BigBird, Mamba-style SSMs) trade exactness for length.
- **Softmax bottleneck**: each head outputs a single probability distribution, capping the relations one head can express. Why you need many heads, not one big one.
- **Position generalisation**: sinusoidal PE generalises to unseen lengths in theory, breaks in practice past training distribution. RoPE and ALiBi exist because of this.

### KEY

Every token simultaneously asks *"who here is relevant to me?"* and borrows meaning weighted by the answer. Parallel, not sequential — that's why it killed RNNs. Multi-head means each token runs that scan through several lenses at once (syntax, semantics, reference) and merges what it finds.

---

## What got cut from the bloated style and why

- **History of RNNs and LSTMs**: doesn't change how you use attention today.
- **Bahdanau et al. citation chain**: doesn't change how you use attention today.
- **Re-derivation of Q/K/V matrix multiplication in prose**: the code shows it.
- **"Notwithstanding these challenges..." paragraph on scaling laws**: real content (Chinchilla) compressed to half a sentence in WHY.
- **Abstract and summary**: ceremony.

What was *kept*: every claim a downstream agent needs to either implement, debug, or recognise the failure modes of attention.
