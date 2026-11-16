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


def production_str(head, body):
    return f"{head} -> {''.join(body) or EPS}"


class Grammar:
    def __init__(self, lines):
        # productions: list of (head, body) where body is a tuple of symbols
        # (the empty tuple is the epsilon production).
        self.productions = []
        for line in lines:
            head, _arrow, *alternatives = line.split()
            for alt in alternatives:
                self.productions.append((head, () if alt == EPS else tuple(alt)))
        self.start = 'S'
        self.nonterminals = {head for head, _ in self.productions}
        self.terminals = sorted({s for _, body in self.productions
                                 for s in body if s not in self.nonterminals})
        self._compute_first()
        self._compute_follow()

    def productions_of(self, A):
        """(index, body) of every production with head A."""
        return [(i, body) for i, (head, body) in enumerate(self.productions) if head == A]

    def tokens(self, w):
        """The input w followed by the end marker, or None if w has a symbol
        that is not a terminal of the grammar (such a string is rejected)."""
        if any(c not in self.terminals for c in w):
            return None
        return list(w) + [END]

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
        for A in self.nonterminals:
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
        self.follow = {A: set() for A in self.nonterminals}
        self.follow[self.start].add(END)
        changed = True
        while changed:
            changed = False
            for A, body in self.productions:
                for i, B in enumerate(body):
                    if B not in self.nonterminals:
                        continue
                    f = self.first_of_string(body[i + 1:])
                    new = f - {EPS}
                    if EPS in f:
                        new |= self.follow[A]
                    if not new <= self.follow[B]:
                        self.follow[B] |= new
                        changed = True

    def print_sets(self):
        for A in sorted(self.nonterminals):
            print(f"First({A}) = {fmt_set(self.first[A])}")
        for A in sorted(self.nonterminals):
            print(f"Follow({A}) = {fmt_set(self.follow[A])}")
