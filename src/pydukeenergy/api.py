import logging
import json
import sys
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
import requests

from pydukeenergy.meter import Meter

BASE_URL = "https://www.duke-energy.com/"
LOGIN_URL = BASE_URL + "form/Login/GetAccountValidationMessage"
USAGE_ANALYSIS_URL = BASE_URL + "api/UsageAnalysis/"
BILLING_INFORMATION_URL = USAGE_ANALYSIS_URL + "GetBillingInformation"
METER_ACTIVE_URL = BASE_URL + "my-account/usage-analysis"
USAGE_CHART_URL = USAGE_ANALYSIS_URL + "GetUsageChartData"

USER_AGENT = {"User-Agent": "python/{}.{} pyduke-energy/0.0.1"}
LOGIN_HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}
USAGE_ANALYSIS_HEADERS = {"Content-Type": "application/json", "Accept": "application/json, text/plain, */*"}

_LOGGER = logging.getLogger(__name__)


class DukeEnergy(object):
    """
    API interface object.
    """

    def __init__(self, email, password, update_interval=60):
        """
        Create the Duke Energy API interface object.
        Args:
            email (str): Duke Energy account email address.
            password (str): Duke Energy account password.
            update_interval (int): How often an update should occur. (Min=10)
        """
        global USER_AGENT
        version_info = sys.version_info
        major = version_info.major
        minor = version_info.minor
        USER_AGENT["User-Agent"] = USER_AGENT["User-Agent"].format(major, minor)
        self.email = email
        self.password = password
        self.meters = []
        self.session = None
        self.update_interval = update_interval
        if not self._login():
            raise DukeEnergyException("")

    def get_meters(self):
        self._get_meters()
        return self.meters

    def get_billing_info(self, meter):
        """
        Pull the billing info for the meter.
        """
        if self.session or self._login():
            post_body = {"MeterNumber": meter.type + " - " + meter.id}
            headers = USAGE_ANALYSIS_HEADERS.copy()
            headers.update(USER_AGENT)
            response = self.session.post(BILLING_INFORMATION_URL, data=json.dumps(post_body), headers=headers,
                                         timeout=10)
            try:
                if response.status_code != 200:
                    _LOGGER.error("Billing info request failed: " + response.status_code)
                    return False
                if response.json()["Status"] == "ERROR":
                    _LOGGER.error("Billing info: " + response.json()["ErrorMsg"])
                    return False
                if response.json()["Status"] == "OK":
                    _LOGGER.debug(str(response.content))
                    meter.set_billing_usage(response.json()["Data"][-1])
                    return True
                else:
                    _LOGGER.error("Status was {}".format(response.json()["Status"]))
                    return False
            except Exception as e:
                _LOGGER.exception("Something went wrong.")
                return False

    def get_usage_chart_data(self, meter):
        """
        billing_frequency ["Week", "Billing Cycle", "Month"]
        graph ["hourlyEnergyUse", "DailyEnergy", "averageEnergyByDayOfWeek"]
        """
        if datetime.today().weekday() == 6:
            the_date = meter.date - timedelta(days=1)
        else:
            the_date = meter.date
        if self.session or self._login():
            post_body = {
                "Graph": "DailyEnergy",
                "BillingFrequency": "Week",
                "GraphText": "Daily Energy and Avg. ",
                "Date": the_date.strftime("%m / %d / %Y"),
                "MeterNumber": meter.type + " - " + meter.id,
                "ActiveDate": meter.start_date
            }
            headers = USAGE_ANALYSIS_HEADERS.copy()
            headers.update(USER_AGENT)
            response = self.session.post(USAGE_CHART_URL, data=json.dumps(post_body), headers=headers, timeout=10)
            try:
                if response.status_code != 200:
                    _LOGGER.error("Usage data request failed: " + response.status_code)
                    return False
                if response.json()["Status"] == "ERROR":
                    _LOGGER.error("Usage data: " + response.json()["ErrorMsg"])
                    return False
                if response.json()["Status"] == "OK":
                    _LOGGER.debug(str(response.content))
                    meter.set_chart_usage(response.json())
                else:
                    _LOGGER.error("Status was {}".format(response.json()["Status"]))
                    return False
            except Exception as e:
                _LOGGER.exception("Something went wrong.")
                return False

    def _login(self):
        """
        Authenticate. This creates a cookie on the session which is used to authenticate with
        the other calls. Unfortunately the service always returns 200 even if you have a wrong
        password.
        """
        self.session = requests.Session()
        data = {"userId": self.email, "userPassword": self.password, "deviceprofile": "mobile"}
        headers = LOGIN_HEADERS.copy()
        headers.update(USER_AGENT)
        response = self.session.post(LOGIN_URL, data=data, headers=headers, timeout=10)
        if response.status_code != 200:
            _LOGGER.error("Failed to log in")
            return False
        return True

    def logout(self):
        """
        Delete the session.
        """
        self.session = None

    def _get_meters(self):
        """
        There doesn't appear to be a service to get this data.
        Collecting the meter info to build meter objects.
        """
        if self._login():
            response = self.session.get(METER_ACTIVE_URL, timeout=10)
            _LOGGER.debug(str(response.text))
            soup = BeautifulSoup(response.text, "html.parser")
            meter_data = json.loads(soup.find("duke-dropdown", {"id": "usageAnalysisMeter"})["items"])
            _LOGGER.debug(str(meter_data))
            for meter in meter_data:
                meter_type, meter_id = meter["text"].split(" - ")
                meter_start_date = meter["CalendarStartDate"]
                self.meters.append(Meter(self, meter_type, meter_id, meter_start_date, self.update_interval))
            self.logout()


class DukeEnergyException(Exception):
    pass

