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
            dt_utc = self._get_timestamp(loc)
            lat = self._e7_to_number(float(loc['latitudeE7']))
            lon = self._e7_to_number(float(loc['longitudeE7']))
            self.data.append((dt_utc, lat, lon))
            
    def find_nearest(self, dt_utc):
        for d in self.data:
            if d[0] > dt_utc:
                return d
        return None

    def print(self):
        for key in self.data.keys():
            print(key, self.data.get(key))
        
    def _get_timestamp(self, loc):
        isodatetime = str(loc['timestamp']).replace('Z', '+00:00')
        dt = datetime.datetime.fromisoformat(isodatetime)
        return dt

    def _e7_to_number(self, e7format):
        return e7format / 1e7
