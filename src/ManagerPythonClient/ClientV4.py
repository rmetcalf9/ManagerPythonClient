import PythonAPIClientBase
import copy
import json
# This is the V4 client
#  it is designed to work always with the same business
#  only for local so no login

class ManagerClientV4(PythonAPIClientBase.APIClientBase):
    def __init__(self, baseUrl, business_name, mock=None, forceOneRequestAtATime=False, verboseLogging=PythonAPIClientBase.VerboseLoggingNullLogClass(), debug=False):
        self.debug = debug
        self.business_name = business_name
        useBaseUrl = baseUrl
        if useBaseUrl != "MOCK":
            if not baseUrl.endswith("/api4"):
                raise Exception(f"Baseurl does not have a /api4 endpoint {baseUrl} (Do you need Client?")
            useBaseUrl = useBaseUrl
        super().__init__(baseURL=useBaseUrl, mock=mock, forceOneRequestAtATime=forceOneRequestAtATime, verboseLogging=verboseLogging)

    def sendRequest(self, reqFn, url, loginSession, data, origin, injectHeadersFn, postRefreshCall=False, skipLockCheck=False, params=None):
        business_params = {}
        if params is not None:
            business_params = copy.deepcopy(params)
        business_params["business"] = self.business_name
        return super().sendRequest(reqFn, url, loginSession, data, origin, injectHeadersFn, postRefreshCall, skipLockCheck, params=business_params)

    def get_profit_and_loss_statement_batch(self):
        apiPath = "/profit-and-loss-statement-batch"
        response = self.sendGetRequest(
            url=apiPath,
            loginSession=None
        )
        if response.status_code != 200:
            raise Exception(f"Error getting {apiPath} ({response.status_code} - {response.text})")
        data = json.loads(response.text)
        return data

    def get_profit_and_loss_statement_view(self, key):
        apiPath = "/profit-and-loss-statement-view"
        params = {
            "key": key
        }
        response = self.sendGetRequest(
            url=apiPath,
            loginSession=None,
            params=params
        )
        if response.status_code != 200:
            raise Exception(f"Error getting {apiPath} ({response.status_code} - {response.text})")
        data = json.loads(response.text)
        return data

    def get_balance_sheet_batch(self):
        apiPath = "/balance-sheet-batch"
        response = self.sendGetRequest(
            url=apiPath,
            loginSession=None
        )
        if response.status_code != 200:
            raise Exception(f"Error getting {apiPath} ({response.status_code} - {response.text})")
        data = json.loads(response.text)
        return data

    def get_balance_sheet_batch(self):
        apiPath = "/balance-sheet-batch"
        response = self.sendGetRequest(
            url=apiPath,
            loginSession=None
        )
        if response.status_code != 200:
            raise Exception(f"Error getting {apiPath} ({response.status_code} - {response.text})")
        data = json.loads(response.text)
        return data

    def get_trial_balance_batch(self):
        apiPath = "/get-trial-balance-batch"
        response = self.sendGetRequest(
            url=apiPath,
            loginSession=None
        )
        if response.status_code != 200:
            raise Exception(f"Error getting {apiPath} ({response.status_code} - {response.text})")
        data = json.loads(response.text)
        return data

