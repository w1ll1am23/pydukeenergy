import logging
import json
from datetime import datetime
import sys

import requests

from pydukeenergy.usageanalysis.last_bill_usage import lastBillUsage
from pydukeenergy.usageanalysis.usage_chart_data import usageChartData

BASE_URL = "https://www.duke-energy.com/"
LOGIN_URL = BASE_URL + "form/Login/GetAccountValidationMessage"
USAGE_ANALYSIS_URL = BASE_URL + "api/UsageAnalysis/"
BILLING_INFORMATION_URL = USAGE_ANALYSIS_URL + "GetBillingInformation"
USAGE_CHART_URL = USAGE_ANALYSIS_URL + "GetUsageChartData"

USER_AGENT = {"User-Agent": "python/{}.{} pyduke-energy/0.0.1"}
LOGIN_HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}
USAGE_ANALYSIS_HEADERS = {"Content-Type": "application/json", "Accept": "application/json, text/plain, */*"}

_LOGGER = logging.getLogger(__name__)


class DukeEnergyApiInterface(object):
    """
    API interface object.
    """

    def __init__(self, email, password, meter_id):
        """
        Create the Duke Energy API interface object.
        Args:
            email (str): Duke Energy account email address.
            password (str): Duke Energy account password.
        """
        global USER_AGENT
        version_info = sys.version_info
        major = version_info.major
        minor = version_info.minor
        USER_AGENT["User-Agent"] = USER_AGENT["User-Agent"].format(major, minor)
        self.email = email
        self.password = password
        self.meter_id = meter_id
        self.session = requests.Session()
        self._login()
        self.last_bill_usage = self._get_billing_info()
        self.chart_data = self._get_usage_chart_data()

    @property
    def get_last_bill_usage(self):
        return self.last_bill_usage

    @property
    def get_chart_data(self):
        return self.chart_data

    def update(self):
        self.last_bill_usage = self._get_billing_info()
        self.chart_data = self._get_usage_chart_data()

    def _get_billing_info(self):
        """
        Pull a water heater's usage report from the API.
        """
        post_body = {"MeterNumber": "ELECTRIC - " + self.meter_id}
        headers = USAGE_ANALYSIS_HEADERS.copy()
        headers.update(USER_AGENT)
        response = self.session.post(BILLING_INFORMATION_URL, data=json.dumps(post_body), headers=headers, timeout=10, verify=False)
        if response.status_code != 200:
            _LOGGER.error("Failed to get billing info")
            return None
        if response.json()["Status"] == "ERROR":
            _LOGGER.error(response.json()["ErrorMsg"])
            return None
        return lastBillUsage(response.json()["Data"][0])

    def _get_usage_chart_data(self):
        """
        """
        post_body = {"Graph": "DailyEnergy", "BillingFrequency": "Billing Cycle", "GraphText": "Daily Energy and Avg. ", "ActiveDate": "05/16/2018"}
        post_body["Date"] = datetime.now().strftime("%m / %d / %Y")
        post_body["MeterNumber"] = "ELECTRIC - " + self.meter_id
        headers = USAGE_ANALYSIS_HEADERS.copy()
        headers.update(USER_AGENT)
        response = self.session.post(USAGE_CHART_URL, data=json.dumps(post_body), headers=headers, timeout=10, verify=False)
        if response.status_code != 200:
            _LOGGER.error("Failed to get billing info")
            return None
        if response.json()["Status"] == "ERROR":
            _LOGGER.error(response.json()["ErrorMsg"])
            return None
        return usageChartData(response.json()["meterData"])

    def _login(self):
        """
        Authenticate.
        """
        data = {"userId": self.email, "userPassword": self.password, "deviceprofile": "mobile"}
        headers = LOGIN_HEADERS.copy()
        headers.update(USER_AGENT)
        response = self.session.post(LOGIN_URL, data=data, headers=headers, timeout=10, verify=False)
        if response.status_code != 200:
            return False
