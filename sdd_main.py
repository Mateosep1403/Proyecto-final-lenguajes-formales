"""Item 3.  Usage:  python3 sdd_main.py [--slr] [--show] [--circular] < strings

Strings are read one per line until an empty line (the empty string is 'e').
  --slr       parse with the SLR(1) parser instead of the LL(1) parser
  --show      print the attribute table and the semantic rules first
  --circular  use a deliberately circular variant of the SDD (Step 6)
"""
import sys

import sdd_def
from grammar import Grammar
from input_strings import ignore_byte_order_mark, read_strings
from ll1 import LL1
from slr import SLR
from sdd import evaluate, print_tree, print_order, print_sdd, vertex_str


def main():
    flags = set(sys.argv[1:])
    ignore_byte_order_mark()
    g = Grammar(sdd_def.GRAMMAR_LINES)
    parser = SLR(g) if '--slr' in flags else LL1(g)
    if not parser.is_valid:
        print(f"The grammar of the SDD is not {parser.name}.")
        return
    sdd = sdd_def.make_sdd(circular='--circular' in flags)
    errors = sdd.check(g)
    if errors:
        print("The SDD is not well formed:")
        for e in errors:
            print("  " + e)
        return
    if '--show' in flags:
        print_sdd(g, sdd)

    for w in read_strings(sys.stdin):
        accepted, root, _ = parser.parse(w)
        if not accepted:
            print('no')
            continue
        ev = evaluate(root, g, sdd)
        if ev.cycle:
            print("The SDD is circular. Cycle in the dependency graph:")
            print("  " + " -> ".join(vertex_str(ev.nodes, v) for v in ev.cycle))
            return
        print("Annotated parse tree:")
        print_tree(root, g)
        print("Evaluation order:")
        print_order(ev)
        print(f"{g.start}.{sdd.main_attr} = {root.attrs[sdd.main_attr]}")


if __name__ == '__main__':
    main()
