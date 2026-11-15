# Classifier accuracy (free keyword rules)

Measured on **unseen** messages, before fixing the rules each time:

| Batch | Result | Unsafe mistakes* |
|---|---|---|
| Original corpus (tuned against) | 55/79 (70%) at baseline | several |
| Held-out batch 1 (37 msgs) | 29/37 (78%) | 1 |
| Held-out batch 2 (30 msgs) | 23/30 (77%) | 1 |

\*Unsafe = an allergy, complaint or "speak to a person" message answered
automatically as an order / FAQ / booking / small talk. Mistakes that land in
"unknown" are SAFE: they go to a human.

After each batch the misses were fixed and added to `tests/corpus.py`, which
now has 148 messages and is a regression suite (100% by construction).

**Takeaway:** expect roughly 75-80% on new real-world messages with the free
rules. Safety messages are protected by a test that forbids unsafe mistakes on
the corpus, but new phrasings will always slip through. This is the main
reason to add an AI model later: it understands phrasing the rules never saw.

**To keep improving for free:** log real messages that went to "unknown" (the
dashboard shows them), add them to `tests/corpus.py` with the right category,
then adjust `src/classifier.py` until the tests pass.
