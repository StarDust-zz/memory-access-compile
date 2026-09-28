# SPDX-License-Identifier: MIT
"""Document homes algebra (from cartridge-retrieves-forgets).

Same document bytes, four lowerings. Retrieval home ≠ retention home.
Cartridges match ICL on multi-doc retrieval; they also forget control.

Discrete of Rakotonirina et al., arXiv:2609.17346.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class Document:
    doc_id: str
    facts: FrozenSet[Tuple[str, str]]


@dataclass(frozen=True)
class Query:
    key: str
    target_doc: str
    expected: str


def toy_corpus() -> List[Document]:
    return [
        Document(
            "leases",
            frozenset({("tenant", "Ada"), ("rent", "1200"), ("due", "first")}),
        ),
        Document(
            "payroll",
            frozenset({("employee", "Bo"), ("salary", "90k"), ("role", "eng")}),
        ),
        Document(
            "inventory",
            frozenset({("sku", "W-41"), ("stock", "17"), ("bin", "A3")}),
        ),
        Document(
            "coding-control",
            frozenset({("sort", "timsort"), ("hash", "siphash"), ("gc", "refcount")}),
        ),
    ]


def knowledge_queries() -> List[Query]:
    return [
        Query("tenant", "leases", "Ada"),
        Query("salary", "payroll", "90k"),
        Query("stock", "inventory", "17"),
    ]


def control_queries() -> List[Query]:
    return [
        Query("sort", "coding-control", "timsort"),
        Query("hash", "coding-control", "siphash"),
        Query("gc", "coding-control", "refcount"),
    ]


@dataclass(frozen=True)
class Cartridge:
    doc_id: str
    kv: FrozenSet[Tuple[str, str]]


@dataclass
class CartridgeBank:
    cartridges: Dict[str, Cartridge] = field(default_factory=dict)
    base_control: Dict[str, str] = field(default_factory=dict)
    forgetting: float = 0.0

    def install(self, docs: Sequence[Document], *, forget: bool = True) -> None:
        for d in docs:
            if d.doc_id == "coding-control":
                self.base_control = dict(d.facts)
            else:
                self.cartridges[d.doc_id] = Cartridge(d.doc_id, d.facts)
        if forget and self.cartridges:
            self.forgetting = 0.6

    def answer(self, q: Query) -> Optional[str]:
        if q.target_doc == "coding-control":
            if self.forgetting >= 0.5:
                return None
            return self.base_control.get(q.key)
        cart = self.cartridges.get(q.target_doc)
        if cart is None:
            return None
        return dict(cart.kv).get(q.key)


@dataclass
class ContextWindow:
    present: Dict[str, FrozenSet[Tuple[str, str]]] = field(default_factory=dict)
    base_control: Dict[str, str] = field(default_factory=dict)

    def load(self, docs: Sequence[Document]) -> None:
        for d in docs:
            if d.doc_id == "coding-control":
                self.base_control = dict(d.facts)
            else:
                self.present[d.doc_id] = d.facts

    def answer(self, q: Query) -> Optional[str]:
        if q.target_doc == "coding-control":
            return self.base_control.get(q.key)
        facts = self.present.get(q.target_doc)
        if facts is None:
            return None
        return dict(facts).get(q.key)


@dataclass
class Compaction:
    keep: int
    blobs: Dict[str, FrozenSet[Tuple[str, str]]] = field(default_factory=dict)
    base_control: Dict[str, str] = field(default_factory=dict)

    def install(self, docs: Sequence[Document]) -> None:
        for d in docs:
            if d.doc_id == "coding-control":
                self.base_control = dict(d.facts)
            else:
                ordered = sorted(d.facts, key=lambda kv: kv[0])
                self.blobs[d.doc_id] = frozenset(ordered[: self.keep])

    def answer(self, q: Query) -> Optional[str]:
        if q.target_doc == "coding-control":
            return self.base_control.get(q.key)
        facts = self.blobs.get(q.target_doc)
        if facts is None:
            return None
        return dict(facts).get(q.key)


@dataclass
class ParametricAdapter:
    capacity: int
    table: Dict[str, str] = field(default_factory=dict)
    owners: Dict[str, str] = field(default_factory=dict)
    base_control: Dict[str, str] = field(default_factory=dict)
    forgetting: float = 0.0

    def install(self, docs: Sequence[Document]) -> None:
        n = 0
        for d in docs:
            if d.doc_id == "coding-control":
                self.base_control = dict(d.facts)
                continue
            for k, v in sorted(d.facts):
                if n >= self.capacity:
                    break
                self.table[k] = v
                self.owners[k] = d.doc_id
                n += 1
        self.forgetting = 0.0

    def answer(self, q: Query) -> Optional[str]:
        if q.target_doc == "coding-control":
            return self.base_control.get(q.key)
        if q.key in self.table and self.owners.get(q.key) == q.target_doc:
            return self.table[q.key]
        return None


def score(answerer, queries: Sequence[Query]) -> float:
    if not queries:
        return 0.0
    hits = sum(1 for q in queries if answerer.answer(q) == q.expected)
    return hits / len(queries)


def homes_of(
    docs: Sequence[Document],
) -> Tuple[ContextWindow, CartridgeBank, Compaction, ParametricAdapter]:
    ctx = ContextWindow()
    ctx.load(docs)
    cart = CartridgeBank()
    cart.install(docs, forget=True)
    comp = Compaction(keep=1)
    comp.install(docs)
    param = ParametricAdapter(capacity=3)
    param.install(docs)
    return ctx, cart, comp, param
