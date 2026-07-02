"""Pre-built GraphQL queries for GetJobber API.

Field selections target the pinned schema version in api/client.py
(X-JOBBER-GRAPHQL-VERSION). Money now lives under `amounts { ... }`, statuses
are typed enums (invoiceStatus / quoteStatus / jobStatus), and related records
are connections (jobs.nodes, properties.nodes) rather than the old *Ids / *Amount
scalar fields. See CHANGELOG 1.1.0.
"""

# Client Queries
LIST_CLIENTS = """
query ListClients($first: Int, $after: String) {
  clients(first: $first, after: $after) {
    nodes {
      id
      firstName
      lastName
      companyName
      email
      phone
      isCompany
      isLead
      createdAt
      updatedAt
    }
    pageInfo {
      hasNextPage
      endCursor
    }
    totalCount
  }
}
"""

GET_CLIENT = """
query GetClient($id: EncodedId!) {
  client(id: $id) {
    id
    firstName
    lastName
    companyName
    email
    phone
    phones { number primary smsAllowed }
    billingAddress {
      street1
      street2
      city
      province
      postalCode
      country
    }
    isCompany
    isLead
    tags {
      nodes {
        label
      }
    }
    createdAt
    updatedAt
  }
}
"""

SEARCH_CLIENTS = """
query SearchClients($query: String!, $first: Int) {
  clients(first: $first, searchTerm: $query) {
    nodes {
      id
      firstName
      lastName
      companyName
      email
      phone
    }
    totalCount
  }
}
"""

# Job Queries
LIST_JOBS = """
query ListJobs($first: Int, $after: String, $status: JobStatusTypeEnum) {
  jobs(first: $first, after: $after, filter: {status: $status}) {
    nodes {
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
      startAt
      endAt
      total
      createdAt
      updatedAt
    }
    pageInfo {
      hasNextPage
      endCursor
    }
    totalCount
  }
}
"""

GET_JOB = """
query GetJob($id: EncodedId!) {
  job(id: $id) {
    id
    title
    jobNumber
    jobStatus
    instructions
    client {
      id
      firstName
      lastName
      companyName
      email
    }
    property {
      id
      address {
        street1
        street2
        city
        province
        postalCode
      }
    }
    startAt
    endAt
    total
    createdAt
    updatedAt
  }
}
"""

# Quote Queries
LIST_QUOTES = """
query ListQuotes($first: Int, $after: String, $status: QuoteStatusTypeEnum) {
  quotes(first: $first, after: $after, filter: {status: $status}) {
    nodes {
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
      amounts {
        total
      }
      createdAt
      updatedAt
    }
    pageInfo {
      hasNextPage
      endCursor
    }
    totalCount
  }
}
"""

GET_QUOTE = """
query GetQuote($id: EncodedId!) {
  quote(id: $id) {
    id
    quoteNumber
    title
    quoteStatus
    message
    client {
      id
      firstName
      lastName
      companyName
      email
    }
    lineItems {
      nodes {
        id
        name
        description
        quantity
        unitPrice
        totalPrice
      }
    }
    amounts {
      subtotal
      discountAmount
      taxAmount
      total
    }
    createdAt
    updatedAt
  }
}
"""

# Invoice Queries
LIST_INVOICES = """
query ListInvoices($first: Int, $after: String, $status: InvoiceStatusTypeEnum) {
  invoices(first: $first, after: $after, filter: {status: $status}) {
    nodes {
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
      amounts {
        total
        paymentsTotal
        invoiceBalance
      }
      dueDate
      issuedDate
      createdAt
      updatedAt
    }
    pageInfo {
      hasNextPage
      endCursor
    }
    totalCount
  }
}
"""

GET_INVOICE = """
query GetInvoice($id: EncodedId!) {
  invoice(id: $id) {
    id
    invoiceNumber
    subject
    invoiceStatus
    message
    client {
      id
      firstName
      lastName
      companyName
      email
    }
    jobs {
      nodes {
        id
        title
        jobNumber
      }
    }
    lineItems {
      nodes {
        id
        name
        description
        quantity
        unitPrice
        totalPrice
      }
    }
    amounts {
      subtotal
      discountAmount
      taxAmount
      paymentsTotal
      invoiceBalance
      total
    }
    dueDate
    issuedDate
    createdAt
    updatedAt
  }
}
"""
