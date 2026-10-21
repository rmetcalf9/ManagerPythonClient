from .ExpectedEntryBase import ExpectedEntryBase
from .ExpectedEntrySalesInvoice import ExpectedEntrySalesInvoice

class ExpectedEntrySalesInvoiceReceipt(ExpectedEntryBase):
    def __init__(self, companyObj, date, description, receivedAccount, accountRecivablesCustomer, account, amount, salesInvoice):
        super().__init__(companyObj, date, description)

        # Extra match on fields
        self.receivedAccount = receivedAccount
        self.accountReceivablesCustomer = accountRecivablesCustomer
        self.amount = amount

        # Other fields needed for creation
        self.account = account # e.g. accounts payable
        self.salesInvoice = salesInvoice
        if not isinstance(salesInvoice, ExpectedEntrySalesInvoice):
            raise Exception("Must have a sales invoice to relate to")
        if self.companyObj["name"] != self.salesInvoice.companyObj["name"]:
            raise Exception("Sales Invoice does not belong to the same company")
        if self.amount != self.salesInvoice.get_total_amount():
            raise Exception ("Sales invoice NOT being paid in full")

    # result = client.pay_sales_invoice(
    #     loginSession=testBusinessLoginSesison,
    #     date="2026-11-30",
    #     recievedAccountKey=rebloutCashAccount["key"],
    #     description="pay Desc",
    #     accountKey=accountsRecievable["key"],
    #     accountReceivablesCustomer=customer["key"],
    #     salesInvoiceKey=looked_up_sales_invoice["key"],
    #     amount=1.01
    # )


    def get_user_output_line(self):
        retVal = self._get_start_output_line()
        retVal += "Paying " + self.salesInvoice.get_name() + " "
        retVal += self.receivedAccount["name"] + " "
        retVal += self.description + " "
        retVal += str(self.amount) + " "
        retVal += "(" + self.account["name"] + ") "
        retVal += "   " + self._checkOutcomeStr()
        return retVal

    def _check(self, client):
        # fields to match
        # date
        # description
        # self.receivedAccount = receivedAccount
        # self.accountReceivablesCustomer = accountReceivablesCustomer
        # self.amount = amount
        # Paid By is always going to be None
        payments = client.get_receipt_for_description(self.companyObj["loginSession"], self.description)
        for payment in payments:
            ##print("sales invoice receipt Match Debug", payment)
            if payment["date"] == self.date:
                if payment["paidBy"] == self.accountReceivablesCustomer["name"]:
                    if payment["receivedIn"]["key"] == self.receivedAccount["key"]:
                        if payment["amount"]["value"] == self.amount:
                            return True
        return False

    def _is_correctable(self):
        return True
    def _correct(self, client):
        result = client.pay_sales_invoice(
            loginSession=self.companyObj["loginSession"],
            date=self.date,
            recievedAccountKey=self.receivedAccount["key"],
            description=self.description,
            accountKey=self.account["key"],
            accountRecivablesCustomer=self.accountReceivablesCustomer["key"],
            salesInvoiceKey=self.salesInvoice.get_matched_item()["key"],
            amount=self.amount
        )
        return 1 #num records corrected
