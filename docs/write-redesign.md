# Write command redesign (v1.3.0)

Write commands were gated from v1.1.0 because Jobber's current schema reworked
the write surface. This records what the schema actually offers, verified by
introspecting the live API on 2026-09-24 at version `2026-05-12`, and the
decisions taken for each command.

**Status: complete.** Every write command is rebuilt or removed, and the gate
(`utils/gating.py`) has been deleted.

## Summary

| CLI command | v1.0 mutation | Now | Action |
|---|---|---|---|
| `clients create` | `clientCreate` | exists, input renamed | rebuilt |
| `clients update` | `clientUpdate` | `clientEdit`, different shape | rebuilt |
| `clients delete` | `clientArchive` | exists, arg renamed | renamed `clients archive` |
| `jobs create` | `jobCreate` | exists, new required inputs | rebuilt |
| `jobs update` | `jobEdit` | exists | rebuilt |
| `jobs complete` | `jobComplete` | **gone** → `jobClose` | renamed `jobs close` |
| `quotes create` | `quoteCreate` | exists, new required inputs | rebuilt |
| `quotes send` | `quoteSend` | **gone, no equivalent** | removed |
| `quotes approve` | `quoteApprove` | **gone, no equivalent** | removed |
| `invoices create` | `invoiceCreate` | exists, new required inputs | rebuilt |
| `invoices send` | `invoiceSend` | **gone** → `invoiceMarkAsSent` | renamed `invoices mark-sent` |

## Commands being removed

`quotes send` and `quotes approve` have no replacement. Searching all 109
mutations exposed by the schema for anything matching send / approve / deliver /
email / message / submit returns an empty set — Jobber no longer exposes any
API-driven delivery or approval, for quotes or anything else. These operations
have to be done in the Jobber web app, so the CLI stops advertising them rather
than shipping commands that can never succeed.

## Commands being renamed

Two operations survive only under different semantics, so the names change to
match what actually happens:

- **`clients delete` → `clients archive`.** The only mutation is
  `clientArchive`. Nothing is deleted; the client is archived and can be
  restored with `clientUnarchive`. A command named `delete` that archives is a
  trap.
- **`invoices send` → `invoices mark-sent`.** The only mutation is
  `invoiceMarkAsSent`, which flags the invoice as sent **without emailing
  anyone**. A `send` that sends nothing is worse than no command at all.
- **`jobs complete` → `jobs close`.** The mutation is `jobClose`, and it
  requires deciding what happens to incomplete visits (see below).

## Newly required inputs

The create mutations now demand structure the old commands never collected.

### `clientCreate(input: ClientCreateInput!)`
No required fields. Emails and phones are lists of objects, not scalars — the
old command sent `email` and `phoneNumber` strings, which the schema does not
accept:

```graphql
emails: [{ address: String, primary: Boolean, description: EmailDescription }]
phones: [{ number: String, primary: Boolean, smsAllowed: Boolean }]
```

### `clientEdit(clientId: EncodedId!, input: ClientEditInput!)`
Edits are differential, not declarative. There is no `emails` field; instead
`emailsToAdd`, `emailsToEdit` (each requiring the email's own `id`) and
`emailsToDelete`. Same for phones, contacts, properties and tags. Setting an
email on a client that already has one is an *edit*, not an add, so the command
must read the current value before deciding.

### `jobCreate(input: JobCreateAttributes!)`
Required: `propertyId: EncodedId!` and
`invoicing: { invoicingType: BillingStrategy!, invoicingSchedule: BillingFrequencyEnum! }`.

- `BillingStrategy`: `FIXED_PRICE`, `VISIT_BASED`
- `BillingFrequencyEnum`: `ON_COMPLETION`, `PERIODIC`, `PER_VISIT`, `NEVER`

A job belongs to a property, not directly to a client, so the command needs a
property — obtainable from the client's `properties`.

### `quoteCreate(attributes: QuoteCreateAttributes!)`
Required: `clientId`, `propertyId`, and a non-empty `lineItems` list.

### `invoiceCreate(input: InvoiceCreateInput!)`
Required: `clientId`, `dueDetails`, `tax: { taxCalculationMethod: TaxCalculationMethodType! }`
(`EXCLUSIVE` or `INCLUSIVE`), and a non-empty `lineItems` list where each item
requires at least `name`.

### `jobClose(jobId: EncodedId!, input: JobCloseInput!)`
Required: `modifyIncompleteVisitsBy: IncompleteVisitDecisionEnum!` —
`DESTROY_ALL` or `COMPLETE_PAST_DESTROY_FUTURE`. There is no default; closing a
job forces a decision about outstanding visits, which the CLI must surface
rather than choose silently.

## Verification policy

Write commands are covered by unit tests against a mocked transport. They are
not exercised against a live Jobber account during development, because doing so
creates real records in a real business's data. Live verification is a
deliberate, human-run step before release.
