"""Generic SDD evaluator using the dependency-graph method
(Aho et al., Sections 5.1.1, 5.2.1, 5.2.2).

The evaluator knows nothing about a particular SDD: everything comes from the
SDD object (data).  A rule is:  target attribute, list of attributes it uses,
and a function that computes it.  Attributes are written as (position, name),
where position 0 is the head of the production and 1..n are the body symbols.
"""
import heapq


class Rule:
    def __init__(self, target, deps, fn, text=""):
        self.target = target   # (pos, attr) defined by this rule
        self.deps = deps       # list of (pos, attr) used by this rule
        self.fn = fn           # fn(*values_of_deps) -> value
        self.text = text       # human-readable form, for printing


class SDD:
    def __init__(self, attrs, rules, main=('S', 's')):
        # attrs: symbol -> {'syn': [names], 'inh': [names]}
        # rules: (head, body_tuple) -> [Rule, ...]
        self.attrs = attrs
        self.rules = rules
        self.main = main

    def decl(self, sym):
        return self.attrs.get(sym, {'syn': [], 'inh': []})

    # ---- well-formedness (Section 5.1.1) --------------------------------
    def check(self, g):
        errors = []
        if self.decl(g.start)['inh']:
            errors.append(f"start symbol {g.start} must not have inherited attributes")
        for head, body in g.productions:
            label = f"{head} -> {''.join(body) or 'e'}"
            rules = self.rules.get((head, body), [])
            defined = []
            for r in rules:
                pos, attr = r.target
                if not 0 <= pos <= len(body):
                    errors.append(f"{label}: bad position in target {r.target}")
                    continue
                sym = head if pos == 0 else body[pos - 1]
                if pos == 0 and attr not in self.decl(sym)['syn']:
                    errors.append(f"{label}: {sym}.{attr} defined but is not a "
                                  f"synthesized attribute of the head")
                if pos > 0 and attr not in self.decl(sym)['inh']:
                    errors.append(f"{label}: {sym}.{attr} defined but is not an "
                                  f"inherited attribute of a body symbol")
                for dp, da in r.deps:
                    if not 0 <= dp <= len(body):
                        errors.append(f"{label}: bad dependency position {dp}")
                        continue
                    dsym = head if dp == 0 else body[dp - 1]
                    if dsym in g.nt_set:
                        d = self.decl(dsym)
                        if da not in d['syn'] + d['inh']:
                            errors.append(f"{label}: uses undeclared {dsym}.{da}")
                    elif da != 'lexval':
                        errors.append(f"{label}: terminal {dsym} only has lexval")
                defined.append((pos, attr))
            required = [(0, a) for a in self.decl(head)['syn']]
            for i, s in enumerate(body):
                if s in g.nt_set:
                    required += [(i + 1, a) for a in self.decl(s)['inh']]
            for req in required:
                c = defined.count(req)
                if c != 1:
                    errors.append(f"{label}: attribute at position {req} is defined "
                                  f"{c} times (must be exactly once)")
        return errors


# ---- tree helpers -------------------------------------------------------
def preorder(n):
    yield n
    for c in n.children:
        yield from preorder(c)


def number_nodes(root):
    for i, n in enumerate(preorder(root), 1):
        n.id = i


def vname(nodes, v):
    n = nodes[v[0]]
    sym = f"'{n.symbol}'" if n.terminal else n.symbol
    return f"{sym}#{v[0]}.{v[1]}"


# ---- dependency graph ---------------------------------------------------
def build_graph(root, g, sdd):
    """Vertices are (node_id, attr).  An edge u -> v means u is used to
    compute v (so u must be evaluated first)."""
    nodes = {n.id: n for n in preorder(root)}
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
        head, body = g.productions[n.prod]
        at = lambda pos, n=n: n if pos == 0 else n.children[pos - 1]
        for r in sdd.rules.get((head, body), []):
            tv = (at(r.target[0]).id, r.target[1])
            srcs = [(at(p).id, a) for p, a in r.deps]
            verts.add(tv)
            verts.update(srcs)
            rule_of[tv] = (r, srcs)
            preds.setdefault(tv, set()).update(srcs)
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


def evaluate(root, g, sdd):
    """Returns dict with 'nodes', 'order', 'cycle' (None if non-circular)."""
    nodes, verts, preds, rule_of = build_graph(root, g, sdd)
    order, remaining = topological_order(verts, preds)
    if remaining:
        return {'nodes': nodes, 'order': order,
                'cycle': find_cycle(remaining, preds)}
    for v in order:
        if v in rule_of:
            r, srcs = rule_of[v]
            vals = [nodes[i].attrs[a] for i, a in srcs]
            nodes[v[0]].attrs[v[1]] = r.fn(*vals)
    return {'nodes': nodes, 'order': order, 'cycle': None, 'rule_of': rule_of}


# ---- printing -----------------------------------------------------------
def print_tree(root, g):
    def rec(n, depth):
        pad = '  ' * depth
        attrs = ', '.join(f"{k}={v}" for k, v in n.attrs.items())
        if n.terminal:
            print(f"{pad}'{n.symbol}'#{n.id} {{{attrs}}}")
        else:
            head, body = g.productions[n.prod]
            print(f"{pad}{n.symbol}#{n.id} [{head} -> {''.join(body) or 'e'}] {{{attrs}}}")
        for c in n.children:
            rec(c, depth + 1)
    rec(root, 0)


def print_order(result):
    nodes, rule_of = result['nodes'], result.get('rule_of', {})
    for k, v in enumerate(result['order'], 1):
        note = '' if v in rule_of else '   (given by the scanner)'
        print(f"  {k:>3}. {vname(nodes, v)}{note}")


def print_sdd(g, sdd):
    print("Attributes:")
    for sym in sorted(sdd.attrs):
        d = sdd.attrs[sym]
        print(f"  {sym}: synthesized {d['syn']}, inherited {d['inh']}")
    print("Semantic rules:")
    for head, body in g.productions:
        rules = sdd.rules.get((head, body), [])
        print(f"  {head} -> {''.join(body) or 'e'}")
        for r in rules:
            print(f"      {r.text}")