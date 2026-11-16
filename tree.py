"""Parse tree node shared by both parsers and the SDD evaluator."""


class Node:
    def __init__(self, symbol, terminal=False):
        self.symbol = symbol      # grammar symbol
        self.terminal = terminal  # True for leaves that are terminals
        self.prod = None          # index into Grammar.productions (nonterminals only)
        self.children = []
        self.attrs = {}           # attribute name -> value
        self.id = None            # assigned by sdd.number_nodes