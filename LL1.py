"""LL(1) table construction (Alg. 4.31) and table-driven predictive parser
(Section 4.4.4). The grammar is NOT transformed."""

from grammar import END
from tree import Node


class LL1:
    def __init__(self, g):
        self.g = g
        self.table = {}       # (A, a) -> list of production indices
        self.is_ll1 = True
        for idx, (A, body) in enumerate(g.productions):
            f = g.first_of_string(body)
            for a in f:
                if a != 'e':
                    self._add(A, a, idx)
            if 'e' in f:
                for b in g.follow[A]:      # includes $
                    self._add(A, b, idx)

    def _add(self, A, a, idx):
        cell = self.table.setdefault((A, a), [])
        if idx not in cell:
            cell.append(idx)
        if len(cell) > 1:
            self.is_ll1 = False           # multiply-defined entry

    def parse(self, s, trace=False):
        """Returns (accepted, parse_tree_or_None, steps)."""
        g = self.g
        if any(c not in g.terminals for c in s):
            return False, None, []
        tokens = list(s) + [END]
        root = Node(g.start)
        stack = [Node(END, terminal=True), root]   # top of stack = last
        pos, steps = 0, []
        while True:
            X, a = stack[-1], tokens[pos]
            stk = ''.join(n.symbol for n in reversed(stack))
            inp = ''.join(tokens[pos:])
            if X.symbol == END:
                ok = (a == END)
                if trace:
                    steps.append((stk, inp, 'accept' if ok else 'error'))
                return ok, (root if ok else None), steps
            if not X.terminal:
                cell = self.table.get((X.symbol, a))
                if not cell:
                    if trace:
                        steps.append((stk, inp, 'error'))
                    return False, None, steps
                idx = cell[0]
                head, body = g.productions[idx]
                if trace:
                    steps.append((stk, inp, f"output {head} -> {''.join(body) or 'e'}"))
                stack.pop()
                X.prod = idx
                X.children = [Node(sym, terminal=sym not in g.nt_set) for sym in body]
                stack.extend(reversed(X.children))
            else:
                if X.symbol == a:
                    if trace:
                        steps.append((stk, inp, f"match {a}"))
                    stack.pop()
                    X.attrs['lexval'] = a
                    pos += 1
                else:
                    if trace:
                        steps.append((stk, inp, 'error'))
                    return False, None, steps

    def print_table(self):
        g = self.g
        cols = g.terminals + [END]
        rows = sorted(g.nt_set)
        cell = {}
        for (A, a), idxs in self.table.items():
            cell[(A, a)] = ' | '.join(
                f"{g.productions[i][0]}->{''.join(g.productions[i][1]) or 'e'}" for i in idxs)
        w = max([len(v) for v in cell.values()] + [len(c) for c in cols] + [3]) + 2
        print(' ' * 3 + ''.join(c.ljust(w) for c in cols))
        for A in rows:
            print(A.ljust(3) + ''.join(cell.get((A, c), '').ljust(w) for c in cols))