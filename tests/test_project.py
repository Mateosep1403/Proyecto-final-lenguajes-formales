"""Tests.  Run from the project root:  python3 -m unittest tests.test_project -v"""
import itertools
import random
import subprocess
import sys
import unittest

import sdd_def
from grammar import Grammar
from ll1 import LL1
from sdd import evaluate
from slr import SLR


def run(script, stdin, *flags):
    return subprocess.run([sys.executable, script, *flags], input=stdin,
                          capture_output=True, text=True, check=True).stdout


def earley_accepts(g, w):
    """Independent recognizer (Earley), used only as an oracle for the parsers."""
    sets = [set() for _ in range(len(w) + 1)]
    sets[0] = {(g.start, body, 0, 0) for _, body in g.productions_of(g.start)}
    for i in range(len(w) + 1):
        changed = True
        while changed:
            changed = False
            for head, body, dot, origin in list(sets[i]):
                if dot < len(body) and body[dot] in g.nonterminals:
                    new = {(body[dot], b, 0, i) for _, b in g.productions_of(body[dot])}
                elif dot == len(body):
                    new = {(h, b, d + 1, o) for h, b, d, o in sets[origin]
                           if d < len(b) and b[d] == head}
                else:
                    continue
                if not new <= sets[i]:
                    sets[i] |= new
                    changed = True
        if i < len(w):
            sets[i + 1] = {(h, b, d + 1, o) for h, b, d, o in sets[i]
                           if d < len(b) and b[d] == w[i]}
    return any(h == g.start and d == len(b) and o == 0
               for h, b, d, o in sets[len(w)])


def random_grammars(count, seed=7):
    """Random grammars over S, A, B and a, b, c whose nonterminals are all
    productive (as the statement guarantees)."""
    rnd = random.Random(seed)
    produced = 0
    while produced < count:
        lines = []
        for A in "SAB":
            alts = {"e" if n == 0 else "".join(rnd.choice("SABabc") for _ in range(n))
                    for n in (rnd.randint(0, 3) for _ in range(rnd.randint(1, 3)))}
            lines.append(f"{A} -> " + " ".join(sorted(alts)))
        g = Grammar(lines)
        productive, changed = set(), True
        while changed:
            changed = False
            for head, body in g.productions:
                if head not in productive and all(s in productive or s in g.terminals
                                                  for s in body):
                    productive.add(head)
                    changed = True
        if productive == g.nonterminals:
            produced += 1
            yield g


class StatementExamples(unittest.TestCase):
    def test_example_1(self):
        out = run('main.py', "3\nS -> S+T T\nT -> T*F F\nF -> (S) i\ni+i\n(i)\n(i+i)*i)\n\n")
        self.assertEqual(out, "Grammar is SLR(1).\nyes\nyes\nno\n")

    def test_example_2_with_sets(self):
        out = run('main.py', "3\nS -> AB\nA -> aA d\nB -> bBc e\nT\nd\nadbc\na\n\nQ\n", '--sets')
        prompt = "Select a parser (T: for LL(1), B: for SLR(1), Q: quit):\n"
        self.assertEqual(out, "First(A) = {a, d}\nFirst(B) = {b, e}\nFirst(S) = {a, d}\n"
                              "Follow(A) = {b, $}\nFollow(B) = {c, $}\nFollow(S) = {$}\n"
                              + prompt + "yes\nyes\nno\n" + prompt)

    def test_example_3(self):
        self.assertEqual(run('main.py', "1\nS -> SS a\n"),
                         "Grammar is neither LL(1) nor SLR(1).\n")


class EdgeCases(unittest.TestCase):
    def test_symbol_terminals_and_empty_string(self):
        # '-', '>' and '|' are terminals; 'e' alone is the empty string.
        out = run('main.py', "2\nS -> a-A e\nA -> >|\nT\ne\na->|\na-\n\nB\ne\na->|\n\nQ\n")
        self.assertEqual(out.split('\n')[1:4], ['yes', 'yes', 'no'])
        self.assertEqual(out.split('\n')[5:7], ['yes', 'yes'])

    def test_start_line_not_first_and_foreign_symbols(self):
        out = run('main.py', "2\nA -> b\nS -> aA\nT\nab\naxb\nAb\na$\n\nQ\n")
        self.assertEqual(out.split('\n')[1:5], ['yes', 'no', 'no', 'no'])

    def test_byte_order_mark_is_ignored(self):
        # Windows PowerShell may send a UTF-8 BOM before the piped text.
        bom = b'\xef\xbb\xbf'
        out = subprocess.run([sys.executable, 'main.py'], input=bom + b"1\nS -> S+a a\na+a\n\n",
                             capture_output=True, check=True).stdout
        self.assertEqual(out.split(), [b'Grammar', b'is', b'SLR(1).', b'yes'])
        out = subprocess.run([sys.executable, 'sdd_main.py'], input=bom + b"7\n\n",
                             capture_output=True, check=True).stdout
        self.assertTrue(out.rstrip().endswith(b"S.s = 7"))

    def test_end_of_input_without_empty_line(self):
        out = run('main.py', "1\nS -> a\nT\na")
        self.assertIn("yes", out)

    def test_slr_but_not_ll1_with_epsilon(self):
        out = run('main.py', "2\nS -> Aa\nA -> Ab e\na\nbba\nab\n\n")
        self.assertEqual(out, "Grammar is SLR(1).\nyes\nyes\nno\n")

    def test_ll1_but_not_slr(self):
        out = run('main.py', "3\nS -> AaAb BbBa\nA -> e\nB -> e\nab\nba\naa\n\n")
        self.assertEqual(out, "Grammar is LL(1).\nyes\nyes\nno\n")

    def test_long_input_is_linear(self):
        g = Grammar(["S -> aSb e"])
        n = 50_000
        self.assertTrue(LL1(g).parse('a' * n + 'b' * n)[0])
        self.assertTrue(SLR(g).parse('a' * n + 'b' * n)[0])


class RandomGrammars(unittest.TestCase):
    def test_ll1_definition_vs_table_without_conflicts(self):
        # They coincide when every FOLLOW set is non-empty (all nonterminals
        # reachable).  For an unreachable A with two nullable alternatives,
        # FOLLOW(A) is empty: the table has no conflict, but the definition
        # (condition 2) says the grammar is not LL(1).
        for g in random_grammars(500):
            ll1 = LL1(g)
            no_conflicts = all(len(cell) == 1 for cell in ll1.table.values())
            if ll1.is_valid:
                self.assertTrue(no_conflicts, g.productions)
            if all(g.follow.values()):
                self.assertEqual(ll1.is_valid, no_conflicts, g.productions)

    def test_unreachable_nonterminal_with_two_nullable_alternatives(self):
        g = Grammar(["S -> a e", "B -> S e"])
        self.assertFalse(LL1(g).is_valid)
        self.assertTrue(SLR(g).is_valid)

    def test_parsers_agree_with_earley(self):
        for g in random_grammars(300):
            parsers = [p for p in (LL1(g), SLR(g)) if p.is_valid]
            for n in range(5):
                for w in map(''.join, itertools.product("abc", repeat=n)):
                    expected = earley_accepts(g, w)
                    for p in parsers:
                        self.assertEqual(p.parse(w)[0], expected, (p.name, g.productions, w))


class SDDEvaluation(unittest.TestCase):
    def setUp(self):
        self.g = Grammar(sdd_def.GRAMMAR_LINES)
        self.sdd = sdd_def.make_sdd()

    def value(self, parser, w):
        accepted, root, _ = parser.parse(w)
        if not accepted:
            return None
        ev = evaluate(root, self.g, self.sdd)
        self.assertIsNone(ev.cycle)
        return root.attrs['s']

    def test_sdd_is_well_formed(self):
        self.assertEqual(self.sdd.check(self.g), [])

    def test_values_with_both_parsers(self):
        cases = {'7': 7, '1,[2,3],4': 15, '[[[[5]]]]': 25, '[1,[2]],3': 11,
                 '1,,2': None, '': None, '[1': None}
        for parser in (LL1(self.g), SLR(self.g)):
            for w, expected in cases.items():
                self.assertEqual(self.value(parser, w), expected, (parser.name, w))

    def test_deep_nesting(self):
        depth = 2000
        self.assertEqual(self.value(LL1(self.g), '[' * depth + '1' + ']' * depth), depth + 1)

    def test_circular_variant_is_detected(self):
        g = self.g
        _, root, _ = LL1(g).parse('1,2')
        ev = evaluate(root, g, sdd_def.make_sdd(circular=True))
        self.assertIsNotNone(ev.cycle)
        self.assertEqual(ev.cycle[0], ev.cycle[-1])

    def test_program_output(self):
        out = run('sdd_main.py', "1,[2,3],4\n1,,2\n\n")
        self.assertTrue(out.startswith("Annotated parse tree:\nS#1 [S -> L] {s=15}\n"))
        self.assertIn("Evaluation order:\n", out)
        self.assertTrue(out.endswith("S.s = 15\nno\n"))
        circular = run('sdd_main.py', "1,2\n\n", '--circular')
        self.assertTrue(circular.startswith("The SDD is circular."))


if __name__ == '__main__':
    unittest.main()
