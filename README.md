# Formal Languages Project: FIRST/FOLLOW, LL(1), SLR(1) and SDD evaluation

## Group members

- Mateo Sepúlveda Escobar
- Isabella Hernández Posada

## Environment

- Operating system: Windows 11 Pro (build 26200)
- Programming language: Python 3.14.3 (any Python 3.8 or newer works)
- Tools: none (only the Python standard library; no parser generators or parsing libraries)

## Files

| File | Content | Book |
| --- | --- | --- |
| `grammar.py` | Grammar reading, FIRST and FOLLOW sets | Section 4.4.2 |
| `ll1.py` | LL(1) test (definition), predictive parsing table, table-driven predictive parser | Section 4.4.3, Alg. 4.31; Section 4.4.4, Alg. 4.34 |
| `slr.py` | LR(0) items, CLOSURE/GOTO, canonical collection, SLR(1) ACTION/GOTO tables, LR parser | Section 4.6.2; Alg. 4.46; Section 4.6.3, Alg. 4.44 |
| `tree.py` | Parse tree node | |
| `input_strings.py` | Reading of the input (shared by both programs) | |
| `main.py` | Items 1 and 2 (input/output of Section 2.2 of the statement) | |
| `sdd.py` | Generic SDD evaluator: dependency graph, topological order, cycle detection | Sections 5.1, 5.2.1, 5.2.2 |
| `sdd_def.py` | Our grammar and our SDD, written as data (Item 3) | |
| `sdd_main.py` | Item 3 program | |
| `examples/` | Input files for the examples below | |
| `tests/test_project.py` | Automated tests | |
| `report.pdf` | Report (Item 4) | |
| `report/` | LaTeX source of the report and its figures | |

## How to run

No build step is needed. Run every command from the root folder of the project.

The programs read their input from the standard input. The way to send a file
to the standard input depends on the terminal:

| Terminal | Command |
| --- | --- |
| Windows PowerShell | `Get-Content examples\example1.txt \| python main.py` |
| Windows Command Prompt (cmd) | `python main.py < examples\example1.txt` |
| Linux / macOS / Git Bash | `python3 main.py < examples/example1.txt` |

On Windows use `python` (`python3` may open the Microsoft Store instead).
The programs can also be used interactively: run `python main.py` and type the
input; an empty line ends the strings to parse.

### Items 1 and 2

```
python main.py [--sets] [--tables] [--trace]
```

- `--sets`: print FIRST and FOLLOW after reading the grammar.
- `--tables`: print the LL(1) table and the LR(0) automaton with the SLR(1) table.
- `--trace`: print the step-by-step trace of each parse.

Without `--tables` and `--trace` the output is exactly the one of Section 2.2.2 of the statement.

Examples (PowerShell):

```
Get-Content examples\example1.txt | python main.py
Get-Content examples\example2.txt | python main.py --sets
Get-Content examples\example3.txt | python main.py
Get-Content examples\report_grammar.txt | python main.py --sets --tables --trace
```

| File | Content | Expected output |
| --- | --- | --- |
| `example1.txt` | Example 1 of the statement | `Grammar is SLR(1).` then `yes`, `yes`, `no` |
| `example2.txt` | Example 2 of the statement (chooses `T`, then `Q`) | the menu, `yes`, `yes`, `no`, the menu |
| `example3.txt` | Example 3 of the statement | `Grammar is neither LL(1) nor SLR(1).` |
| `report_grammar.txt` | The grammar of the report, with both parsers | the menu, `yes yes no no no` twice |

### Item 3

```
python sdd_main.py [--slr] [--show] [--circular]
```

Strings are read one per line until an empty line (`e` is the empty string).
The grammar and the SDD are in `sdd_def.py`.

- `--slr`: parse with the SLR(1) parser (default: LL(1)).
- `--show`: print the attribute table and the semantic rules.
- `--circular`: use a deliberately circular variant of the SDD, to show cycle detection.

Examples (PowerShell):

```
Get-Content examples\sdd_strings.txt | python sdd_main.py
Get-Content examples\sdd_strings.txt | python sdd_main.py --slr --show
Get-Content examples\sdd_strings.txt | python sdd_main.py --circular
```

For the strings of `sdd_strings.txt` the values are `S.s = 7`, `11`, `15`, `25`
and `no` for `1,,2`.

### Tests

```
python -m unittest tests.test_project -v
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

We used generative AI tools, mainly Claude (Anthropic), as support during the
whole project: to clarify concepts of the book, to write, review and debug the
code, to write the tests and to prepare the report. We reviewed, ran and tested
everything we submit.
