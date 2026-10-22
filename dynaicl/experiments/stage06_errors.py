"""Stage 0.6 runner outcome taxonomy (v2 freeze).

* :class:`Refusal`: a policy or guard failure (exit code 3, printed as ``REFUSED``): wrong hash, wrong seeds, missing or stale
  authorization, incompatible schema, unqualified environment, a second run, ...
* :class:`Corrupt`: an integrity failure of data the runner reads (exit code 4, printed as ``CORRUPT``): an empty, truncated or
  damaged file, a checksum mismatch, a field missing or of the wrong type, a unit that does not match its file name.

Every instance names the offending path (when there is one) and the reason. Neither is a catch-all: callers raise them at the
specific check that failed, and unrelated exceptions are never converted.
"""

from __future__ import annotations


class Refusal(RuntimeError):
    exit_code = 3
    label = "REFUSED"

    def __init__(self, reason: str, path=None):
        self.reason, self.path = reason, (str(path) if path is not None else None)
        super().__init__(f"{self.path}: {reason}" if self.path else reason)


class Corrupt(Refusal):
    exit_code = 4
    label = "CORRUPT"
