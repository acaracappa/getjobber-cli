"""Pre-built GraphQL queries for GetJobber API."""

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
      phoneNumber
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
query GetClient($id: ID!) {
  client(id: $id) {
    id
    firstName
    lastName
    companyName
    email
    phoneNumber
    mobileNumber
    billingAddress {
      street1
      street2
      city
      province
      postalCode
      country
    }
    tags
    createdAt
    updatedAt
  }
}
"""

SEARCH_CLIENTS = """
query SearchClients($query: String!, $first: Int) {
  clients(first: $first, filter: {search: $query}) {
    nodes {
      id
      firstName
      lastName
      companyName
      email
      phoneNumber
    }
    totalCount
  }
}
"""

# Job Queries
LIST_JOBS = """
query ListJobs($first: Int, $after: String, $status: String) {
  jobs(first: $first, after: $after, filter: {status: $status}) {
    nodes {
      id
      title
      jobNumber
      status
      client {
        id
        firstName
        lastName
        companyName
      }
      startAt
      endAt
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
query GetJob($id: ID!) {
  job(id: $id) {
    id
    title
    jobNumber
    status
    description
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
    totalAmount
    createdAt
    updatedAt
  }
}
"""

# Quote Queries
LIST_QUOTES = """
query ListQuotes($first: Int, $after: String, $status: String) {
  quotes(first: $first, after: $after, filter: {status: $status}) {
    nodes {
      id
      quoteNumber
      title
      status
      client {
        id
        firstName
        lastName
        companyName
      }
      totalAmount
      sentAt
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
query GetQuote($id: ID!) {
  quote(id: $id) {
    id
    quoteNumber
    title
    status
    message
    client {
      id
      firstName
      lastName
      companyName
      email
    }
    lineItems {
      id
      name
      description
      quantity
      unitPrice
      total
    }
    subtotal
    taxAmount
    totalAmount
    sentAt
    createdAt
    updatedAt
  }
}
"""

# Invoice Queries
LIST_INVOICES = """
query ListInvoices($first: Int, $after: String, $status: String) {
  invoices(first: $first, after: $after, filter: {status: $status}) {
    nodes {
      id
      invoiceNumber
      subject
      status
      client {
        id
        firstName
        lastName
        companyName
      }
      totalAmount
      amountPaid
      balance
      dueDate
      sentAt
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
query GetInvoice($id: ID!) {
  invoice(id: $id) {
    id
    invoiceNumber
    subject
    status
    message
    client {
      id
      firstName
      lastName
      companyName
      email
    }
    job {
      id
      title
      jobNumber
    }
    lineItems {
      id
      name
      description
      quantity
      unitPrice
      total
    }
    subtotal
    taxAmount
    totalAmount
    amountPaid
    balance
    dueDate
    sentAt
    paidAt
    createdAt
    updatedAt
  }
}
"""
