"""Errors that map to the CLI's exit codes."""

from __future__ import annotations

OK = 0
VALIDATION = 1  # bad input, unknown model, rejected key
USAGE = 2  # argparse
REFUSED = 3  # a safety rule said no
FAILED = 4  # failed, nothing changed
PARTIAL = 5  # failed after a partial change


class OwhError(Exception):
    code = FAILED


class ValidationError(OwhError):
    code = VALIDATION


class Refused(OwhError):
    code = REFUSED


class Failed(OwhError):
    code = FAILED


class PartialFailure(OwhError):
    code = PARTIAL
