

class PurchaseInvoiceGenerator:
    lines = None
    def __init__(self, issueDate, reference, supplierKey, description):
        self.issueDate = issueDate
        self.reference = reference
        self.supplierKey = supplierKey
        self.description = description
        self.lines = []

    def addLine(self, accountKey, description, qty, unit_price):
        self.lines.append((accountKey, description, qty, unit_price))
