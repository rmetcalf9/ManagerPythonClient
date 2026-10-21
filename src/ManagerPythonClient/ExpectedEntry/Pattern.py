


class Pattern:
    entries = None
    key = None
    def __init__(self,key):
        self.entries = []
        self.key = key
    def add_entry(self, expected_entry):
        self.entries.append(expected_entry)

    def get_key(self):
        return self.key

    def get_user_output(self):
        retVal = ""

        for entry in self.entries:
            retVal += entry.get_user_output_line() + "\n"

        return retVal

    def check_all_enteries(self, client):
        for entry in self.entries:
            entry.check(client)

    def num_correctable_entries(self, client):
        self.check_all_enteries(client)
        retVal =0
        for entry in self.entries:
            if entry.is_correctable():
                retVal += 1
        return retVal

    def is_correctable(self, client):
        self.check_all_enteries(client)
        for entry in self.entries:
            if not entry.is_correctable():
                return False
        return True

    def run_corrections(self, client):
        number_corrected = 0
        ##self.entries.sort(key=lambda entry: entry.sorting_weight())
        for entry in self.entries:
            number_corrected += entry.correct(client)
        return number_corrected
