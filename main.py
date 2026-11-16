"""Items 1 and 2.  Usage:  python3 main.py [--sets] [--tables] [--trace] < input

  --sets    print FIRST/FOLLOW sets after reading the grammar
  --tables  print the LL(1) table and the LR(0) automaton + SLR(1) table
  --trace   print the step-by-step trace of every parse (for the report)
"""
import sys

from grammar import Grammar
from ll1 import LL1
from slr import SLR

PROMPT = "Select a parser (T: for LL(1), B: for SLR(1), Q: quit):"


def run_strings(parser, lines, trace):
    """Read strings until an empty line (or EOF); print yes/no for each."""
    while lines:
        w = lines.pop(0).strip()
        if w == '':
            return
        if w == 'e':
            w = ''
        ok, _, steps = parser.parse(w, trace=trace)
        if trace:
            for stk, inp, act in steps:
                print(f"  {stk:<30} {inp:<20} {act}")
        print('yes' if ok else 'no')


def main():
    flags = set(sys.argv[1:])
    lines = [l.rstrip('\r\n') for l in sys.stdin.read().split('\n')]
    n = int(lines.pop(0).strip())
    g = Grammar([lines.pop(0).strip() for _ in range(n)])
    if '--sets' in flags:
        g.print_sets()
    ll, slr = LL1(g), SLR(g)
    trace = '--trace' in flags
    if '--tables' in flags:
        print("LL(1) table:" + ("" if ll.is_ll1 else "  (has conflicts: not LL(1))"))
        ll.print_table()
        slr.print_automaton()
        print("SLR(1) table:" + ("" if slr.is_slr else "  (has conflicts: not SLR(1))"))
        slr.print_table()

    if ll.is_ll1 and slr.is_slr:
        while True:
            print(PROMPT)
            if not lines:
                break
            c = lines.pop(0).strip().upper()
            if c == 'Q':
                break
            if c == 'T':
                run_strings(ll, lines, trace)
            elif c == 'B':
                run_strings(slr, lines, trace)
    elif ll.is_ll1:
        print("Grammar is LL(1).")
        run_strings(ll, lines, trace)
    elif slr.is_slr:
        print("Grammar is SLR(1).")
        run_strings(slr, lines, trace)
    else:
        print("Grammar is neither LL(1) nor SLR(1).")


if __name__ == '__main__':
    main()