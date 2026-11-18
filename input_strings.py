"""Reading of the input, shared by main.py and sdd_main.py."""

import sys

from grammar import EPS


def ignore_byte_order_mark():
    """Windows PowerShell (and Notepad) may put a UTF-8 byte order mark at the
    beginning of the text; the 'utf-8-sig' codec drops it."""
    sys.stdin.reconfigure(encoding='utf-8-sig')


def read_strings(stream):
    """Yields one string per line until an empty line (or end of input).
    The line 'e' is the empty string."""
    for line in stream:
        w = line.strip()
        if not w:
            return
        yield '' if w == EPS else w
