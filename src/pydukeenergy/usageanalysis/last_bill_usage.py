class lastBillUsage(object):

    def __init__(self, _dict):
        self.billing_days = _dict.get("BillingDays")
        self.total_kwh = _dict.get("ElectricityUsed")
        self.average_kwh = _dict.get("AvgElectricityUsed")
        self.total_gas = _dict.get("GasUsed")
        self.average_gas = _dict.get("AvgGasUsed")

    def total_kwh(self):
    	return self.total_kwh

