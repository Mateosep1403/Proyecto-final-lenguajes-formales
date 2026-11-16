"""Generic SDD evaluator using the dependency-graph method
(Aho et al., Sections 5.1.1, 5.2.1, 5.2.2).

The evaluator knows nothing about a particular SDD: everything comes from the
SDD object (data).  A rule is:  target attribute, list of attributes it uses,
and a function that computes it.  Attributes are written as (position, name),
where position 0 is the head of the production and 1..n are the body symbols.
"""
import heapq
from dataclasses import dataclass

from grammar import production_str


class Rule:
    def __init__(self, target, deps, fn, text=""):
        self.target = target   # (pos, attr) defined by this rule
        self.deps = deps       # list of (pos, attr) used by this rule
        self.fn = fn           # fn(*values_of_deps) -> value
        self.text = text       # human-readable form, for printing


class SDD:
    def __init__(self, attrs, rules, main_attr):
        # attrs: symbol -> {'syn': [names], 'inh': [names]}
        # rules: (head, body_tuple) -> [Rule, ...]
        # main_attr: attribute of the start symbol printed as the result
        self.attrs = attrs
        self.rules = rules
        self.main_attr = main_attr

    def decl(self, sym):
        return self.attrs.get(sym, {'syn': [], 'inh': []})

    # ---- well-formedness (Section 5.1.1) --------------------------------
    def check(self, g):
        errors = []
        if self.decl(g.start)['inh']:
            errors.append(f"start symbol {g.start} must not have inherited attributes")
        for head, body in g.productions:
            errors += self._check_production(g, head, body)
        return errors

    def _check_production(self, g, head, body):
        """Each rule defines a synthesized attribute of the head or an inherited
        attribute of a body symbol, using only attributes of this production;
        every such attribute is defined exactly once."""
        label = production_str(head, body)
        symbol_at = lambda pos: head if pos == 0 else body[pos - 1]
        errors, defined = [], []
        for r in self.rules.get((head, body), []):
            pos, attr = r.target
            if not 0 <= pos <= len(body):
                errors.append(f"{label}: bad position in target {r.target}")
                continue
            kind = 'syn' if pos == 0 else 'inh'
            if attr not in self.decl(symbol_at(pos))[kind]:
                role = ('a synthesized attribute of the head' if pos == 0
                        else 'an inherited attribute of a body symbol')
                errors.append(f"{label}: {symbol_at(pos)}.{attr} is not {role}")
            for dp, da in r.deps:
                if not 0 <= dp <= len(body):
                    errors.append(f"{label}: bad dependency position {dp}")
                    continue
                dsym = symbol_at(dp)
                if dsym in g.nonterminals:
                    d = self.decl(dsym)
                    if da not in d['syn'] + d['inh']:
                        errors.append(f"{label}: uses undeclared {dsym}.{da}")
                elif da != 'lexval':
                    errors.append(f"{label}: terminal {dsym} only has lexval")
            defined.append((pos, attr))
        required = [(0, a) for a in self.decl(head)['syn']]
        for i, s in enumerate(body, 1):
            if s in g.nonterminals:
                required += [(i, a) for a in self.decl(s)['inh']]
        for req in required:
            count = defined.count(req)
            if count != 1:
                errors.append(f"{label}: attribute at position {req} is defined "
                              f"{count} times (must be exactly once)")
        return errors


# ---- tree helpers -------------------------------------------------------
def preorder(root):
    """Iterative, so that deeply nested trees do not hit the recursion limit."""
    stack = [root]
    while stack:
        n = stack.pop()
        yield n
        stack.extend(reversed(n.children))


def node_label(n):
    return f"'{n.symbol}'#{n.id}" if n.terminal else f"{n.symbol}#{n.id}"


# ---- dependency graph ---------------------------------------------------
def build_graph(root, g, sdd):
    """Numbers the nodes in preorder and returns (nodes, verts, preds, rule_of).
    Vertices are (node_id, attr).  An edge u -> v means u is used to compute v
    (so u must be evaluated first); preds[v] is the set of such u."""
    nodes = {}
    for i, n in enumerate(preorder(root), 1):
        n.id = i
        nodes[i] = n
    verts, preds, rule_of = set(), {}, {}
    for n in nodes.values():
        if n.terminal:
            verts.update((n.id, a) for a in n.attrs)           # lexval
        else:
            d = sdd.decl(n.symbol)
            verts.update((n.id, a) for a in d['syn'] + d['inh'])
    for n in nodes.values():
        if n.terminal:
            continue
        at = lambda pos, n=n: n if pos == 0 else n.children[pos - 1]
        for r in sdd.rules.get(g.productions[n.prod], []):
            target = (at(r.target[0]).id, r.target[1])
            srcs = [(at(p).id, a) for p, a in r.deps]
            rule_of[target] = (r, srcs)
            preds.setdefault(target, set()).update(srcs)
    return nodes, verts, preds, rule_of


def topological_order(verts, preds):
    """Kahn's algorithm (ties broken by (node id, attr) for determinism).
    Returns (order, remaining) where remaining is non-empty iff there is a cycle."""
    succ = {v: set() for v in verts}
    indeg = {v: 0 for v in verts}
    for v, ps in preds.items():
        for p in ps:
            succ[p].add(v)
            indeg[v] += 1
    heap = [v for v in verts if indeg[v] == 0]
    heapq.heapify(heap)
    order = []
    while heap:
        v = heapq.heappop(heap)
        order.append(v)
        for w in sorted(succ[v]):
            indeg[w] -= 1
            if indeg[w] == 0:
                heapq.heappush(heap, w)
    return order, set(verts) - set(order)


def find_cycle(remaining, preds):
    """Every vertex left over by Kahn has a predecessor that is also left over;
    walk backwards until a vertex repeats."""
    v = min(remaining)
    seen, path = {}, []
    while v not in seen:
        seen[v] = len(path)
        path.append(v)
        v = min(p for p in preds[v] if p in remaining)
    cyc = path[seen[v]:][::-1]      # reverse: edges go from "used" to "defined"
    return cyc + [cyc[0]]


@dataclass
class Evaluation:
    nodes: dict          # node id -> Node
    order: list          # topological order of the vertices (node_id, attr)
    rule_of: dict        # vertex -> (Rule, source vertices); lexvals have none
    cycle: list = None   # a cycle of the dependency graph, or None


def evaluate(root, g, sdd):
    nodes, verts, preds, rule_of = build_graph(root, g, sdd)
    order, remaining = topological_order(verts, preds)
    if remaining:
        return Evaluation(nodes, order, rule_of, find_cycle(remaining, preds))
    for v in order:
        if v in rule_of:
            r, srcs = rule_of[v]
            nodes[v[0]].attrs[v[1]] = r.fn(*(nodes[i].attrs[a] for i, a in srcs))
    return Evaluation(nodes, order, rule_of)


# ---- printing -----------------------------------------------------------
def vertex_str(nodes, v):
    return f"{node_label(nodes[v[0]])}.{v[1]}"


def print_tree(root, g):
    stack = [(root, 0)]
    while stack:
        n, depth = stack.pop()
        attrs = ', '.join(f"{k}={v}" for k, v in sorted(n.attrs.items()))
        prod = '' if n.terminal else f" [{production_str(*g.productions[n.prod])}]"
        print(f"{'  ' * depth}{node_label(n)}{prod} {{{attrs}}}")
        stack.extend((c, depth + 1) for c in reversed(n.children))


def print_order(ev):
    for k, v in enumerate(ev.order, 1):
        note = '' if v in ev.rule_of else '   (given by the scanner)'
        print(f"  {k:>3}. {vertex_str(ev.nodes, v)}{note}")


def print_sdd(g, sdd):
    print("Attributes:")
    for sym in sorted(sdd.attrs):
        d = sdd.attrs[sym]
        print(f"  {sym}: synthesized {d['syn']}, inherited {d['inh']}")
    print("Semantic rules:")
    for head, body in g.productions:
        print(f"  {production_str(head, body)}")
        for r in sdd.rules.get((head, body), []):
            print(f"      {r.text}")
