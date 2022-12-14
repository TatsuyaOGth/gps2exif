import os
import glob
import argparse
import traceback
from gps import GoogleLocationHistory
from exif import ExifToolSubprocess
from utils import DateTimeHelper

FOOTPRINT_KEYWORD = 'gps2exif'
INDENT = '  '

def parse_arguments():
    parser = argparse.ArgumentParser(description='Adding GPS to Exif')
    parser.add_argument(
        'fpath', 
        help='Photo file path or directory.', 
        type=str)
    parser.add_argument(
        'gpsfile', 
        help='Path to Google location history(Records.json)', 
        type=str)
    parser.add_argument(
        '-f', '--filter', 
        help='File filter (ex. JPG, DNG. default = \'*\')', 
        default='*', 
        type=str)
    parser.add_argument(
        '-t', '--offsettime',
        help='Offset time original to be set if not in Exif., UTC is 0, default is 9(JST)',
        default='9.0',
        type=float)
    parser.add_argument(
        '-O', '--overwrite', 
        help='Overwrite GPS if has specific keyword (footprint) that this tool wrote in metadata.', 
        action='store_true')
    parser.add_argument(
        '-F', '--footprint', 
        help='Adding specific keyword (footprint) when add new GPS.', 
        action='store_true')
    parser.add_argument(
        '-R', '--readonly',
        help='Run without writing to exif.',
        action='store_true')
    return parser.parse_args()
    
    
def has_footprint(exif, f) -> bool:
    keywords = exif.get_keywords(f)
    if keywords is not None:
        if type(keywords) is str:
            return str(FOOTPRINT_KEYWORD) == keywords
        elif type(keywords) is list:
            return str(FOOTPRINT_KEYWORD) in keywords

def in_atdir(path):
    norm_path = os.path.normcase(os.path.normcase(os.path.split(path)[0]))
    dirs = str(norm_path).split(os.path.sep)
    for d in dirs:
        if d.startswith('@'):
            return True
    return False
    

def main(args):
    if args.readonly:
        print('*** READ ONLY MODE ***')
    
    # Instantiate
    loc = GoogleLocationHistory()
    dt_helper = DateTimeHelper()
    
    # Load GPS data from Google Location History
    loc_file_path = args.gpsfile
    print(f'Location file loading: {loc_file_path}')
    loc.load(loc_file_path)
    print(INDENT, 'OK!', loc.get_data_info())
    
    # Import photo file(s)
    photo_path = args.fpath
    print(f'Photo file(s) loading: {photo_path}')
    if os.path.exists(photo_path) == False:
        print(f'Could not find file or directory: {photo_path}')
        return
    files = []
    if os.path.isfile(photo_path):
        files.append(photo_path)
    elif os.path.isdir(photo_path):
        filter = args.filter
        if filter is None:
            filter = '*'
        path = photo_path + '/**/*.' + filter
        files = [
            p for p in glob.glob(path, recursive=True) 
            if os.path.isfile(p) and not in_atdir(p)
        ]
    print(INDENT, 'OK!')
        
    # Values for logging
    n_files = len(files)
    n_new = 0
    n_has = 0
    n_notdata = 0
    n_err = 0
    i = 0
    
    # ?????????1??????????????????????????????
    for f in files:
        i += 1
        print(os.path.relpath(f), f'({i}/{n_files})')
        
        try:
            # ???????????????????????????
            if os.path.isdir(f):
                print(INDENT, 'is directory')
                continue
            
            with ExifToolSubprocess() as exif:
                exif.no_write = args.readonly
                
                # ?????????GPS????????????????????????????????????
                gps_org = exif.get_gps_position(f)
                if gps_org is not None:
                    if args.overwrite and has_footprint(exif, f):
                        print(INDENT, 'OVERWRITE GPS')
                    else:
                        print(INDENT, 'already has GPS', gps_org)
                        n_has += 1
                        continue
                
                # ?????????????????????
                dt_org = exif.get_datetime_original(f)
                if dt_org is None:
                    print(INDENT, 'datetime original is not found in exif')
                    continue
                
                # ???????????????UTC?????????
                offset_time = exif.get_offsettime_original(f)
                if offset_time is None:
                    print(INDENT, f'offset-time original is not found in exif, will use {args.offsettime} from argument')
                    offset_time = args.offsettime
                else:
                    print(INDENT, f'offset-time original found: {offset_time}')
                dt_org_utc = dt_helper.offset_to_utc(dt_org, -offset_time)
                
                # ???????????????????????????????????????????????????GPS???????????????
                gps = loc.find_nearest(dt_org_utc)
                if gps is not None:
                    exif.set_gps_info(f, gps[0], gps[1], gps[2])
                    print(
                        INDENT,
                        'GPS added',
                        gps[0].strftime('%Y/%m/%d-%H:%M:%S') + '(UTC)',
                        gps[1],
                        gps[2])
                    if args.footprint:
                        exif.set_keywords(f, str(FOOTPRINT_KEYWORD))
                        print(INDENT, 'keyword added', FOOTPRINT_KEYWORD)
                    n_new += 1
                else:
                    print(INDENT, 'could not find nearest data', dt_org_utc)
                    n_notdata += 1
        except Exception as ex:
            print('[ERROR]', traceback.format_exc())
            n_err += 1
            
    # Print report
    print('REPORT:')
    print(INDENT, f'{n_new} GPS added | updated')
    print(INDENT, f'{n_has} already has GPS, not updated')
    print(INDENT, f'{n_notdata} could not find GPS')
    print(INDENT, f'{n_err} Error')
 
if __name__ == "__main__":
    args = parse_arguments()
    main(args)
    