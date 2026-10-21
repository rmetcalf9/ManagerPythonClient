
from .ExpectedEntryBase import ExpectedEntryBase


class ExpectedEntryInterAccountTransfer(ExpectedEntryBase):
    def __init__(self, companyObj, date, paidFromAccount, description, amount, receivedInAccount, reference):
        # reference, billingAddress needed for creation
        super().__init__(companyObj, date, description)

        # Extra match on fields
        self.paidFromAccount = paidFromAccount
        self.receivedInAccount = receivedInAccount
        self.amount = amount

        # Other fields needed for creation
        self.reference = reference

    def get_user_output_line(self):
        retVal = self._get_start_output_line()
        retVal += "From " + self.paidFromAccount["name"]
        retVal += " -> " + self.receivedInAccount["name"] + " "
        retVal += str(self.amount) + " "
        retVal += "   " + self._checkOutcomeStr()
        return retVal

    def _check(self, client):
        transfers = client.get_inter_account_transfer_for_description(self.companyObj["loginSession"], self.description)
        for transfer in transfers:
            # description already matched
            # Has to match date amount paidFromAccount receivedInAccount
            if transfer["date"] == self.date:
                if transfer["amount"]["value"] == self.amount:
                    if transfer["paidFrom"] == self.paidFromAccount["name"]:
                        if transfer["receivedIn"] == self.receivedInAccount["name"]:
                            return True
        return False

    def _is_correctable(self):
        return True
    def _correct(self, client):
        transfer_result = client.create_inter_account_transfer(
            loginSession=self.companyObj["loginSession"],
            date=self.date,
            reference=self.reference,
            paidFromAccountKey=self.paidFromAccount["key"],
            receivedInAccountKey=self.receivedInAccount["key"],
            description=self.description,
            amount=self.amount
        )
        return 1 #num records corrected
