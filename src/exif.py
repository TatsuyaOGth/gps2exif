from exiftool import ExifToolHelper
from exiftool.exceptions import ExifToolExecuteError
from datetime import datetime, timezone, timedelta
from time import time_ns

class ExifToolSubprocess:
    
    def __init__(self):
        self.et = ExifToolHelper()
        self.no_write = False
        
    def __enter__(self):
        self.et.run()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if exception_type is ExifToolExecuteError:
            print('STDERR', exception_value.stderr)
            print('STDOUT', exception_value.stdout)
        self.et.terminate()
    
    def get_datetime_original(self, fname):
        dt_s = self._get_exif_data(fname, 'DateTimeOriginal')
        if not dt_s:
            return None
        dt = datetime.strptime(dt_s, '%Y:%m:%d %H:%M:%S')
        dt_jst = dt.replace(tzinfo=timezone(timedelta(hours=9)))
        return dt_jst
            
    def get_gps_info(self, fname):
        lat = self._get_exif_data(fname, 'GPSLatitude')
        lon = self._get_exif_data(fname, 'GPSLongitude')
        if not lat or not lon:
            return None
        return (float(lat), float(lon))
        
    def get_gps_datetime(self, fname):
        dt_s = self._get_exif_data(fname, 'GPSDateStamp')
        tm_s = self._get_exif_data(fname, 'GPSTimeStamp')
        if not dt_s or not tm_s:
            return None
        dt = datetime.strptime(dt_s, '%Y:%m:%d')
        tm = datetime.strptime(tm_s, '%H:%M:%S')
        return datetime.combine(dt.date(), tm.time(), tzinfo=timezone.utc)
        
    def set_gps_info(self, fname, dt: datetime, lat, lon):
        if self.no_write:
            return
        self._set_exif_data(fname, 'GPSVersionID', '2 3 0 0')
        self._set_exif_data(fname, 'GPSLatitudeRef', 'N')
        self._set_exif_data(fname, 'GPSLongitudeRef', 'E')
        self._set_exif_data(fname, 'GPSLatitude', lat)
        self._set_exif_data(fname, 'GPSLongitude', lon)
        self._set_exif_data(fname, 'GPSDateStamp', dt.strftime('%Y:%m:%d'))
        self._set_exif_data(fname, 'GPSTimeStamp', dt.strftime('%H:%M:%S'))
        
    def set_keywords(self, fname, keyword):
        if self.no_write:
            return
        self._add_keyword_if_not_has(fname, 'Keywords', keyword, 'IPTC')
        self._add_keyword_if_not_has(fname, 'Subject', keyword, 'XMP')
        
    def get_keywords(self, fname):
        return self._get_exif_data(fname, 'Keywords', 'IPTC')
        
    def print_all(self, fname):
        for d in self.et.get_metadata(fname):
            for k, v in d.items():
                print(f'{k} = {v}')
            
    def _get_exif_data(self, fname, tag_name, tag_header = 'EXIF'):
        tags = self.et.get_tags(fname, tag_name)

        if tags is None:
            return None

        if len(tags) == 0:
            return None

        key = tag_header + ':' + tag_name
        if key not in tags[0].keys():
            return None

        return tags[0][key]
        
    def _set_exif_data(self, fname, tag_name, value):
        if self.no_write:
            return
        self.et.set_tags(
            fname,
            tags={tag_name: value},
            params=['-P', '-overwrite_original']
        )
        
    def _add_keyword_if_not_has(self, fname, tag_name, keyword, tag_header):
        words = self._get_exif_data(fname, tag_name, tag_header)
        if words is None:
            self._set_exif_data(fname, tag_name, [keyword])
        elif type(words) is str:
            if words != keyword:
                self._set_exif_data(fname, tag_name, [words, keyword])
        elif type(words) is list:
            if keyword not in words:
                words.append(keyword)
                self._set_exif_data(fname, tag_name, words)



class DateTimeHelper:
    
    def jst_to_utc_with_time(self, dt: datetime) -> datetime:
        dt_utc = dt.replace(tzinfo=timezone.utc)
        return dt_utc - timedelta(hours=9)
        
    def utc_to_jst_with_time(self, dt: datetime) -> datetime:
        dt_jst = dt.replace(tzinfo=timezone(timedelta(hours=9)))
        return dt_jst + timedelta(hours=9)
