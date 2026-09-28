# SPDX-License-Identifier: MIT
"""Just-enough access algebra (from access-dont-dump / JustMem).

History is source; atomic cards + provenance are the store;
LOOKUP / COMPOSE / REPLAY are query-conditioned access compiles;
DUMP is inject.

Discrete of Chen et al., JustMem, arXiv:2609.19877.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class Turn:
    tid: str
    session: str
    text: str

    def tokens(self) -> int:
        return len(self.text.split())


@dataclass(frozen=True)
class Card:
    cid: str
    session: str
    kind: str  # factual | event | plan
    text: str
    tags: frozenset
    provenance: str  # turn id

    def tokens(self) -> int:
        return len(self.text.split())


@dataclass(frozen=True)
class Evidence:
    mode: str
    texts: Tuple[str, ...]
    token_cost: int
    cards_used: Tuple[str, ...]
    sources_used: Tuple[str, ...]


def kitchen() -> Tuple[Dict[str, Turn], Dict[str, Card]]:
    """Kyoto / Lisbon travel toy (JustMem-style)."""
    turns = {
        "t_pref": Turn(
            "t_pref",
            "S1",
            "I prefer small quiet hotels and feel anxious in crowded places.",
        ),
        "t_kyoto_visit": Turn(
            "t_kyoto_visit",
            "S2",
            "I visited Kyoto Japan in April 2025.",
        ),
        "t_lisbon_visit": Turn(
            "t_lisbon_visit",
            "S4",
            "I visited Lisbon Portugal in October 2025.",
        ),
        "t_plan_ask": Turn(
            "t_plan_ask",
            "S3",
            "Can you plan a relaxed morning in Kyoto before my afternoon train?",
        ),
        "t_plan_out": Turn(
            "t_plan_out",
            "S3",
            (
                "8:00 breakfast near the hotel; "
                "9:30 walk along the Kamo River; "
                "12:30 leave for Kyoto Station."
            ),
        ),
        "t_noise": Turn(
            "t_noise",
            "S5",
            "Also remind me to buy a metro card next year maybe.",
        ),
    }
    cards = {
        "c_pref": Card(
            "c_pref",
            "S1",
            "factual",
            "The user prefers small quiet hotels and feels anxious in crowded places.",
            frozenset({"preference", "hotel", "quiet", "kyoto"}),
            "t_pref",
        ),
        "c_kyoto": Card(
            "c_kyoto",
            "S2",
            "event",
            "PERSON User EVENT Visited Kyoto Japan DATE April 2025",
            frozenset({"travel", "kyoto", "2025", "april"}),
            "t_kyoto_visit",
        ),
        "c_lisbon": Card(
            "c_lisbon",
            "S4",
            "event",
            "PERSON User EVENT Visited Lisbon Portugal DATE October 2025",
            frozenset({"travel", "lisbon", "2025", "october"}),
            "t_lisbon_visit",
        ),
        "c_plan": Card(
            "c_plan",
            "S3",
            "plan",
            "The assistant created a timed itinerary for the user's last morning in Kyoto.",
            frozenset({"kyoto", "morning", "schedule", "itinerary", "plan"}),
            "t_plan_out",
        ),
        "c_noise": Card(
            "c_noise",
            "S5",
            "factual",
            "The user mentioned buying a metro card next year.",
            frozenset({"metro", "future"}),
            "t_noise",
        ),
    }
    return turns, cards


QUERIES = {
    "local_pref": {
        "text": "Would a quiet Kyoto guesthouse suit me?",
        "tags": frozenset({"preference", "quiet", "hotel", "kyoto"}),
        "distributed": False,
        "fidelity": False,
        "gold_need": "small quiet",
        "gold_mode": "LOOKUP",
        "slot": "small quiet",
    },
    "distributed_trips": {
        "text": "Write a one-line summary of my 2025 trips.",
        "tags": frozenset({"travel", "2025"}),
        "distributed": True,
        "fidelity": False,
        "gold_need": ("Kyoto", "Lisbon"),
        "gold_mode": "COMPOSE",
        "slot": "Kyoto",  # binding token for answerability checks
    },
    "fidelity_schedule": {
        "text": "Pull up the schedule for my last morning in Kyoto.",
        "tags": frozenset({"kyoto", "morning", "schedule"}),
        "distributed": False,
        "fidelity": True,
        "gold_need": "8:00 breakfast",
        "gold_mode": "REPLAY",
        "slot": "8:00 breakfast",
    },
}


def plan(qkey: str) -> str:
    q = QUERIES[qkey]
    if q["fidelity"]:
        return "REPLAY"
    if q["distributed"]:
        return "COMPOSE"
    return "LOOKUP"


def _score(card: Card, tags: frozenset) -> int:
    return len(card.tags & tags)


def lookup(cards: Dict[str, Card], tags: frozenset, k: int = 1) -> List[Card]:
    ranked = sorted(cards.values(), key=lambda c: (-_score(c, tags), c.cid))
    return [c for c in ranked if _score(c, tags) > 0][:k]


def compose(cards: Dict[str, Card], tags: frozenset, k: int = 3) -> List[Card]:
    rewrite = frozenset(t for t in tags if t in {"travel", "2025", "kyoto", "lisbon"})
    pool_tags = tags | rewrite | frozenset({"travel", "2025"})
    ranked = sorted(cards.values(), key=lambda c: (-_score(c, pool_tags), c.cid))
    return [c for c in ranked if _score(c, pool_tags) > 0][:k]


def dump_all(turns: Dict[str, Turn]) -> Evidence:
    texts = tuple(t.text for t in turns.values())
    return Evidence(
        mode="DUMP",
        texts=texts,
        token_cost=sum(t.tokens() for t in turns.values()),
        cards_used=(),
        sources_used=tuple(turns.keys()),
    )


def access(
    mode: str,
    turns: Dict[str, Turn],
    cards: Dict[str, Card],
    qkey: str,
) -> Evidence:
    q = QUERIES[qkey]
    tags = q["tags"]
    if mode == "DUMP":
        return dump_all(turns)
    if mode == "LOOKUP":
        hits = lookup(cards, tags, k=1)
        texts = tuple(c.text for c in hits)
        return Evidence(
            mode="LOOKUP",
            texts=texts,
            token_cost=sum(c.tokens() for c in hits),
            cards_used=tuple(c.cid for c in hits),
            sources_used=(),
        )
    if mode == "COMPOSE":
        hits = compose(cards, tags, k=3)
        texts = tuple(c.text for c in hits)
        return Evidence(
            mode="COMPOSE",
            texts=texts,
            token_cost=sum(c.tokens() for c in hits),
            cards_used=tuple(c.cid for c in hits),
            sources_used=(),
        )
    if mode == "REPLAY":
        hits = lookup(cards, tags, k=1)
        recovered: List[str] = []
        sources: List[str] = []
        cost = 0
        for c in hits:
            cost += c.tokens()
            src = turns[c.provenance]
            recovered.append(src.text)
            sources.append(src.tid)
            cost += src.tokens()
        return Evidence(
            mode="REPLAY",
            texts=tuple(recovered),
            token_cost=cost,
            cards_used=tuple(c.cid for c in hits),
            sources_used=tuple(sources),
        )
    raise ValueError(mode)


def answers(ev: Evidence, qkey: str) -> bool:
    blob = " ".join(ev.texts)
    need = QUERIES[qkey]["gold_need"]
    if isinstance(need, tuple):
        return all(n in blob for n in need)
    return need in blob
