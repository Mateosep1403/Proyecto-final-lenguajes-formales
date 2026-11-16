# Formal Languages Project: FIRST/FOLLOW, LL(1), SLR(1) and SDD evaluation

## Group members

- Mateo Sepúlveda Escobar
- TODO: full name of Isabella

## Environment

- Operating system: Windows 11 Pro (build 26200)
- Programming language: Python 3.14.3 (any Python 3.8 or newer works)
- Tools: none (only the Python standard library; no parser generators or parsing libraries)

On Windows use `python` instead of `python3` in the commands below.

## Files

| File | Content | Book |
| --- | --- | --- |
| `grammar.py` | Grammar reading, FIRST and FOLLOW sets | Section 4.4.2 |
| `ll1.py` | LL(1) test (definition), predictive parsing table, table-driven predictive parser | Section 4.4.3, Alg. 4.31; Section 4.4.4, Alg. 4.34 |
| `slr.py` | LR(0) items, CLOSURE/GOTO, canonical collection, SLR(1) ACTION/GOTO tables, LR parser | Section 4.6.2; Alg. 4.46; Section 4.6.3, Alg. 4.44 |
| `tree.py` | Parse tree node | |
| `input_strings.py` | Reading of the strings to parse (shared by both programs) | |
| `main.py` | Items 1 and 2 (input/output of Section 2.2 of the statement) | |
| `sdd.py` | Generic SDD evaluator: dependency graph, topological order, cycle detection | Sections 5.1, 5.2.1, 5.2.2 |
| `sdd_def.py` | Our grammar and our SDD, written as data (Item 3) | |
| `sdd_main.py` | Item 3 program | |
| `tests/test_project.py` | Automated tests | |
| `report.pdf` | Report (Item 4) | |
| `report/report.tex` | LaTeX source of the report | |

## How to run

No build step is needed.

### Items 1 and 2

```
python3 main.py [--sets] [--tables] [--trace] < input.txt
```

- `--sets`: print FIRST and FOLLOW after reading the grammar.
- `--tables`: print the LL(1) table and the LR(0) automaton with the SLR(1) table.
- `--trace`: print the step-by-step trace of each parse.

Without `--tables` and `--trace` the output is exactly the one of Section 2.2.2 of the statement.
The program can also be used interactively (type the grammar and the strings).

Example:

```
printf '3\nS -> S+T T\nT -> T*F F\nF -> (S) i\ni+i\n(i)\n(i+i)*i)\n\n' | python3 main.py
```

### Item 3

```
python3 sdd_main.py [--slr] [--show] [--circular] < strings.txt
```

Strings are read one per line until an empty line (`e` is the empty string).
The grammar and the SDD are in `sdd_def.py`.

- `--slr`: parse with the SLR(1) parser (default: LL(1)).
- `--show`: print the attribute table and the semantic rules.
- `--circular`: use a deliberately circular variant of the SDD, to show cycle detection.

Example:

```
printf '1,[2,3],4\n\n' | python3 sdd_main.py
```

### Tests

From the project root:

```
python3 -m unittest tests.test_project -v
```

They check the examples of the statement, edge cases, Item 3, and compare both
parsers against an independent recognizer (Earley) on hundreds of random grammars.

## Note on the LL(1) test

The LL(1) test implements the definition at the beginning of Section 4.4.3
(for every pair of alternatives `A -> α | β`). It agrees with "the predictive
table has no multiply-defined entry" whenever every nonterminal is reachable
from `S`. For an unreachable nonterminal with two nullable alternatives
(e.g. `S -> a e`, `B -> S e`), FOLLOW(B) is empty, so the table has no
conflict, but the definition (at most one alternative derives ε) fails:
our program reports that grammar as SLR(1) only.

## Generative AI usage

TODO: describe what Mateo used AI for when writing the first version.

We used Claude (Anthropic), through Claude Code, to review the code against
the statement, find bugs (unimportable file names, quadratic LL(1) parsing,
recursion limit on deep trees, LL(1) test not following the definition, input
read all at once) and refactor it, and to write the automated tests. We also
used it to draft the text of the report and to generate its tables and traces
from the output of our programs.

TODO (only if true before submitting): the hand-worked example of Item 3
(Step 3) was done by us, by hand.

TODO (only if true before submitting): every member of the group read the
changes, traced the algorithms by hand, and can explain and modify the code.
