import logging
from datetime import datetime

_LOGGER = logging.getLogger(__name__)


class Meter(object):
    """
    This is a collection of meter data that we care about.
    """

    def __init__(self, api_interface, meter_type, meter_id, meter_start_date, update_interval):
        self.api = api_interface
        self.type = meter_type
        self.id = meter_id
        self.start_date = meter_start_date
        self.update_interval = 10
        if update_interval > 10:
            self.update_interval = update_interval
        self.yesterdays_kwh = None
        self.yesterdays_gas = None
        self.billing_days = None
        self.total_kwh = None
        self.average_kwh = None
        self.total_gas = None
        self.average_gas = None
        self.unit = None
        self.date = datetime.now()
        self.update(True)

    def set_billing_usage(self, _dict):
        self.billing_days = _dict.get("BillingDays")
        self.total_kwh = _dict.get("ElectricityUsed")
        self.average_kwh = _dict.get("AvgElectricityUsed")
        self.total_gas = _dict.get("GasUsed")
        self.average_gas = _dict.get("AvgGasUsed")

    def set_chart_usage(self, _dict):
        unit1 = _dict.get("unitOfMeasure1")
        unit2 = _dict.get("unitOfMeasure2")
        if unit1:
            self.unit = unit1
        else:
            self.unit = unit2
        if self.type == "ELECTRIC":
            electric = _dict.get("meterData").get("Electric")
            self.yesterdays_kwh = electric[-1]
        elif self.type == "GAS":
            gas = _dict.get("meterData").get("Gas")
            self.yesterdays_gas = gas[-1]
        else:
            _LOGGER.error("Invalid meter type {}".format(self.type))

    def get_usage(self):
        if self.type == "ELECTRIC":
            return self.yesterdays_kwh
        elif self.type == "GAS":
            return self.yesterdays_gas
        else:
            _LOGGER.error("Invalid meter type {}".format(self.type))

    def get_average(self):
        if self.type == "ELECTRIC":
            return self.average_kwh
        elif self.type == "GAS":
            return self.average_gas   
        else:
            _LOGGER.error("Invalid meter type {}".format(self.type)) 

    def get_total(self):
        if self.type == "ELECTRIC":
            return self.total_kwh
        elif self.type == "GAS":
            return self.total_gas
        else:
            _LOGGER.error("Invalid meter type {}".format(self.type))

    def get_days_billed(self):
        return self.billing_days

    def get_unit(self):
        return self.unit

    def update(self, force=False):
        if ((datetime.now() - self.date).seconds / 60 >= self.update_interval) or force:
            _LOGGER.info("Getting new meter info")
            self.date = datetime.now()
            self.api.get_billing_info(self)
            self.api.get_usage_chart_data(self)
            self.api.logout()

