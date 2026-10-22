from importlib.metadata import files

import PythonAPIClientBase
import json
from urllib.parse import quote
from uuid import UUID
import base64
import mimetypes
import os
import requests
import copy
from decimal import Decimal
import datetime

from .SalesInvoiceGenerator import SalesInvoiceGenerator
from .PurchaseInvoiceGenerator import PurchaseInvoiceGenerator
from .TransactionReporter import TransactionReporter


def json_dump_s_default_function(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError(
        f"Object of type {type(obj).__name__} is not JSON serializable"
    )

def nameMatchFunction(item, name):
    return item["name"] == name

def _get_attachment_url(purchaseInvoiceKey, businessName):
    name = businessName.encode()

    protobuf = b"\xa2\x06" + bytes([len(name)]) + name

    uuid = UUID(purchaseInvoiceKey)

    protobuf += b"\x0a" + b"\x12"
    protobuf += b"\x09" + uuid.bytes_le[:8]
    protobuf += b"\x11" + uuid.bytes_le[8:]

    encoded = base64.urlsafe_b64encode(protobuf).decode().rstrip("=")

    return f"/new-attachment?{encoded}"

class ManagerClient(PythonAPIClientBase.APIClientBase):
    debug = None
    def __init__(self, baseUrl, mock=None, forceOneRequestAtATime=False, verboseLogging=PythonAPIClientBase.VerboseLoggingNullLogClass(), debug=False):
        self.debug = debug
        useBaseUrl = baseUrl
        if useBaseUrl != "MOCK":
            useBaseUrl = useBaseUrl
        super().__init__(baseURL=useBaseUrl, mock=mock, forceOneRequestAtATime=forceOneRequestAtATime, verboseLogging=verboseLogging)

    def is_online(self):
        try:
            response = self.sendGetRequest(
                url="/",
                loginSession=None
            )
        except PythonAPIClientBase.APIClientException as cli:
            if cli.result.status_code == 401:
                return True # running but not authed as we have no login session
            return False
        except Exception as exp:
            print("Other exp", exp)
            return False
        return True

    def _get_generator(self, loginSession, apiObj, outputKey=None, enrichParams=None, skipFn=None):
        if outputKey is None:
            outputKey = apiObj
        pageSize = 100
        skip = 0
        while True:
            params = {
                "pageSize": pageSize,
                "skip": skip
            }
            if enrichParams is not None:
                enrichParams(params)
            response = self.sendGetRequest(
                url=f"/{apiObj}",
                loginSession=loginSession,
                params=params
            )
            if response.status_code != 200:
                print("status_code=", response.status_code)
                raise Exception("Error getting " + apiObj)
            data = json.loads(response.text)
            # print("D", data)
            if outputKey not in data:
                print("Possible keys", data.keys())
                raise Exception("given output key not possible - " + outputKey)
            customers = data[outputKey]
            for customer in customers:
                skip = False
                if skipFn is not None:
                    skip = skipFn(customer)
                if not skip:
                    yield customer
            if len(customers) < pageSize:
                break
            skip += pageSize

    def _get_single(self, loginSession, name, apiObj, outputKey=None, matchFn=nameMatchFunction, extra_params={}):
        if outputKey is None:
            outputKey = apiObj
        params = copy.deepcopy(extra_params)
        if name is not None:
            params["term"] = name
        response = self.sendGetRequest(
            url=f"/{apiObj}",
            loginSession=loginSession,
            params=params
        )
        if response.status_code != 200:
            raise Exception("Error getting " + apiObj)
        data = json.loads(response.text)
        if outputKey is None:
            # we do not know the output key, just output it all
            if matchFn is not None:
                raise Exception("No output key given - not possible to use a match function")
            return data
        if outputKey not in data:
            raise Exception(f"OutputKey: {outputKey} not found in response - given keys: {data.keys()}")
        if len(data[outputKey]) == 0:
            return None
        retItems = []
        for item in data[outputKey]:
            if matchFn(item, name):
                retItems.append(item)
        if len(retItems) == 0:
            return None
        if len(retItems) == 1:
            return retItems[0]
        return None # only return if we have a unique match


    def get_customers(self, loginSession):
        return self._get_generator(loginSession, "customers")
    def get_customer(self, loginSession, name):
        return self._get_single(loginSession, name, "customers")

    def get_suppliers(self, loginSession):
        return self._get_generator(loginSession, "suppliers")
    def get_supplier(self, loginSession, name):
        return self._get_single(loginSession, name, "suppliers")

    def get_bank_and_cash_accounts(self, loginSession):
        return self._get_generator(loginSession, "bank-and-cash-accounts", "bankAndCashAccounts")
    def get_bank_and_cash_account(self, loginSession, name):
        return self._get_single(loginSession, name, "bank-and-cash-accounts", "bankAndCashAccounts")

    def get_chart_of_accounts(self, loginSession):
        return self._get_generator(loginSession, "chart-of-accounts", "chartOfAccounts")
    def get_chart_of_account(self, loginSession, name):
        return self._get_single(loginSession, name, "chart-of-accounts", "chartOfAccounts")

    def get_sales_invoices(self, loginSession):
        def enrichParams(params):
            params["sortBy"] = "IssueDate"
        return self._get_generator(loginSession, "sales-invoices", "salesInvoices", enrichParams=enrichParams)
    def get_sales_invoices_for_customer(self, loginSession, customerName):
        def skipFn(sales_invoice):
            if customerName != sales_invoice["customer"]:
                return True
            return False
        return self._get_generator(loginSession, "sales-invoices", "salesInvoices", skipFn=skipFn)
    def get_sales_invoice(self, loginSession, description, customerName):
        def nameMatchFunction(item, name):
            if item["customer"] != customerName:
                return False
            if item["description"] != description:
                return False
            return True
        return self._get_single(loginSession, description, "sales-invoices", "salesInvoices", matchFn=nameMatchFunction)

    def get_sales_invoices_for_period(self, loginSession, start_day, end_day):
        # Start day and end day format to be passed to this function: "01-JAN-2024"
        # issuedate format in returned string 'issueDate': '2026-01-31'
        def check_date_format(x):
            if not isinstance(x, str):
                raise ValueError("Invalid date format")
            if len(x) != 11:
                raise ValueError("Invalid date format")
        check_date_format(start_day)
        check_date_format(end_day)
        start_date = datetime.datetime.strptime(start_day, "%d-%b-%Y").date()
        end_date = datetime.datetime.strptime(end_day, "%d-%b-%Y").date()
        if start_date > end_date:
            raise ValueError("start_day must be before or equal to end_day")
        for invoice in self.get_sales_invoices(loginSession):
            issue_date = datetime.datetime.strptime(
                invoice["issueDate"], "%Y-%m-%d"
            ).date()
            if issue_date > end_date:
                break
            if issue_date >= start_date:
                yield invoice

    def get_sales_invoice_lines(self, loginSession):
        def enrichParams(params):
            params["sortBy"] = "IssueDate"
        return self._get_generator(loginSession, "sales-invoice-lines", "salesInvoiceLines", enrichParams=enrichParams)
    def get_sales_invoice_lines_for_period(self, loginSession, start_day, end_day):
        # Start day and end day format to be passed to this function: "01-JAN-2024"
        # issuedate format in returned string 'issueDate': '2026-01-31'
        def check_date_format(x):
            if not isinstance(x, str):
                raise ValueError("Invalid date format")
            if len(x) != 11:
                raise ValueError("Invalid date format")
        check_date_format(start_day)
        check_date_format(end_day)
        start_date = datetime.datetime.strptime(start_day, "%d-%b-%Y").date()
        end_date = datetime.datetime.strptime(end_day, "%d-%b-%Y").date()
        if start_date > end_date:
            raise ValueError("start_day must be before or equal to end_day")
        for invoice in self.get_sales_invoice_lines(loginSession):
            issue_date = datetime.datetime.strptime(
                invoice["issueDate"], "%Y-%m-%d"
            ).date()
            if issue_date > end_date:
                break
            if issue_date >= start_date:
                yield invoice

    def get_sales_invoice_form(self, loginSession, sales_invoice_key):
        return self._get_single(loginSession, None, f"sales-invoice-form/{sales_invoice_key}", None)

    def get_inter_account_transfer_for_description(self, loginSession, description):
        def enrichParams(params):
            params["term"] = description
        # def skipFn(rec):
        #     if date == rec["date"]:
        #         return False
        #     return True
        return self._get_generator(
            loginSession,
            "inter-account-transfers",
            "interAccountTransfers",
            enrichParams=enrichParams
        )


    def get_purchase_invoices(self, loginSession):
        return self._get_generator(loginSession, "purchase-invoices", "purchaseInvoices")
    def get_purchase_invoices_for_supplier(self, loginSession, supplierName):
        def skipFn(purchase_invoice):
            if supplierName != purchase_invoice["supplier"]:
                return True
            return False
        return self._get_generator(loginSession, "purchase-invoices", "purchaseInvoices", skipFn=skipFn)
    def get_purchase_invoice(self, loginSession, description, supplierName):
        def nameMatchFunction(item, name):
            if item["supplier"] != supplierName:
                return False
            if item["description"] != description:
                return False
            return True
        return self._get_single(loginSession, description, "purchase-invoices", "purchaseInvoices", matchFn=nameMatchFunction)

    def get_payment_for_description(self, loginSession, description):
        def enrichParams(params):
            params["term"] = description
        # def skipFn(rec):
        #     if date == rec["date"]:
        #         return False
        #     return True
        return self._get_generator(
            loginSession,
            "payments",
            "payments",
            enrichParams=enrichParams
        )

    def create_sales_invoice_generator(self, issueDate, reference, customerKey, billingAddress, description):
        return SalesInvoiceGenerator(issueDate, reference, customerKey, billingAddress, description)

    def create_sales_invoice(self, loginSession, generator):
        if not isinstance(generator, SalesInvoiceGenerator):
            raise Exception("Wrong type of generator")
        hasLineDescription = False
        for line in generator.lines:
            accountKey, description, qty, unit_price = line
            if description is not None and description != "":
                hasLineDescription = True
        postData = {
            "IssueDate": generator.issueDate,
            "Reference": generator.reference,
            "Customer": generator.customerKey,
            "BillingAddress": generator.billingAddress,
            "Description": generator.description,
            "HasLineDescription": hasLineDescription,
            "Lines": []
        }
        if len(generator.lines) == 0:
            raise Exception("No lines found")

        for line in generator.lines:
            accountKey, description, qty, unit_price = line
            postData["Lines"].append({
                "Account": accountKey,
                "LineDescription": description,
                "Qty": qty,
                "SalesUnitPrice": unit_price
            })
        response = self.sendPostRequest(
            url="/sales-invoice-form",
            loginSession=loginSession,
            data=json.dumps(postData, default=json_dump_s_default_function)
        )
        if response.status_code != 201:
            raise Exception("Error creating sales invoice")
        data = json.loads(response.text)
        return data

    def pay_sales_invoice(self, loginSession, date, recievedAccountKey, description, accountKey, accountRecivablesCustomer, salesInvoiceKey, amount):
        postData = {
            "Date": date,
            "ReceivedIn": recievedAccountKey,
            "Description": description,
            "PaidBy": 1,
            "Customer": accountRecivablesCustomer,
            "Lines": [
                {
                    "Account": accountKey,
                    "AccountsReceivableCustomer": accountRecivablesCustomer,
                    "AccountsReceivableSalesInvoice": salesInvoiceKey,
                    "Amount": amount
                }
            ]
        }
        response = self.sendPostRequest(
            url="/receipt-form",
            loginSession=loginSession,
            data=json.dumps(postData, default=json_dump_s_default_function)
        )
        if response.status_code != 201:
            raise Exception("Error creating sales invoice payment")
        data = json.loads(response.text)
        return data

    def get_receipt_for_description(self, loginSession, description):
        def enrichParams(params):
            params["term"] = description
        # def skipFn(rec):
        #     if date == rec["date"]:
        #         return False
        #     return True
        return self._get_generator(
            loginSession,
            "receipts",
            "receipts",
            enrichParams=enrichParams
        )

    def create_purchase_invoice_generator(self, issueDate, reference, supplierKey, description):
        return PurchaseInvoiceGenerator(issueDate, reference, supplierKey, description)

    def create_purchase_invoice(self, loginSession, generator):
        if not isinstance(generator, PurchaseInvoiceGenerator):
            raise Exception("Wrong type of generator")
        hasLineDescription = False
        for line in generator.lines:
            accountKey, description, qty, unit_price = line
            if description is not None and description != "":
                hasLineDescription = True
        postData = {
            "IssueDate": generator.issueDate,
            "Reference": generator.reference,
            "Supplier": generator.supplierKey,
            "Description": generator.description,
            "HasLineDescription": hasLineDescription,
            "Lines": []
        }
        if len(generator.lines) == 0:
            raise Exception("No lines found")

        for line in generator.lines:
            accountKey, description, qty, unit_price = line
            postData["Lines"].append({
                "Account": accountKey,
                "LineDescription": description,
                "Qty": qty,
                "PurchaseUnitPrice": unit_price
            })
        response = self.sendPostRequest(
            url="/purchase-invoice-form",
            loginSession=loginSession,
            data=json.dumps(postData, default=json_dump_s_default_function)
        )
        if response.status_code != 201:
            raise Exception("Error creating sales invoice")
        data = json.loads(response.text)
        return data

    def pay_purchase_invoice(self, loginSession, date, paidFromAccountKey, description, accountKey, accountPayableSupplier, purchaseInvoiceKey, amount):
        postData = {
            "Date": date,
            "PaidFrom": paidFromAccountKey,
            "Description": description,
            "Payee": 2,
            "Supplier": accountPayableSupplier,
            "Lines": [
                {
                    "Account": accountKey,
                    "AccountsPayableSupplier": accountPayableSupplier,
                    "PurchaseInvoice": purchaseInvoiceKey,
                    "Amount": amount
                }
            ]
        }
        response = self.sendPostRequest(
            url="/payment-form",
            loginSession=loginSession,
            data=json.dumps(postData, default=json_dump_s_default_function)
        )
        if response.status_code != 201:
            raise Exception("Error creating purchase invoice payment")
        data = json.loads(response.text)
        return data

    def create_inter_account_transfer(
        self,
        loginSession,
        date,
        reference,
        paidFromAccountKey,
        receivedInAccountKey,
        description,
        amount
    ):
        postData = {
            "Date": date,
            "Reference": reference,
            "PaidFrom": paidFromAccountKey,
            "ReceivedIn": receivedInAccountKey,
            "Description": description,
            "CreditAmount": amount,
            "DebitAmount": amount
        }

        response = self.sendPostRequest(
            url="/inter-account-transfer-form",
            loginSession=loginSession,
            data=json.dumps(postData, default=json_dump_s_default_function)
        )

        if response.status_code != 201:
            raise Exception(
                f"Error creating inter account transfer: "
                f"{response.status_code} {response.text}"
            )

        return json.loads(response.text)

    def get_business(self, loginSession):
        response = self.sendGetRequest(
            url="/access-tokens?pageSize=1",
            loginSession=loginSession
        )
        if response.status_code != 200:
            raise Exception(
                f"Error getting business name: "
                f"{response.status_code} {response.text}"
            )
        data = json.loads(response.text)
        return data["business"]

    def attach_to_purchase_invoice(
            self,
            loginSession,
            purchaseInvoiceKey,
            filename,
            fileData,
            fileType=None
    ):
        import mimetypes
        import os
        fileNameToSend = os.path.basename(filename)
        fileNameToSend = quote(fileNameToSend, safe="")
        if fileType is None:
            fileType, _ = mimetypes.guess_type(fileNameToSend)
            if fileType is None:
                fileType = "application/octet-stream"
        business = self.get_business(loginSession)
        url = (self.baseURL + _get_attachment_url(
            purchaseInvoiceKey,
            business["name"]
        )).replace("/api2/", "/")

        headers = {
            "Content-Type": "application/octet-stream",
            "X-File-Name": fileNameToSend,
            "X-File-Type": fileType,
        }
        if loginSession is not None:
            loginSession.injectHeaders(headers)

        response = requests.post(
            url=url,
            data=fileData,   # raw bytes, not files=
            headers=headers
        )
        if response.status_code not in (200, 201):
            raise Exception(
                f"Error uploading attachment: "
                f"{response.status_code} {response.text}"
            )
        data = json.loads(response.text)
        return data

    def get_transaction_reporter(self, loginSession):
        def enrichParams(params):
            params["fields"] = ["Date", "Transaction", "Reference", "BankOrCashAccount", "Customer",
                "Supplier", "Employee",
                "Description", "Item", "Account", "BalanceSheetAccount", "ProfitAndLossStatementAccount",
                "LineDescription", "Qty", "UnitPrice", "Project", "Division", "TaxCode", "TaxAmount",
                "Debit", "Credit", "Amount", "Timestamp"
            ]
        gen = self._get_generator(
            loginSession,
            "transactions",
            enrichParams=enrichParams
            #,outputKey="balanceSheetTransactions"
        )
        return TransactionReporter(gen)
