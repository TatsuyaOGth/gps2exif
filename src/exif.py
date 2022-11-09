from exiftool import ExifToolHelper
from datetime import datetime, timezone, timedelta
from time import time_ns

class ExifToolSubprocess:
    
    def get_datetime_original(self, fname):
        dt_s = self._get_exif_data(fname, 'DateTimeOriginal')
        if dt_s is None:
            return None
        dt = datetime.strptime(dt_s, '%Y:%m:%d %H:%M:%S')
        dt_jst = dt.replace(tzinfo=timezone(timedelta(hours=9)))
        return dt_jst
            
    def get_gps_info(self, fname):
        lat = self._get_exif_data(fname, 'GPSLatitude')
        lon = self._get_exif_data(fname, 'GPSLongitude')
        if lat is None or lon is None:
            return None
        return (float(lat), float(lon))
        
    def get_gps_datetime(self, fname):
        dt_s = self._get_exif_data(fname, 'GPSDateStamp')
        tm_s = self._get_exif_data(fname, 'GPSTimeStamp')
        if dt_s is None or tm_s is None:
            return None
        dt = datetime.strptime(dt_s, '%Y:%m:%d')
        tm = datetime.strptime(tm_s, '%H:%M:%S')
        return datetime.combine(dt.date(), tm.time(), tzinfo=timezone.utc)
        
    def set_gps_info(self, fname, dt: datetime, lat, lon):
        self._set_exif_data(fname, 'GPSVersionID', '2 3 0 0')
        self._set_exif_data(fname, 'GPSLatitudeRef', 'N')
        self._set_exif_data(fname, 'GPSLongitudeRef', 'E')
        self._set_exif_data(fname, 'GPSLatitude', lat)
        self._set_exif_data(fname, 'GPSLongitude', lon)
        self._set_exif_data(fname, 'GPSDateStamp', dt.strftime('%Y:%m:%d'))
        self._set_exif_data(fname, 'GPSTimeStamp', dt.strftime('%H:%M:%S'))
        
    def print_all(self, fname):
        with ExifToolHelper() as et:
            for d in et.get_metadata(fname):
                for k, v in d.items():
                    print(f'{k} = {v}')
            
    def _get_exif_data(self, fname, tag_name):
        with ExifToolHelper() as et:
            tags = et.get_tags(fname, tag_name)

            if tags is None:
                return None

            if len(tags) == 0:
                return None

            key = 'EXIF:' + tag_name
            if key not in tags[0].keys():
                return None

            return str(tags[0][key])
            
    def _set_exif_data(self, fname, tag_name, value):
        with ExifToolHelper() as et:
            et.set_tags(
                fname,
                tags={tag_name: value},
                params=['-P', '-overwrite_original']
            )



class DateTimeHelper:
    
    def jst_to_utc_with_time(self, dt: datetime) -> datetime:
        dt_utc = dt.replace(tzinfo=timezone.utc)
        return dt_utc - timedelta(hours=9)
        
    def utc_to_jst_with_time(self, dt: datetime) -> datetime:
        dt_jst = dt.replace(tzinfo=timezone(timedelta(hours=9)))
        return dt_jst + timedelta(hours=9)
