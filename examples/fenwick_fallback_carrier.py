"""Thin shim so `python -m examples.fenwick_fallback_carrier` keeps working
from a repo checkout. The real, installed-with-the-package copy lives at
panel/demos/fenwick_fallback_carrier.py so `panel demo` works after `pip
install` too, without depending on this examples/ directory being present.
"""

from panel.demos.fenwick_fallback_carrier import main

if __name__ == "__main__":
    main()
