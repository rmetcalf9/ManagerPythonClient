

class ExpectedEntryBase:
    def __init__(self, companyObj, date, description):
        self.companyObj = companyObj
        self.date = date
        self.description = description
        self.checkRun = False
        self.isPresent = False
        self.correctionProcessWasRun = False
        self.matched_item = None

    def _get_start_output_line(self):
        retVal = ""
        if self.is_correctable():
            retVal += "CANCOR "
        else:
            if self.isPresent:
                if self.correctionProcessWasRun:
                    retVal += "FIXED  "
                else:
                    retVal += "OK     "
            else:
                retVal += "       "
        retVal += (self.companyObj["shortName"] + "     ")[:3] + " "
        retVal += self.date + " "
        retVal += self.__class__.__name__[13:] + " "
        return retVal

    def get_user_output_line(self):
        retVal = self._get_start_output_line()
        retVal += self.description + " "
        retVal += str(self.amount) + " "
        return retVal

    def check(self, client, recheck=False):
        if not recheck:
            if self.checkRun:
                return # Already checked
        res = self._check(client)
        if res is None:
            return
        self.isPresent = res
        self.checkRun = True

    def _checkOutcomeStr(self):
        if not self.checkRun:
            return ""
        if self.isPresent:
            return "✅ Found Entry"
        return "❌ Missing"
    # Checks the entry to see if it can be found
    def _check(self, client):
        raise Exception("__check Not Overridden in " + self.__class__.__name__)

    def is_correctable(self):
        if not self.checkRun:
            return False
        if self.isPresent:
            return False # No need to correct
        return self._is_correctable()


    def correct(self, client):
        if not self.is_correctable():
            return 0
        if self.isPresent:
            raise Exception("It is correctable but element already present")
        if self.correctionProcessWasRun:
            raise Exception("Trying to correct twice")
        num = self._correct(client)
        self.check(client, recheck=True)
        if not self.isPresent:
            print("ERROR WHEN TRYING CORRECTION")
            print(self.get_user_output_line())
            print("")
            raise Exception("Did not find created entry - bad error")
        self.correctionProcessWasRun = True
        return num


    # Override these both together
    def _is_correctable(self):
        return False
    def _correct(self, client):
        raise Exception("Not Overridden")
        #return 1 #num records corrected

    def _save_matched_item(self, item):
        self.matched_item = item

    def get_matched_item(self):
        return self.matched_item

    # def sorting_weight(self):
    #     return 100