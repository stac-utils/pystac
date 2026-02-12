import os
import sys

for _p in sys.path:
    _candidate = os.path.join(_p, "pystac", "extensions")
    if os.path.isdir(_candidate) and _candidate not in __path__:
        __path__.append(_candidate)
