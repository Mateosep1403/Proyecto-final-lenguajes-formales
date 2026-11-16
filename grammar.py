"""Grammar reading and FIRST/FOLLOW sets (Aho et al., Section 4.4.2)."""

EPS = 'e'
END = '$'


def fmt_set(s):
    """Terminals in ASCII order, then e, then $."""
    items = sorted(x for x in s if x not in (EPS, END))
    if EPS in s:
        items.append(EPS)
    if END in s:
        items.append(END)
    return '{' + ', '.join(items) + '}'


class Grammar:
    def __init__(self, lines):
        # productions: list of (head, body) where body is a tuple of symbols
        # (the empty tuple is the epsilon production).
        self.productions = []
        self.nonterminals = []
        for line in lines:
            head, _, rhs = line.partition('->')
            head = head.strip()
            self.nonterminals.append(head)
            for alt in rhs.split():
                body = () if alt == EPS else tuple(alt)
                self.productions.append((head, body))
        self.start = 'S'
        self.nt_set = set(self.nonterminals)
        self.terminals = sorted({s for _, b in self.productions
                                 for s in b if s not in self.nt_set})
        self._compute_first()
        self._compute_follow()

    # ---- FIRST ----------------------------------------------------------
    def first_of_string(self, symbols):
        """FIRST(X1 X2 ... Xn); contains EPS iff every Xi is nullable."""
        result = set()
        for X in symbols:
            fx = self.first[X]
            result |= fx - {EPS}
            if EPS not in fx:
                return result
        result.add(EPS)
        return result

    def _compute_first(self):
        self.first = {a: {a} for a in self.terminals}
        for A in self.nt_set:
            self.first[A] = set()
        changed = True
        while changed:
            changed = False
            for A, body in self.productions:
                new = self.first_of_string(body)
                if not new <= self.first[A]:
                    self.first[A] |= new
                    changed = True

    # ---- FOLLOW ---------------------------------------------------------
    def _compute_follow(self):
        self.follow = {A: set() for A in self.nt_set}
        self.follow[self.start].add(END)
        changed = True
        while changed:
            changed = False
            for A, body in self.productions:
                for i, B in enumerate(body):
                    if B not in self.nt_set:
                        continue
                    f = self.first_of_string(body[i + 1:])
                    new = f - {EPS}
                    if EPS in f:
                        new |= self.follow[A]
                    if not new <= self.follow[B]:
                        self.follow[B] |= new
                        changed = True

    def print_sets(self):
        for A in sorted(self.nt_set):
            print(f"First({A}) = {fmt_set(self.first[A])}")
        for A in sorted(self.nt_set):
            print(f"Follow({A}) = {fmt_set(self.follow[A])}")