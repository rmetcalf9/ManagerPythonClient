from .ExpectedEntryBase import ExpectedEntryBase


class ExpectedEntrySalesInvoice(ExpectedEntryBase):
    def __init__(self, companyObj, issueDate, description, customer, reference, billingAddress, account, lineDescription, qty, unitPrice):
        # reference, billingAddress needed for creation
        super().__init__(companyObj, date=issueDate, description=description)

        # Extra match on fields
        self.customer = customer
        self.account = account
        self.qty = qty
        self.unitPrice = unitPrice

        # Other fields needed for creation
        self.reference = reference
        self.lineDescription = lineDescription
        self.billingAddress = billingAddress

    # salesInvoiceGenerator = client.create_sales_invoice_generator(
    #     issueDate="2026-01-31",
    #     reference="REF",
    #     customerKey=customer["key"],
    #     billingAddress="One the road\nthe street\nth towh, DF3 F45",
    #     description=invoiceDescription
    # )
    # salesInvoiceGenerator.addLine(
    #     accountKey=account["key"],
    #     description="TODO",
    #     qty=2,
    #     unit_price=12.34
    # )

    def get_user_output_line(self):
        retVal = self._get_start_output_line()
        retVal += self.customer["name"] + " "
        retVal += self.description + " "
        retVal += str(self.qty) + "x" + str(self.unitPrice) + " "
        retVal += "(" + self.account["name"] + ") "
        retVal += "   " + self._checkOutcomeStr()
        return retVal

    def _check(self, client):
        # fields to match
        # date
        # description
        # self.customer = customer
        # self.account = account # Not going to be able to match on line account
        # self.qty = qty
        # self.unitPrice = unitPrice
        invoices = client.get_sales_invoices_for_customer(self.companyObj["loginSession"], self.customer["name"])
        for invoice in invoices:
            if invoice["issueDate"] == self.date:
                if invoice["description"] == self.description:
                    if invoice["invoiceAmount"]["value"] == self.get_total_amount():
                        self._save_matched_item(invoice)
                        return True
        return False

    def get_name(self):
        # Used in payment get_user_output_line display
        return self.customer["name"]

    def get_total_amount(self):
        return self.qty * self.unitPrice

    def _is_correctable(self):
        return True
    def _correct(self, client):
        salesInvoiceGenerator = client.create_sales_invoice_generator(
            issueDate=self.date,
            reference=self.reference,
            customerKey=self.customer["key"],
            billingAddress=self.billingAddress,
            description=self.description
        )
        salesInvoiceGenerator.addLine(
            accountKey=self.account["key"],
            description=self.lineDescription,
            qty=self.qty,
            unit_price=self.unitPrice
        )
        sales_invoice_info = client.create_sales_invoice(self.companyObj["loginSession"], salesInvoiceGenerator)
        self._save_matched_item(sales_invoice_info)
        return 1

    def sorting_weight(self):
        return 50 # must before purchase invoice patments
