"""Item 3.  Usage:  python3 sdd_main.py [--slr] [--show] [--circular] < strings

Strings are read one per line until an empty line (the empty string is 'e').
  --slr       parse with the SLR(1) parser instead of the LL(1) parser
  --show      print the attribute table and the semantic rules first
  --circular  use a deliberately circular variant of the SDD (Step 6)
"""
import sys

import sdd_def
from grammar import Grammar
from ll1 import LL1
from slr import SLR
from sdd import number_nodes, evaluate, print_tree, print_order, print_sdd, vname


def main():
    flags = set(sys.argv[1:])
    g = Grammar(sdd_def.GRAMMAR_LINES)
    use_slr = '--slr' in flags
    parser = SLR(g) if use_slr else LL1(g)
    if not (parser.is_slr if use_slr else parser.is_ll1):
        print(f"The grammar of the SDD is not {'SLR(1)' if use_slr else 'LL(1)'}.")
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

    main_sym, main_attr = sdd.main
    for line in sys.stdin:
        w = line.strip()
        if w == '':
            break
        if w == 'e':
            w = ''
        ok, root, _ = parser.parse(w)
        if not ok:
            print('no')
            continue
        number_nodes(root)
        result = evaluate(root, g, sdd)
        if result['cycle']:
            nodes = result['nodes']
            print("The SDD is circular. Cycle in the dependency graph:")
            print("  " + " -> ".join(vname(nodes, v) for v in result['cycle']))
            return
        print("Annotated parse tree:")
        print_tree(root, g)
        print("Evaluation order:")
        print_order(result)
        print(f"{main_sym}.{main_attr} = {root.attrs[main_attr]}")


if __name__ == '__main__':
    main()