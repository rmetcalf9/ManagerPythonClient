from PythonAPIClientBase import LoginSession

class ManagerLoginSession(LoginSession):
    token = None
    def __init__(self, client, token):
        self.client = client
        self.token = token

    def injectHeaders(self, headers):
        headers["X-API-KEY"] = self.token

    def refresh(self):
        return False


class ManagerLoginSessionFromAuthToken(ManagerLoginSession):
    def __init__(self, client, access_token):
        super().__init__(client=client, token=access_token)
