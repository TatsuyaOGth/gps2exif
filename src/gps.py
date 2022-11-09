import json
import datetime
from time import time_ns

class GoogleLocationHistory:

    data = []

    def load(self, filepath):
        with open(filepath) as f:
            records = json.load(f)
        locs = records['locations']
        self.data = []
        for loc in locs:
            dt_jst = self._get_timestamp_jst(loc)
            lat = self._e7_to_number(float(loc['latitudeE7']))
            lon = self._e7_to_number(float(loc['longitudeE7']))
            self.data.append((dt_jst, lat, lon))
            
    def find_nearest(self, dt):
        for d in self.data:
            if d[0] > dt:
                return d
        return None

    def print(self):
        for key in self.data.keys():
            print(key, self.data.get(key))

    def _get_timestamp_jst(self, loc):
        isodatetime = str(loc['timestamp']).replace('Z', '+09:00')
        dt = datetime.datetime.fromisoformat(isodatetime)
        return dt + datetime.timedelta(hours=9)

    def _e7_to_number(self, e7format):
        return e7format / 1e7
