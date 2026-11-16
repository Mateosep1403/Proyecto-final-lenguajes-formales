"""Reading of the strings to parse, shared by main.py and sdd_main.py."""

from grammar import EPS


def read_strings(stream):
    """Yields one string per line until an empty line (or end of input).
    The line 'e' is the empty string."""
    for line in stream:
        w = line.strip()
        if not w:
            return
        yield '' if w == EPS else w
