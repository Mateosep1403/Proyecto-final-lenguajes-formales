"""Items 1 and 2.  Usage:  python3 main.py [--sets] [--tables] [--trace] < input

  --sets    print FIRST/FOLLOW sets after reading the grammar
  --tables  print the LL(1) table and the LR(0) automaton + SLR(1) table
  --trace   print the step-by-step trace of every parse (for the report)
"""
import sys

from grammar import Grammar
from input_strings import ignore_byte_order_mark, read_strings
from ll1 import LL1
from slr import SLR

PROMPT = "Select a parser (T: for LL(1), B: for SLR(1), Q: quit):"


def run_strings(parser, trace):
    for w in read_strings(sys.stdin):
        accepted, _, steps = parser.parse(w, trace=trace)
        for stack, rest, action in steps:
            print(f"  {stack:<30} {rest:<20} {action}")
        print('yes' if accepted else 'no')


def print_tables(ll1, slr):
    print("LL(1) table:" + ("" if ll1.is_valid else "  (not LL(1))"))
    ll1.print_table()
    slr.print_automaton()
    print("SLR(1) table:" + ("" if slr.is_valid else "  (has conflicts: not SLR(1))"))
    slr.print_table()


def main():
    flags = set(sys.argv[1:])
    ignore_byte_order_mark()
    n = int(sys.stdin.readline())
    g = Grammar([sys.stdin.readline() for _ in range(n)])
    if '--sets' in flags:
        g.print_sets()
    ll1, slr = LL1(g), SLR(g)
    if '--tables' in flags:
        print_tables(ll1, slr)
    trace = '--trace' in flags

    if ll1.is_valid and slr.is_valid:
        parsers = {'T': ll1, 'B': slr}
        while True:
            print(PROMPT)
            line = sys.stdin.readline()
            choice = line.strip()
            if not line or choice == 'Q':
                return
            if choice in parsers:
                run_strings(parsers[choice], trace)
    elif ll1.is_valid or slr.is_valid:
        parser = ll1 if ll1.is_valid else slr
        print(f"Grammar is {parser.name}.")
        run_strings(parser, trace)
    else:
        print("Grammar is neither LL(1) nor SLR(1).")


if __name__ == '__main__':
    main()
