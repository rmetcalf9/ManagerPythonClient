from .ExpectedEntryBase import ExpectedEntryBase


class ExpectedEntryPurchaseInvoice(ExpectedEntryBase):
    def __init__(self, companyObj, date, description, supplier, reference, account, lineDescription, qty, unitPrice, requiredAttachements=0, attachements=[]):
        # reference, billingAddress needed for creation
        super().__init__(companyObj, date, description)

        # Extra match on fields
        self.supplier = supplier
        self.account = account
        self.qty = qty
        self.unitPrice = unitPrice

        # Other fields needed for creation
        self.reference = reference
        self.lineDescription = lineDescription

        self.requiredAttachements = requiredAttachements
        self.attachements = attachements
        if not isinstance(self.attachements, list):
            raise Exception("Attachements should be a list")
        for (filename, filedata) in self.attachements:
            if not isinstance(filename, str):
                raise Exception("Attachment Filename should be a string")
            if not isinstance(filedata, bytes):
                print("Got type", filedata.__class__)
                raise Exception("Attachment filedata should be a x")


    # purchaseInvoiceGenerator = client.create_purchase_invoice_generator(
    #     issueDate="2026-02-25",
    #     reference="REF" + random_string,
    #     supplierKey=supplier["key"],
    #     description=invoiceDescription
    # )
    # purchaseInvoiceGenerator.addLine(
    #     accountKey=expenseAccount["key"],
    #     description="Thing I really wanted",
    #     qty=1,
    #     unit_price=purchaseInvoiceAmount
    # )

    def get_user_output_line(self):
        retVal = self._get_start_output_line()
        retVal += self.supplier["name"] + " "
        retVal += self.description + " "
        retVal += str(self.qty) + "x" + str(self.unitPrice) + " "
        retVal += "(" + self.account["name"] + ") "
        retVal += "   " + self._checkOutcomeStr()
        return retVal

    def _check(self, client):
        # fields to match
        # date
        # description
        # self.supplier = supplier
        # self.account = account # Not going to be able to match on line account
        # self.qty = qty
        # self.unitPrice = unitPrice
        invoices = client.get_purchase_invoices_for_supplier(self.companyObj["loginSession"], self.supplier["name"])
        for invoice in invoices:
            if invoice["issueDate"] == self.date:
                if invoice["description"] == self.description:
                    if invoice["invoiceAmount"]["value"] == self.get_total_amount():
                        self._save_matched_item(invoice)
                        return True

        return False

    def get_name(self):
        # Used in payment get_user_output_line display
        return self.supplier["name"]

    def get_total_amount(self):
        return self.qty * self.unitPrice

    def _is_correctable(self):
        if len(self.attachements) != self.requiredAttachements:
            return False
        return True # False for now change later
    def _correct(self, client):
        purchaseInvoiceGenerator = client.create_purchase_invoice_generator(
            issueDate=self.date,
            reference=self.reference,
            supplierKey=self.supplier["key"],
            description=self.description
        )
        purchaseInvoiceGenerator.addLine(
            accountKey=self.account["key"],
            description=self.lineDescription,
            qty=self.qty,
            unit_price=self.unitPrice
        )
        purchase_result = client.create_purchase_invoice(self.companyObj["loginSession"], purchaseInvoiceGenerator)
        self._save_matched_item(purchase_result)

        for (filename, filedata) in self.attachements:
            upload_attach_result = client.attach_to_purchase_invoice(
                loginSession=self.companyObj["loginSession"],
                purchaseInvoiceKey=purchase_result["Key"],
                filename=filename,
                fileData=filedata,
                fileType=None # will guess if none is provided
            )
        return 1 #num records corrected

    def sorting_weight(self):
        return 50 # must before purchase invoice payments