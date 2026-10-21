

class SalesInvoiceGenerator:
    lines = None
    def __init__(self, issueDate, reference, customerKey, billingAddress, description):
        self.issueDate = issueDate
        self.reference = reference
        self.customerKey = customerKey
        self.billingAddress = billingAddress
        self.description = description
        self.lines = []

    def addLine(self, accountKey, description, qty, unit_price):
        self.lines.append((accountKey, description, qty, unit_price))
