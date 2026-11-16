"""LL(1) test (definition at the beginning of Section 4.4.3), predictive
parsing table (Algorithm 4.31) and table-driven predictive parser
(Algorithm 4.34, Section 4.4.4). The grammar is NOT transformed."""

from itertools import combinations

from grammar import EPS, END, production_str
from tree import Node


class LL1:
    name = 'LL(1)'

    def __init__(self, g):
        self.g = g
        self.is_valid = self._satisfies_ll1_definition()
        self.table = self._build_table()

    def _satisfies_ll1_definition(self):
        """For every pair of distinct productions A -> alpha | beta:
        1. alpha and beta do not derive strings beginning with the same terminal;
        2. at most one of them derives the empty string;
        3. if beta =>* e, alpha derives no string beginning with a terminal
           of FOLLOW(A) (and symmetrically).
        Conditions 1 and 2 together are FIRST(alpha) & FIRST(beta) == {}."""
        g = self.g
        for A in g.nonterminals:
            firsts = [g.first_of_string(body) for _, body in g.productions_of(A)]
            for f1, f2 in combinations(firsts, 2):
                if f1 & f2:
                    return False
                if EPS in f1 and f2 & g.follow[A] or EPS in f2 and f1 & g.follow[A]:
                    return False
        return True

    def _build_table(self):
        """(A, a) -> list of production indices; a cell with more than one
        index only exists when the grammar is not LL(1)."""
        g = self.g
        table = {}
        for idx, (A, body) in enumerate(g.productions):
            f = g.first_of_string(body)
            lookaheads = (f - {EPS}) | (g.follow[A] if EPS in f else set())
            for a in lookaheads:
                table.setdefault((A, a), []).append(idx)
        return table

    def parse(self, w, trace=False):
        """Returns (accepted, parse_tree_or_None, steps)."""
        g = self.g
        tokens = g.tokens(w)
        if tokens is None:
            return False, None, []
        root = Node(g.start)
        stack = [Node(END, terminal=True), root]   # top of stack = last
        pos, steps = 0, []

        def log(action):
            if trace:
                steps.append((''.join(n.symbol for n in reversed(stack)),
                              ''.join(tokens[pos:]), action))

        while True:
            X, a = stack[-1], tokens[pos]
            if X.symbol == END:
                accepted = a == END
                log('accept' if accepted else 'error')
                return accepted, (root if accepted else None), steps
            if X.terminal:
                if X.symbol != a:
                    log('error')
                    return False, None, steps
                log(f"match {a}")
                stack.pop()
                X.attrs['lexval'] = a
                pos += 1
            else:
                cell = self.table.get((X.symbol, a))
                if not cell:
                    log('error')
                    return False, None, steps
                X.prod = cell[0]
                head, body = g.productions[X.prod]
                log(f"output {production_str(head, body)}")
                stack.pop()
                X.children = [Node(s, terminal=s not in g.nonterminals) for s in body]
                stack.extend(reversed(X.children))

    def print_table(self):
        g = self.g
        cols = g.terminals + [END]
        cell = {key: ' | '.join(production_str(*g.productions[i]) for i in idxs)
                for key, idxs in self.table.items()}
        w = max([len(v) for v in cell.values()] + [len(c) for c in cols] + [3]) + 2
        print(' ' * 3 + ''.join(c.ljust(w) for c in cols))
        for A in sorted(g.nonterminals):
            print(A.ljust(3) + ''.join(cell.get((A, c), '').ljust(w) for c in cols))
