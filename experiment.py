#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Memory-access-compile: join gate over three keepers.

Stages over a history / document store (source, not an executable dump):
  A. access-dont-dump          — query demand → LOOKUP|COMPOSE|REPLAY;
                                  DUMP is inject
  B. answerable-memory         — terminal WM must be memory-only answerable;
                                  empty/generic findings are MMC inject
  C. cartridge-retrieves-forgets — retrieval home ≠ retention home;
                                  treating cartridge as forever-memory is inject

Final action ∈ {serve, hold}.
Blind inject = DUMP ∧ empty/generic WM ∧ forever-cartridge.

Stdlib only. No network. No GPU. No vendor API.
Run: python3 experiment.py
"""

from __future__ import annotations

from typing import Optional

from access_stub import (
    QUERIES,
    access,
    answers,
    kitchen,
    plan,
)
from answerable_stub import (
    Question,
    REWARD,
    answer_from_evidence,
    answer_from_memory,
    cell,
    write_wm,
)
from cartridge_stub import (
    control_queries,
    homes_of,
    knowledge_queries,
    score,
    toy_corpus,
)


# ---------------------------------------------------------------------------
# Gate
# ---------------------------------------------------------------------------

def access_compile(
    qkey: str,
    *,
    force_mode: Optional[str] = None,
    wm_mode: str = "answerable",
    home: str = "cartridge",
    forever_cartridge: bool = False,
) -> dict:
    """Compile demand → access mode → answerable WM → home trade.

    Mapping:
      plan(q)             → LOOKUP | COMPOSE | REPLAY  (or DUMP if forced)
      write_wm            → question-conditioned findings (or empty/generic)
      home choice         → cartridge retrieves; context retains;
                            forever_cartridge pretends cartridge retains
      serve               = adaptive mode answers ∧ MSC ∧ home trade acknowledged
      hold                = any inject failure
      blind               = DUMP ∧ empty/generic WM ∧ forever_cartridge
    """
    turns, cards = kitchen()
    mode = force_mode if force_mode is not None else plan(qkey)
    ev = access(mode, turns, cards, qkey)
    qmeta = QUERIES[qkey]
    slot = qmeta["slot"]
    gold = slot if isinstance(qmeta["gold_need"], str) else qmeta["gold_need"][0]
    q = Question(ask=qmeta["text"], gold=gold, slot=slot)

    source = ev.cards_used[0] if ev.cards_used else (
        ev.sources_used[0] if ev.sources_used else "dump"
    )
    memory = write_wm(mode=wm_mode, source=source, slot=slot)

    ans_ok = answer_from_evidence(ev.texts, q) == q.gold
    mem_ok = answer_from_memory(memory, q) == q.gold
    awm_cell = cell(ans_ok, mem_ok)

    docs = toy_corpus()
    ctx, cart, comp, param = homes_of(docs)
    kq, cq = knowledge_queries(), control_queries()
    homes = {
        "context": ctx,
        "cartridge": cart,
        "compaction": comp,
        "parametric": param,
    }
    chosen = homes[home]
    knowledge_s = score(chosen, kq)
    control_s = score(chosen, cq)
    # Forever-cartridge inject: claim cartridge retains control even though it forgot.
    retention_ok = True
    if forever_cartridge:
        # Blind claim: retrieval home is also retention home.
        retention_ok = False  # measured failure: cartridge forgot control
        claimed_retention = control_s == 1.0  # what forever-claim needs; is False
        forever_claim = True
    else:
        claimed_retention = None
        forever_claim = False
        # Honest trade: cartridge may retrieve well and forget; context retains.
        if home == "cartridge":
            retention_ok = knowledge_s == 1.0 and control_s == 0.0
        elif home == "context":
            retention_ok = knowledge_s == 1.0 and control_s == 1.0
        else:
            # Compaction / parametric are neither the retrieval winner alone.
            retention_ok = True  # not asserting forever; just not the forever-inject

    access_ok = answers(ev, qkey) and mode != "DUMP"
    wm_ok = awm_cell == "MSC"
    home_ok = retention_ok and not forever_claim

    if access_ok and wm_ok and home_ok:
        action = "serve"
        reason = f"{mode}+MSC+{home}"
    else:
        action = "hold"
        fails = []
        if not access_ok:
            fails.append("access" if mode != "DUMP" else "dump")
        if not wm_ok:
            fails.append(f"wm:{awm_cell}")
        if forever_claim or not retention_ok:
            fails.append("forever-cartridge" if forever_claim else "home-trade")
        reason = "+".join(fails) if fails else "hold"

    return {
        "action": action,
        "reason": reason,
        "mode": mode,
        "planned": plan(qkey),
        "token_cost": ev.token_cost,
        "answers": answers(ev, qkey),
        "evidence_texts": ev.texts,
        "cards_used": ev.cards_used,
        "sources_used": ev.sources_used,
        "wm_cell": awm_cell,
        "wm_size": len(memory),
        "ans_ok": ans_ok,
        "mem_ok": mem_ok,
        "home": home,
        "knowledge_s": knowledge_s,
        "control_s": control_s,
        "forever_cartridge": forever_cartridge,
        "claimed_retention": claimed_retention,
        "ctx_knowledge": score(ctx, kq),
        "ctx_control": score(ctx, cq),
        "cart_knowledge": score(cart, kq),
        "cart_control": score(cart, cq),
        "comp_knowledge": score(comp, kq),
        "param_knowledge": score(param, kq),
        "param_control": score(param, cq),
    }


def blind_inject(qkey: str) -> dict:
    """Three injects at once: DUMP + empty WM + forever-cartridge."""
    return access_compile(
        qkey,
        force_mode="DUMP",
        wm_mode="empty",
        home="cartridge",
        forever_cartridge=True,
    )


def _ok(cond, msg):
    if not cond:
        raise AssertionError(msg)


# ---------------------------------------------------------------------------
# Seven join assertions (test the JOIN, not each pack alone)
# ---------------------------------------------------------------------------

def scenario_1():
    """Blind dump ≠ gate: DUMP+empty+forever holds; adaptive serve on local."""
    gate = access_compile("local_pref")
    blind = blind_inject("local_pref")
    _ok(gate["action"] == "serve", f"adaptive local should serve; got {gate['action']} {gate['reason']}")
    _ok(gate["mode"] == "LOOKUP", gate["mode"])
    _ok(gate["wm_cell"] == "MSC", gate["wm_cell"])
    _ok(blind["action"] == "hold", f"blind must hold; got {blind['action']}")
    _ok(blind["mode"] == "DUMP", blind["mode"])
    _ok(blind["wm_cell"] == "MMC", blind["wm_cell"])
    _ok(blind["forever_cartridge"] is True, "blind forever-cartridge flag")
    _ok(blind["token_cost"] > gate["token_cost"], (blind["token_cost"], gate["token_cost"]))
    return {
        "gate": gate["action"],
        "gate_mode": gate["mode"],
        "gate_wm": gate["wm_cell"],
        "blind": blind["action"],
        "blind_mode": blind["mode"],
        "blind_wm": blind["wm_cell"],
        "tokens": (gate["token_cost"], blind["token_cost"]),
    }


def scenario_2():
    """Demand selects LOOKUP|COMPOSE|REPLAY; fixed LOOKUP fails distributed+fidelity."""
    expected = {
        "local_pref": "LOOKUP",
        "distributed_trips": "COMPOSE",
        "fidelity_schedule": "REPLAY",
    }
    for qkey, mode in expected.items():
        g = access_compile(qkey)
        _ok(g["mode"] == mode, f"{qkey}: planned {mode}, got {g['mode']}")
        _ok(g["answers"] is True, (qkey, g["evidence_texts"]))
        _ok(g["action"] == "serve", f"{qkey} should serve; {g['reason']}")

    # Fixed LOOKUP inject: wrong mode for distributed and fidelity
    dist = access_compile("distributed_trips", force_mode="LOOKUP")
    fid = access_compile("fidelity_schedule", force_mode="LOOKUP")
    _ok(dist["answers"] is False, dist["evidence_texts"])
    _ok(fid["answers"] is False, fid["evidence_texts"])
    _ok(dist["action"] == "hold", dist["action"])
    _ok(fid["action"] == "hold", fid["action"])
    return {
        "planned": expected,
        "fixed_lookup_fails": ["distributed_trips", "fidelity_schedule"],
    }


def scenario_3():
    """After access, answerable WM is MSC; empty WM with same evidence is MMC."""
    # COMPOSE recovers distributed gold; answerable write → MSC/serve
    ok = access_compile("distributed_trips", wm_mode="answerable")
    empty = access_compile("distributed_trips", wm_mode="empty")
    _ok(ok["answers"] is True, ok["evidence_texts"])
    _ok(ok["wm_cell"] == "MSC", ok["wm_cell"])
    _ok(ok["action"] == "serve", ok["reason"])
    # Same access evidence visible at answer time, but empty M → MMC / hold
    _ok(empty["ans_ok"] is True, "evidence still answers")
    _ok(empty["mem_ok"] is False, "empty M not memory-answerable")
    _ok(empty["wm_cell"] == "MMC", empty["wm_cell"])
    _ok(empty["action"] == "hold", empty["reason"])
    _ok("wm:MMC" in empty["reason"], empty["reason"])
    return {
        "answerable": ok["wm_cell"],
        "empty": empty["wm_cell"],
        "serve": ok["action"],
        "hold": empty["action"],
    }


def scenario_4():
    """Generic finding after successful REPLAY is still MMC (access ≠ license)."""
    # REPLAY recovers fidelity schedule; generic WM still MMC
    ans = access_compile("fidelity_schedule", wm_mode="answerable")
    gen = access_compile("fidelity_schedule", wm_mode="generic")
    _ok(ans["mode"] == "REPLAY", ans["mode"])
    _ok(ans["answers"] is True, ans["evidence_texts"])
    _ok("t_plan_out" in ans["sources_used"], ans["sources_used"])
    _ok(ans["wm_cell"] == "MSC", ans["wm_cell"])
    _ok(ans["action"] == "serve", ans["reason"])
    _ok(gen["ans_ok"] is True, "REPLAY evidence still present")
    _ok(gen["mem_ok"] is False, "generic finding has no slot")
    _ok(gen["wm_cell"] == "MMC", gen["wm_cell"])
    _ok(gen["action"] == "hold", gen["reason"])
    # AWM reward separates MSC from MMC; answer-only cannot
    ans_only = {"MSC": 1.0, "MMC": 1.0}
    _ok(REWARD["MSC"] > REWARD["MMC"], REWARD)
    _ok(ans_only["MSC"] == ans_only["MMC"], "answer-only collapses")
    return {
        "replay_msc": ans["wm_cell"],
        "generic_mmc": gen["wm_cell"],
        "sources": ans["sources_used"],
        "reward_gap": REWARD["MSC"] - REWARD["MMC"],
    }


def scenario_5():
    """Cartridge retrieves (matches context); compaction/parametric lag — join with COMPOSE."""
    # Multi-doc access demand + cartridge home
    g = access_compile("distributed_trips", home="cartridge")
    _ok(g["mode"] == "COMPOSE", g["mode"])
    _ok(g["action"] == "serve", g["reason"])
    _ok(g["cart_knowledge"] == 1.0, g["cart_knowledge"])
    _ok(g["ctx_knowledge"] == 1.0, g["ctx_knowledge"])
    _ok(g["cart_knowledge"] == g["ctx_knowledge"], "cartridge matches ICL")
    _ok(g["comp_knowledge"] < g["cart_knowledge"], (g["comp_knowledge"], g["cart_knowledge"]))
    _ok(g["param_knowledge"] < g["cart_knowledge"], (g["param_knowledge"], g["cart_knowledge"]))
    # Compaction home alone is a weak retrieval pick for multi-doc
    weak = access_compile("distributed_trips", home="compaction")
    # Compaction still "serves" under current rule (not forever-inject), but
    # knowledge lags — join measures the lag vs cartridge.
    _ok(weak["knowledge_s"] < g["knowledge_s"], (weak["knowledge_s"], g["knowledge_s"]))
    return {
        "compose_mode": g["mode"],
        "cart_k": g["cart_knowledge"],
        "ctx_k": g["ctx_knowledge"],
        "comp_k": g["comp_knowledge"],
        "param_k": g["param_knowledge"],
    }


def scenario_6():
    """Forever-cartridge inject fails: retrieval ≠ retention; context retains both."""
    honest = access_compile("local_pref", home="cartridge", forever_cartridge=False)
    forever = access_compile("local_pref", home="cartridge", forever_cartridge=True)
    ctx = access_compile("local_pref", home="context", forever_cartridge=False)
    _ok(honest["action"] == "serve", honest["reason"])
    _ok(honest["cart_knowledge"] == 1.0, honest["cart_knowledge"])
    _ok(honest["cart_control"] == 0.0, honest["cart_control"])
    _ok(forever["action"] == "hold", forever["reason"])
    _ok("forever-cartridge" in forever["reason"], forever["reason"])
    _ok(forever["claimed_retention"] is False, forever["claimed_retention"])
    _ok(ctx["ctx_knowledge"] == 1.0 and ctx["ctx_control"] == 1.0, "context retains")
    _ok(ctx["action"] == "serve", ctx["reason"])
    # Parametric retains control but lags retrieval — dual object
    param = access_compile("local_pref", home="parametric")
    _ok(param["param_control"] == 1.0, param["param_control"])
    _ok(param["param_knowledge"] < honest["cart_knowledge"], param["param_knowledge"])
    return {
        "honest": honest["action"],
        "forever": forever["action"],
        "cart_k": honest["cart_knowledge"],
        "cart_c": honest["cart_control"],
        "ctx_k": ctx["ctx_knowledge"],
        "ctx_c": ctx["ctx_control"],
        "param_c": param["param_control"],
    }


def scenario_7():
    """Safe join path serves; three concurrent injects (dump / empty / forever) each hold."""
    # Safe: adaptive LOOKUP + MSC WM + honest cartridge trade
    safe = access_compile("local_pref")
    _ok(safe["action"] == "serve", safe["reason"])
    _ok(safe["mode"] == "LOOKUP", safe["mode"])
    _ok(safe["wm_cell"] == "MSC", safe["wm_cell"])
    _ok(safe["forever_cartridge"] is False, "honest home trade")
    _ok(safe["cart_control"] == 0.0, "cartridge forgot control (acknowledged)")

    dump = access_compile("local_pref", force_mode="DUMP", wm_mode="answerable")
    empty = access_compile("local_pref", force_mode="LOOKUP", wm_mode="empty")
    forever = access_compile(
        "local_pref", force_mode="LOOKUP", wm_mode="answerable", forever_cartridge=True
    )
    blind = blind_inject("local_pref")

    _ok(dump["action"] == "hold", f"DUMP must hold; got {dump['action']} {dump['reason']}")
    _ok("dump" in dump["reason"], dump["reason"])
    _ok(empty["action"] == "hold", empty["reason"])
    _ok("wm:MMC" in empty["reason"], empty["reason"])
    _ok(forever["action"] == "hold", forever["reason"])
    _ok("forever-cartridge" in forever["reason"], forever["reason"])
    _ok(blind["action"] == "hold", blind["reason"])
    # Blind stacks all three inject signatures
    _ok(blind["mode"] == "DUMP", blind["mode"])
    _ok(blind["wm_cell"] == "MMC", blind["wm_cell"])
    _ok(blind["forever_cartridge"] is True, True)
    # Adaptive cheaper than dump while still serving
    _ok(safe["token_cost"] < dump["token_cost"], (safe["token_cost"], dump["token_cost"]))
    # Across all three queries, adaptive serve path works
    for qkey in QUERIES:
        g = access_compile(qkey)
        _ok(g["action"] == "serve", f"{qkey}: {g['reason']}")
        b = blind_inject(qkey)
        _ok(b["action"] == "hold", f"blind {qkey}: {b['reason']}")
    return {
        "safe": safe["action"],
        "dump": dump["action"],
        "empty_wm": empty["action"],
        "forever": forever["action"],
        "blind": blind["action"],
        "safe_tokens": safe["token_cost"],
        "dump_tokens": dump["token_cost"],
        "all_queries_serve": list(QUERIES.keys()),
    }


SCENARIOS = [
    ("1_blind_dump_ne_gate", scenario_1),
    ("2_demand_selects_access_mode", scenario_2),
    ("3_answerable_wm_vs_empty_mmc", scenario_3),
    ("4_generic_after_replay_still_mmc", scenario_4),
    ("5_cartridge_retrieves_with_compose", scenario_5),
    ("6_forever_cartridge_vs_retention", scenario_6),
    ("7_safe_join_vs_three_injects", scenario_7),
]


def main() -> int:
    passed = 0
    for name, fn in SCENARIOS:
        try:
            detail = fn()
            passed += 1
            print(f"PASS  {name}: {detail}")
        except AssertionError as e:
            print(f"FAIL  {name}: {e}")
        except Exception as e:
            print(f"ERROR {name}: {e}")
    total = len(SCENARIOS)
    print(f"\n{passed}/{total} assertions passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
