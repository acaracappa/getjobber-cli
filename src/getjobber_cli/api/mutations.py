"""Pre-built GraphQL mutations for GetJobber API."""

# Client Mutations
CREATE_CLIENT = """
mutation CreateClient($input: ClientCreateInput!) {
  clientCreate(input: $input) {
    client {
      id
      firstName
      lastName
      companyName
      email
      phone
      isCompany
      createdAt
    }
    userErrors {
      message
      path
    }
  }
}
"""

# Edits are differential: emails and phones are added, edited by their own id,
# or deleted, rather than assigned. See docs/write-redesign.md.
UPDATE_CLIENT = """
mutation EditClient($clientId: EncodedId!, $input: ClientEditInput!) {
  clientEdit(clientId: $clientId, input: $input) {
    client {
      id
      firstName
      lastName
      companyName
      email
      phone
      isCompany
      updatedAt
    }
    userErrors {
      message
      path
    }
  }
}
"""

# Jobber has no client delete; archiving is the only removal, and is reversible
# with clientUnarchive.
ARCHIVE_CLIENT = """
mutation ArchiveClient($clientId: EncodedId!) {
  clientArchive(clientId: $clientId) {
    client {
      id
      firstName
      lastName
      companyName
    }
    userErrors {
      message
      path
    }
  }
}
"""

# Job Mutations
CREATE_JOB = """
mutation CreateJob($input: JobCreateAttributes!) {
  jobCreate(input: $input) {
    job {
      id
      title
      jobNumber
      jobStatus
      client {
        id
        firstName
        lastName
        companyName
      }
      createdAt
    }
    userErrors {
      message
      path
    }
  }
}
"""

UPDATE_JOB = """
mutation EditJob($jobId: EncodedId!, $input: JobEditInput!) {
  jobEdit(jobId: $jobId, input: $input) {
    job {
      id
      title
      jobNumber
      jobStatus
      updatedAt
    }
    userErrors {
      message
      path
    }
  }
}
"""

# jobComplete no longer exists. jobClose is the replacement, and it requires an
# explicit decision about visits that have not happened yet.
CLOSE_JOB = """
mutation CloseJob($jobId: EncodedId!, $input: JobCloseInput!) {
  jobClose(jobId: $jobId, input: $input) {
    job {
      id
      title
      jobStatus
      completedAt
    }
    userErrors {
      message
      path
    }
  }
}
"""

# Quote Mutations
CREATE_QUOTE = """
mutation CreateQuote($attributes: QuoteCreateAttributes!) {
  quoteCreate(attributes: $attributes) {
    quote {
      id
      quoteNumber
      title
      quoteStatus
      client {
        id
        firstName
        lastName
        companyName
      }
      createdAt
    }
    userErrors {
      message
      path
    }
  }
}
"""

# Invoice Mutations
CREATE_INVOICE = """
mutation CreateInvoice($input: InvoiceCreateInput!) {
  invoiceCreate(input: $input) {
    invoice {
      id
      invoiceNumber
      subject
      invoiceStatus
      client {
        id
        firstName
        lastName
        companyName
      }
      createdAt
    }
    userErrors {
      message
      path
    }
  }
}
"""

UPDATE_INVOICE = """
mutation EditInvoice($invoiceId: EncodedId!, $input: InvoiceEditInput!) {
  invoiceEdit(invoiceId: $invoiceId, input: $input) {
    invoice {
      id
      invoiceNumber
      subject
      invoiceStatus
      updatedAt
    }
    userErrors {
      message
      path
    }
  }
}
"""

# invoiceSend no longer exists. invoiceMarkAsSent only flags the record; it does
# not email the client.
MARK_INVOICE_SENT = """
mutation MarkInvoiceSent($id: EncodedId!) {
  invoiceMarkAsSent(id: $id) {
    invoice {
      id
      invoiceNumber
      invoiceStatus
    }
    userErrors {
      message
      path
    }
  }
}
"""
