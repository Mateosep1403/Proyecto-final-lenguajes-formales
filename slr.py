"""SLR(1): LR(0) items, CLOSURE/GOTO and canonical collection (Section 4.6.2),
ACTION/GOTO tables (Algorithm 4.46) and the LR parsing algorithm
(Algorithm 4.44, Section 4.6.3)."""

from grammar import END, production_str
from tree import Node

AUG = "S'"


class SLR:
    name = 'SLR(1)'

    def __init__(self, g):
        self.g = g
        # production 0 is the augmenting production S' -> S
        self.prods = [(AUG, (g.start,))] + g.productions
        self.states = []      # list of frozenset of items (prod_index, dot)
        self.trans = {}       # (state, symbol) -> state
        self.action = {}      # (state, terminal or $) -> ('s', j) | ('r', p) | ('acc',)
        self.goto = {}        # (state, nonterminal) -> state
        self.is_valid = True
        self._build_automaton()
        self._build_tables()

    # ---- canonical collection ------------------------------------------
    def closure(self, items):
        res = set(items)
        work = list(items)
        while work:
            p, d = work.pop()
            body = self.prods[p][1]
            if d < len(body) and body[d] in self.g.nonterminals:
                for q, _ in self.g.productions_of(body[d]):
                    item = (q + 1, 0)             # +1: shifted by S' -> S
                    if item not in res:
                        res.add(item)
                        work.append(item)
        return frozenset(res)

    def goto_set(self, I, X):
        moved = {(p, d + 1) for (p, d) in I
                 if d < len(self.prods[p][1]) and self.prods[p][1][d] == X}
        return self.closure(moved) if moved else None

    def _build_automaton(self):
        symbols = sorted(self.g.nonterminals) + self.g.terminals
        start = self.closure({(0, 0)})
        self.states = [start]
        index = {start: 0}
        i = 0
        while i < len(self.states):
            for X in symbols:
                J = self.goto_set(self.states[i], X)
                if J is None:
                    continue
                if J not in index:
                    index[J] = len(self.states)
                    self.states.append(J)
                self.trans[(i, X)] = index[J]
            i += 1

    # ---- tables ---------------------------------------------------------
    def _set_action(self, i, a, act):
        old = self.action.get((i, a))
        if old is not None and old != act:
            self.is_valid = False     # shift/reduce or reduce/reduce conflict
            return
        self.action[(i, a)] = act

    def _build_tables(self):
        g = self.g
        for i, I in enumerate(self.states):
            for (p, d) in sorted(I):
                H, body = self.prods[p]
                if d < len(body):
                    a = body[d]
                    if a not in g.nonterminals:
                        self._set_action(i, a, ('s', self.trans[(i, a)]))
                elif p == 0:
                    self._set_action(i, END, ('acc',))
                else:
                    for a in g.follow[H]:
                        self._set_action(i, a, ('r', p))
            for A in g.nonterminals:
                if (i, A) in self.trans:
                    self.goto[(i, A)] = self.trans[(i, A)]

    # ---- parsing --------------------------------------------------------
    def parse(self, w, trace=False):
        """Returns (accepted, parse_tree_or_None, steps)."""
        tokens = self.g.tokens(w)
        if tokens is None:
            return False, None, []
        states, nodes, pos, steps = [0], [], 0, []

        def log(action):
            if trace:
                stack = str(states[0]) + ''.join(
                    f" {n.symbol} {states[k + 1]}" for k, n in enumerate(nodes))
                steps.append((stack, ''.join(tokens[pos:]), action))

        while True:
            a = tokens[pos]
            act = self.action.get((states[-1], a))
            if act is None:
                log('error')
                return False, None, steps
            if act[0] == 's':
                log(f"shift {act[1]}")
                leaf = Node(a, terminal=True)
                leaf.attrs['lexval'] = a
                nodes.append(leaf)
                states.append(act[1])
                pos += 1
            elif act[0] == 'r':
                H, body = self.prods[act[1]]
                log(f"reduce {production_str(H, body)}")
                k = len(body)                     # k may be 0 (epsilon)
                node = Node(H)
                node.prod = act[1] - 1            # index in g.productions
                node.children = nodes[len(nodes) - k:]
                del nodes[len(nodes) - k:]
                del states[len(states) - k:]
                nodes.append(node)
                states.append(self.goto[(states[-1], H)])
            else:
                log('accept')
                return True, nodes[0], steps

    # ---- printing -------------------------------------------------------
    def item_str(self, p, d):
        H, body = self.prods[p]
        b = list(body)
        b.insert(d, '.')
        return f"{H} -> {''.join(b)}"

    def print_automaton(self):
        for i, I in enumerate(self.states):
            print(f"I{i}:")
            for (p, d) in sorted(I):
                print(f"    {self.item_str(p, d)}")
        print("Transitions:")
        for (i, X), j in sorted(self.trans.items()):
            print(f"    I{i} --{X}--> I{j}")

    def print_table(self):
        g = self.g
        tcols = g.terminals + [END]
        ncols = sorted(g.nonterminals)
        header = ['state'] + tcols + ncols
        rows = []
        for i in range(len(self.states)):
            row = [str(i)]
            for a in tcols:
                act = self.action.get((i, a))
                row.append('' if act is None else
                           ('acc' if act[0] == 'acc' else f"{act[0]}{act[1]}"))
            for A in ncols:
                row.append(str(self.goto.get((i, A), '')))
            rows.append(row)
        w = max(len(c) for r in rows + [header] for c in r) + 2
        print(''.join(c.ljust(w) for c in header))
        for r in rows:
            print(''.join(c.ljust(w) for c in r))
