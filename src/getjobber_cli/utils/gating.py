"""Temporary gating for write commands.

Jobber's current GraphQL schema reworked the write surface: several mutations
the old commands used (invoiceSend, quoteSend, quoteApprove, jobComplete) no
longer exist, and the create mutations now require nested inputs (dueDetails,
tax, lineItems, propertyId) that the current commands don't collect. Rather than
fail with cryptic GraphQL errors, write commands short-circuit with a clear
message until the write redesign lands (v1.2.0).

Read commands (list / get / search) are fully supported on the current schema.
"""

import functools

import typer

from getjobber_cli.utils.formatters import print_error

_MESSAGE = (
    "This write command is temporarily disabled: Jobber's current API schema "
    "reworked the write operations, and the command needs a redesign (planned "
    "for v1.2.0). Read commands — list, get, search — are fully supported."
)


def write_command_pending(func):
    """Short-circuit a write command until the v1.2.0 write redesign.

    Preserves the wrapped function's signature so `--help` still renders the
    command's options; the wrapper ignores any passed arguments.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print_error(_MESSAGE)
        raise typer.Exit(2)

    return wrapper
