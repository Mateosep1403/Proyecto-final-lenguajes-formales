"""The SDD of Item 3, written as DATA (grammar + attributes + rules).

Language: nested lists of digits, e.g.  1,[2,3],4   or   [[7]]
Grammar (LL(1) and SLR(1)):
    S -> L
    L -> E M
    M -> , E M | e
    E -> D | [ L ]
    D -> 0 | 1 | ... | 9

Attributes
    d  (inherited)    depth of the list the symbol is in; top level = 1
    s  (synthesized)  sum of every digit multiplied by the depth where it appears
    h  (synthesized)  maximum depth found in the subtree
    val(synthesized)  numeric value of a digit
Main attribute: S.s
"""
from sdd import SDD, Rule

GRAMMAR_LINES = [
    "S -> L",
    "L -> EM",
    "M -> ,EM e",
    "E -> D [L]",
    "D -> 0 1 2 3 4 5 6 7 8 9",
]

ATTRS = {
    'S': {'syn': ['s', 'h'], 'inh': []},
    'L': {'syn': ['s', 'h'], 'inh': ['d']},
    'M': {'syn': ['s', 'h'], 'inh': ['d']},
    'E': {'syn': ['s', 'h'], 'inh': ['d']},
    'D': {'syn': ['val'], 'inh': []},
}


def make_sdd(circular=False):
    """circular=True replaces one rule so that the SDD becomes circular
    (used only to show that the evaluator detects cycles, Step 6)."""
    copy = lambda x: x
    add = lambda a, b: a + b
    rules = {}

    # S -> L
    if circular:
        l_d = Rule((1, 'd'), [(1, 's')], copy, "L.d = L.s          <-- circular on purpose")
    else:
        l_d = Rule((1, 'd'), [], lambda: 1, "L.d = 1")
    rules[('S', ('L',))] = [
        l_d,
        Rule((0, 's'), [(1, 's')], copy, "S.s = L.s"),
        Rule((0, 'h'), [(1, 'h')], copy, "S.h = L.h"),
    ]

    # L -> E M
    rules[('L', ('E', 'M'))] = [
        Rule((1, 'd'), [(0, 'd')], copy, "E.d = L.d"),
        Rule((2, 'd'), [(0, 'd')], copy, "M.d = L.d"),
        Rule((0, 's'), [(1, 's'), (2, 's')], add, "L.s = E.s + M.s"),
        Rule((0, 'h'), [(1, 'h'), (2, 'h')], max, "L.h = max(E.h, M.h)"),
    ]

    # M -> , E M1
    rules[('M', (',', 'E', 'M'))] = [
        Rule((2, 'd'), [(0, 'd')], copy, "E.d = M.d"),
        Rule((3, 'd'), [(0, 'd')], copy, "M1.d = M.d"),
        Rule((0, 's'), [(2, 's'), (3, 's')], add, "M.s = E.s + M1.s"),
        Rule((0, 'h'), [(2, 'h'), (3, 'h')], max, "M.h = max(E.h, M1.h)"),
    ]

    # M -> e
    rules[('M', ())] = [
        Rule((0, 's'), [], lambda: 0, "M.s = 0"),
        Rule((0, 'h'), [(0, 'd')], copy, "M.h = M.d"),
    ]

    # E -> D
    rules[('E', ('D',))] = [
        Rule((0, 's'), [(1, 'val'), (0, 'd')], lambda v, d: v * d, "E.s = D.val * E.d"),
        Rule((0, 'h'), [(0, 'd')], copy, "E.h = E.d"),
    ]

    # E -> [ L ]
    rules[('E', ('[', 'L', ']'))] = [
        Rule((2, 'd'), [(0, 'd')], lambda d: d + 1, "L.d = E.d + 1"),
        Rule((0, 's'), [(2, 's')], copy, "E.s = L.s"),
        Rule((0, 'h'), [(2, 'h')], copy, "E.h = L.h"),
    ]

    # D -> digit
    for c in "0123456789":
        rules[('D', (c,))] = [
            Rule((0, 'val'), [(1, 'lexval')], int, f"D.val = int({c}.lexval)"),
        ]

    return SDD(ATTRS, rules, main=('S', 's'))