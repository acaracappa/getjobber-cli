"""Pre-built GraphQL mutations for GetJobber API."""

# Client Mutations
CREATE_CLIENT = """
mutation CreateClient($input: ClientInput!) {
  clientCreate(input: $input) {
    client {
      id
      firstName
      lastName
      companyName
      email
      phoneNumber
      createdAt
    }
    userErrors {
      message
      path
    }
  }
}
"""

UPDATE_CLIENT = """
mutation UpdateClient($id: ID!, $input: ClientInput!) {
  clientUpdate(id: $id, input: $input) {
    client {
      id
      firstName
      lastName
      companyName
      email
      phoneNumber
      updatedAt
    }
    userErrors {
      message
      path
    }
  }
}
"""

DELETE_CLIENT = """
mutation DeleteClient($id: ID!) {
  clientArchive(id: $id) {
    client {
      id
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
mutation CreateJob($input: JobInput!) {
  jobCreate(input: $input) {
    job {
      id
      title
      jobNumber
      status
      client {
        id
        firstName
        lastName
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
mutation UpdateJob($id: ID!, $input: JobInput!) {
  jobUpdate(id: $id, input: $input) {
    job {
      id
      title
      jobNumber
      status
      updatedAt
    }
    userErrors {
      message
      path
    }
  }
}
"""

COMPLETE_JOB = """
mutation CompleteJob($id: ID!) {
  jobComplete(id: $id) {
    job {
      id
      title
      status
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
mutation CreateQuote($input: QuoteInput!) {
  quoteCreate(input: $input) {
    quote {
      id
      quoteNumber
      title
      status
      client {
        id
        firstName
        lastName
      }
      totalAmount
      createdAt
    }
    userErrors {
      message
      path
    }
  }
}
"""

UPDATE_QUOTE = """
mutation UpdateQuote($id: ID!, $input: QuoteInput!) {
  quoteUpdate(id: $id, input: $input) {
    quote {
      id
      quoteNumber
      title
      status
      updatedAt
    }
    userErrors {
      message
      path
    }
  }
}
"""

SEND_QUOTE = """
mutation SendQuote($id: ID!) {
  quoteSend(id: $id) {
    quote {
      id
      quoteNumber
      status
      sentAt
    }
    userErrors {
      message
      path
    }
  }
}
"""

APPROVE_QUOTE = """
mutation ApproveQuote($id: ID!) {
  quoteApprove(id: $id) {
    quote {
      id
      quoteNumber
      status
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
mutation CreateInvoice($input: InvoiceInput!) {
  invoiceCreate(input: $input) {
    invoice {
      id
      invoiceNumber
      subject
      status
      client {
        id
        firstName
        lastName
      }
      totalAmount
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
mutation UpdateInvoice($id: ID!, $input: InvoiceInput!) {
  invoiceUpdate(id: $id, input: $input) {
    invoice {
      id
      invoiceNumber
      subject
      status
      updatedAt
    }
    userErrors {
      message
      path
    }
  }
}
"""

SEND_INVOICE = """
mutation SendInvoice($id: ID!) {
  invoiceSend(id: $id) {
    invoice {
      id
      invoiceNumber
      status
      sentAt
    }
    userErrors {
      message
      path
    }
  }
}
"""
