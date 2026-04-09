# Example: Debugging (alternate format)

**Topic:** "My PyTorch model loss is NaN after a few hundred steps. What's wrong?"

| Section | Tokens (cl100k_base) | Status |
|---|---|---|
| Bloated baseline | varies by model | illustrative excerpt below -- not a measured response |
| Dense version (below) | **612** | measured |

Debugging breaks the four-section format. The structure is **hypothesis → test → fix**. The reasoning chain matters more than the abstract "why" -- the user needs to follow your logic to apply it to their own situation.

---

## Bloated version (illustrative excerpt of the kind of prose this protocol replaces)

> NaN losses in PyTorch training are a common issue that can arise from a variety of sources. There are several things you should check. First, you should verify your learning rate. A learning rate that is too high can cause exploding gradients which lead to NaN values. You should also check your loss function. Some loss functions like cross-entropy can produce NaN values when the input contains values of 0 or negative numbers due to the logarithm operation. Another common cause is bad data in your training set...

A typical version in this register continues by listing every possible cause with no prioritisation, leaving the user to guess where to start.

---

## Dense version (full)

### Hypothesis (ranked by likelihood × ease of check)

1. **Exploding gradients from learning rate too high.** Most common cause when NaN appears after the model has been training fine for a while. The model finds a steep region of the loss surface, gradient blows up, weights become Inf, next forward pass produces NaN.
2. **Numerical instability in the loss function.** `log(0)` from a softmax output that hit 0, or `log(negative)` from an unclamped value. Cross-entropy on raw logits without `LogSoftmax` is the classic.
3. **Bad data leaking in mid-epoch.** A NaN or Inf in your dataset that the dataloader hits at step ~N.
4. **Mixed precision overflow.** If you're using fp16, activations can overflow to Inf.

### Test (do these in order, stop when you find it)

```python
# 1. Catch the NaN at the moment it appears
torch.autograd.set_detect_anomaly(True)

# 2. Log gradient norm every step
total_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=float('inf'))
print(f"step {step} grad_norm {total_norm:.2f}")
# If grad_norm spikes to 1e6+ right before NaN → it's #1

# 3. Check the data the step before failure
assert not torch.isnan(batch).any() and not torch.isinf(batch).any()
# If this trips → it's #3

# 4. Check loss function inputs
assert (probs > 0).all()  # before any log()
# If this trips → it's #2
```

### Fix (matched to which test tripped)

- **#1 (gradient spike):** Add `torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)` before `optimizer.step()`. Drop learning rate by 10x. If using Adam, increase `eps` to `1e-7`.
- **#2 (loss instability):** Use `nn.CrossEntropyLoss` on raw logits, never softmax → log manually. For custom losses, add `torch.clamp(x, min=1e-7)` before any `log`.
- **#3 (bad data):** Add the assertion to your dataloader's `__getitem__`. Find the offending row and decide: drop, impute, or fix upstream.
- **#4 (fp16 overflow):** Use `torch.cuda.amp.GradScaler` if you aren't already. If you are, the scaler is already handling it -- your problem is one of the other three.

### Why this order

Likelihood × ease of check. Gradient norm logging is one line and catches the most common cause. Data assertions are also one line. Loss function fixes require code changes. Mixed precision is least likely if you weren't touching it when the bug appeared.

---

## What got cut from the bloated style and why

- **The "list every possible cause" preamble**: replaced with a ranked hypothesis list. Prioritisation is the actual help.
- **Generic "check your data" advice**: replaced with the exact assertion line.
- **Tutorial on what NaN is**: the user has a NaN, they know what NaN is.
- **"Hope this helps!" / "Let me know if you have more questions"**: ceremony.

What was kept: the reasoning chain. The user needs to know *why* gradient spike is hypothesis #1, not #4 -- otherwise they can't adapt the logic when their situation differs.
