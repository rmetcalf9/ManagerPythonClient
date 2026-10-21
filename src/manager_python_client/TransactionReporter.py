from decimal import Decimal

CASH_ACCOUNT_NAME = "Cash & cash equivalents"

class TransactionReporter:
    mainData = None
    # Dict, first key is the name of the bankOrCashAccount
    def __init__(self, generator):
        self.mainData = {}
        for transaction in generator:
            transaction["amount"] = Decimal(str(transaction["amount"]))
            if transaction["bankOrCashAccount"] not in self.mainData:
                self.mainData[transaction["bankOrCashAccount"]] = []
            self.mainData[transaction["bankOrCashAccount"]].append(transaction)

    def get_bank_or_cash_accounts(self):
        return [account for account in self.mainData if account is not None]

    def get_bank_or_cash_account_entries(self, bankOrCashAccountName):
        if bankOrCashAccountName not in self.mainData:
            raise Exception("bankOrCashAccountName not found")
        retVal = []
        for entry in self.mainData[bankOrCashAccountName]:
            if entry["account"] == CASH_ACCOUNT_NAME:
                retVal.append(entry)
        return sorted(retVal, key=lambda entry: entry["date"])

    def get_customer_receipts(self, customerName):
        retVal = []
        for account in self.mainData.keys():
            if account is not None:
                for entry in self.mainData[account]:
                    if entry["transaction"] == "Receipt":
                        if entry["customer"] == customerName:
                            if entry["account"] == CASH_ACCOUNT_NAME:
                                retVal.append(entry)
        return sorted(retVal, key=lambda entry: entry["date"])

    def get_supplier_payments(self, supplierName):
        retVal = []
        for account in self.mainData.keys():
            if account is not None:
                for entry in self.mainData[account]:
                    if entry["transaction"] == "Payment":
                        if entry["supplier"] == supplierName:
                            if entry["account"] == CASH_ACCOUNT_NAME:
                                retVal.append(entry)
        return sorted(retVal, key=lambda entry: entry["date"])