# Formal Languages Project: FIRST/FOLLOW, LL(1), SLR(1) and SDD evaluation

## Group members

- Mateo Sepúlveda Escobar
- Isabella Hernandez

## Environment

Fill in the versions you actually used (run `python3 --version` and check your OS):

- Operating system: <e.g. Ubuntu 24.04 / Windows 11 / macOS 15>
- Programming language: Python <3.x.y>
- Tools: none (only the Python standard library; no parser generators or parsing libraries)

## Files

| File | Content |
| --- | --- |
| `grammar.py` | Grammar reading, FIRST and FOLLOW sets (book, Section 4.4.2) |
| `ll1.py` | LL(1) table (Alg. 4.31) and table-driven predictive parser (Section 4.4.4) |
| `slr.py` | LR(0) items, CLOSURE/GOTO, canonical collection (Section 4.6.2), ACTION/GOTO tables (Alg. 4.46), LR parser (Section 4.6.3) |
| `tree.py` | Parse tree node |
| `main.py` | Items 1 and 2 (input/output of Section 2.2 of the statement) |
| `sdd.py` | Generic SDD evaluator: dependency graph, topological order, cycle detection (Sections 5.1 and 5.2) |
| `sdd_def.py` | Our grammar and our SDD, written as data (Item 3) |
| `sdd_main.py` | Item 3 program |

## How to run

No build step is needed. Python 3.8 or newer.

### Items 1 and 2

```
python3 main.py [--sets] [--tables] [--trace] < input.txt
```

- `--sets`: print FIRST and FOLLOW after reading the grammar.
- `--tables`: print the LL(1) table and the LR(0) automaton with the SLR(1) table.
- `--trace`: print the step-by-step trace of each parse.

Example:

```
printf '3\nS -> S+T T\nT -> T*F F\nF -> (S) i\ni+i\n(i)\n(i+i)*i)\n\n' | python3 main.py
```

### Item 3

```
python3 sdd_main.py [--slr] [--show] [--circular] < strings.txt
```

Strings are read one per line until an empty line (`e` is the empty string).

- `--slr`: parse with the SLR(1) parser (default: LL(1)).
- `--show`: print the attribute table and the semantic rules.
- `--circular`: use a deliberately circular variant of the SDD, to show cycle detection.

Example:

```
printf '1,[2,3],4\n\n' | python3 sdd_main.py
```

## Generative AI usage

<Edit this section so that it is true for your group.> We used Claude (Anthropic) as a support tool to
<describe exactly what: e.g. generate a first version of the code, which we then read, traced by hand
and tested; clarify concepts of Sections 4.4-4.6 and 5.1-5.2>. We did not use AI to replace reading the book or
the hand-worked examples, and every member of the group can explain and modify the code.