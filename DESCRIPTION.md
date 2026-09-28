# Memory-access-compile

A synergy deep-dive joining three keepers into one measurable
**memory access compile**. History / document bytes are source (not an
executable dump). Before serving an answer the gate compiles three
stages — demand-selected access mode, answerable working-memory write,
and retrieve-vs-retain home trade — into a final action
`serve | hold`. Blind inject (DUMP **and** empty/generic WM **and**
treating cartridge as forever-memory) is the AMMI-like lowering.

This is **not** a fresh arXiv pack. It reuses the discrete objects from:

- [access-dont-dump](https://github.com/StarDust-zz/access-dont-dump)
  (Chen et al., JustMem, [arXiv:2609.19877](https://arxiv.org/abs/2609.19877))
  — history source; LOOKUP|COMPOSE|REPLAY access config; DUMP inject
- [answerable-memory](https://github.com/StarDust-zz/answerable-memory)
  (Zhou et al., AWM, [arXiv:2608.25618](https://arxiv.org/abs/2608.25618))
  — terminal WM must be memory-only answerable; empty/generic → MMC
- [cartridge-retrieves-forgets](https://github.com/StarDust-zz/cartridge-retrieves-forgets)
  (Rakotonirina et al., [arXiv:2609.17346](https://arxiv.org/abs/2609.17346))
  — retrieval home ≠ retention home; cartridges match ICL and forget

```
python3 experiment.py
```

No GPU. No live model. No vendor API. No product import. Pure Python
stdlib.

## The object

```
# Stage A — access mode (access-dont-dump)
H, ATOMS   = history source + atomic cards with provenance
LOOKUP     = narrow discovery + compact reading
COMPOSE    = broad discovery + compact reading
REPLAY     = compact locate, then recover source via provenance
DUMP       = inject all of H                            ← inject
PLAN(q)    = (breadth, fidelity) → LOOKUP|COMPOSE|REPLAY

# Stage B — answerable WM (answerable-memory)
M          = terminal working memory (findings)
MSC        = final ans correct ∧ memory-only ans correct
MMC        = final ans correct ∧ memory-only fails
empty/generic findings with evidence still visible → MMC ← inject

# Stage C — document home (cartridge-retrieves-forgets)
CONTEXT    = raw docs in prompt (retrieves + retains)
CARTRIDGE  = loadable KV unit (retrieves; forgets control)
COMPACTION = lossy KV (lags retrieval)
PARAMETRIC = small adapter (lags multi-doc; retains control)
forever    = treat cartridge as retention home          ← inject

# Final gate
serve      = adaptive mode answers ∧ MSC ∧ honest home trade
hold       = DUMP ∨ MMC ∨ forever-cartridge ∨ wrong mode
blind      = DUMP ∧ empty/generic WM ∧ forever-cartridge  ← must differ
```

**Claim.** Memory access is a compile, not a dump: the query's evidence
demand selects an access mode (LOOKUP|COMPOSE|REPLAY) over an atomic
store; the written working-memory artifact must remain answerable
without the trajectory; and choosing a retrieval home (cartridge) is
not choosing a retention home. Dumping full history / empty-or-generic
WM / treating cartridge as forever-memory are the three inject failures
the join measures.

**Falsifier.** If blind DUMP+empty+forever matched the gate on action;
if fixed LOOKUP answered distributed and fidelity queries; if empty or
generic WM after successful access counted as MSC; if cartridge lagged
context on multi-doc while compaction matched; if forever-cartridge
still served while context failed to retain; or if any of the three
injects alone still served on the safe local path — the join collapses.

## What this pack tests (7/7 join, not each pack alone)

1. **Blind dump ≠ gate.** DUMP+empty WM+forever-cartridge holds;
   adaptive LOOKUP+MSC+honest cartridge serves at lower token cost.
2. **Demand selects access mode.** PLAN → LOOKUP|COMPOSE|REPLAY and
   each serves; fixed LOOKUP fails distributed and fidelity (hold).
3. **Answerable WM vs empty MMC.** After COMPOSE, answerable write is
   MSC/serve; same evidence with empty M is MMC/hold.
4. **Generic after REPLAY still MMC.** Successful REPLAY + generic
   finding is MMC (access ≠ license); AWM reward separates MSC/MMC.
5. **Cartridge retrieves with COMPOSE.** Multi-doc demand + cartridge
   matches context; compaction and parametric lag.
6. **Forever-cartridge vs retention.** Honest cartridge serves
   (retrieves, forgot control); forever-claim holds; context retains
   both; parametric retains but lags retrieval.
7. **Safe join vs three injects.** Adaptive+MSC+honest serves; DUMP,
   empty WM, and forever-cartridge each hold alone; stacked blind
   holds; all three queries serve under the adaptive path.

## Synergy

Joins the memory-access cluster:

- [access-dont-dump](https://github.com/StarDust-zz/access-dont-dump)
  — history is source; just-enough access is the compile; DUMP drifts
- [answerable-memory](https://github.com/StarDust-zz/answerable-memory)
  — terminal WM is an answerable compile; page/trajectory access ≠ license
- [cartridge-retrieves-forgets](https://github.com/StarDust-zz/cartridge-retrieves-forgets)
  — retrieval home ≠ retention home for the same document bytes

Also sits next to
[trust-compile-gate](https://github.com/StarDust-zz/trust-compile-gate)
(CRM/outbound `send|hold|escalate`),
[stop-cliff-compile](https://github.com/StarDust-zz/stop-cliff-compile)
(long-horizon `continue|cliff|stop`), and
[compile-dont-inject](https://github.com/StarDust-zz/compile-dont-inject)
(Brief-State compile vs AMMI). Here the product object is the
**memory access compile** (`serve|hold`).

## Keepers

If 7/7 pass: **Memory access is a compile: demand selects
LOOKUP|COMPOSE|REPLAY, terminal WM must be MSC, and retrieval home ≠
retention home. DUMP / empty-or-generic WM / forever-cartridge are the
three injects.**
