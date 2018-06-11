# pydukeenergy
Python3 interface to the unofficial Duke Energy API.

**NOTE** This isn't using an official API therefore this library could stop working at any time, without warning.

```python
from pydukeenergy.api import DukeEnergy

def main():
	# update_interval is optional default is 60 minutes
    duke = DukeEnergy("your_user_name", "your_password", update_interval=60)
    meters = duke.get_meters()
    for meter in meters:
    	print(meter.get_usage())
```