"""Schema-shape guards for api/queries.py.

Static checks (no network) that the query constants stay on Jobber's current
schema and don't regress to fields removed in the 1.1.0 modernization.
"""

from getjobber_cli.api import queries

ALL_QUERIES = "\n".join(
    v for k, v in vars(queries).items() if isinstance(v, str) and not k.startswith("__")
)


def test_no_removed_scalar_money_or_status_fields():
    # These scalars were removed from the schema (money moved under `amounts`,
    # phone is `phone`, statuses are typed enums). None should reappear.
    for removed in ("totalAmount", "amountPaid", "phoneNumber"):
        assert removed not in ALL_QUERIES, f"removed field '{removed}' is back in queries.py"


def test_invoice_uses_current_shape():
    assert "invoiceStatus" in queries.LIST_INVOICES
    assert "amounts" in queries.LIST_INVOICES and "invoiceBalance" in queries.GET_INVOICE
    assert "issuedDate" in queries.LIST_INVOICES


def test_status_filters_are_typed_enums():
    assert "InvoiceStatusTypeEnum" in queries.LIST_INVOICES
    assert "QuoteStatusTypeEnum" in queries.LIST_QUOTES
    assert "JobStatusTypeEnum" in queries.LIST_JOBS


def test_id_args_use_encoded_id():
    # Single-record lookups take EncodedId, not the old ID! type.
    for q in (queries.GET_INVOICE, queries.GET_QUOTE, queries.GET_JOB, queries.GET_CLIENT):
        assert "EncodedId!" in q
