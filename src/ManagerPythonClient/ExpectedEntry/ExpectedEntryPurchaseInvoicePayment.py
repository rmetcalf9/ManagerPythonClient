from .ExpectedEntryBase import ExpectedEntryBase
from .ExpectedEntryPurchaseInvoice import ExpectedEntryPurchaseInvoice

class ExpectedEntryPurchaseInvoicePayment(ExpectedEntryBase):
    def __init__(self, companyObj, date, description, paidFromAccount, accountPayableSupplier, account, amount, purchaseInvoice):
        # reference, billingAddress needed for creation
        super().__init__(companyObj, date, description)

        # Extra match on fields
        self.paidFromAccount = paidFromAccount
        self.accountPayableSupplier = accountPayableSupplier
        self.amount = amount

        # Other fields needed for creation
        self.account = account # e.g. accounts payable
        self.purchaseInvoice = purchaseInvoice
        if not isinstance(purchaseInvoice, ExpectedEntryPurchaseInvoice):
            raise Exception("Must have a purchase invoice to relate to")
        if self.companyObj["name"] != self.purchaseInvoice.companyObj["name"]:
            raise Exception("Purchase Invoice does not belong to the same company")
        if self.amount != self.purchaseInvoice.get_total_amount():
            raise Exception ("Purchase invoice NOT being paid in full")

    # purchaseInvoicePaymentResult = client.pay_purchase_invoice(
    #     loginSession=testBusinessLoginSesison,
    #     date="2026-02-25",
    #     paidFromAccountKey=rebloutCashAccount["key"],
    #     description="pay Desc",
    #     accountKey=accountsPayable["key"],
    #     accountPayableSupplier=supplier["key"],
    #     purchaseInvoiceKey=purchase_result["Key"],
    #     amount=purchaseInvoiceAmount
    # )

    def get_user_output_line(self):
        retVal = self._get_start_output_line()
        retVal += "Paying " + self.purchaseInvoice.get_name() + " "
        retVal += self.paidFromAccount["name"] + " "
        retVal += self.description + " "
        retVal += str(self.amount) + " "
        retVal += "(" + self.account["name"] + ") "
        retVal += "   " + self._checkOutcomeStr()
        return retVal

    def _check(self, client):
        # fields to match
        # date
        # description
        # self.paidFromAccount = paidFromAccount
        # self.accountPayableSupplier = accountPayableSupplier
        # self.amount = amount
        payments = client.get_payment_for_description(self.companyObj["loginSession"], self.description)
        for payment in payments:
            #print("purchase invoice Payment Match Debug", payment)
            if payment["date"] == self.date:
                if payment["paidFrom"] == self.paidFromAccount["name"]:
                    if payment["payee"] == self.accountPayableSupplier["name"]:
                        if payment["amount"]["value"] == self.amount:
                            return True
        return False

    def _is_correctable(self):
        return True
    def _correct(self, client):
        purchaseInvoicePaymentResult = client.pay_purchase_invoice(
            loginSession=self.companyObj["loginSession"],
            date=self.date,
            paidFromAccountKey=self.paidFromAccount["key"],
            description=self.description,
            accountKey=self.account["key"],
            accountPayableSupplier=self.accountPayableSupplier["key"],
            purchaseInvoiceKey=self.purchaseInvoice.get_matched_item()["key"],
            amount=self.amount
        )
        return 1 #num records corrected