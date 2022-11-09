import os
import glob
import argparse
from gps import GoogleLocationHistory
from exif import ExifToolSubprocess, DateTimeHelper

# LOCATION_FILE_PATH = '../data/Records.json'
# PHOTOS_DICTIONARY_PATH = '../data/test/'

def parse_arguments():
    parser = argparse.ArgumentParser(description='Adding GPS to Exif')
    parser.add_argument('fpath', help='Photo file path or directory')
    parser.add_argument('gpsfile', help='Path to Google location history(Records.json)')
    parser.add_argument('-f', '--filter', help='File filter (ex. DNG)', default='JPG')
    return parser.parse_args()

def main(args):
    print(f'Input path = {args.fpath}, GPS data file = {args.gpsfile}')
    
    # 必要なクラスのインスタンス化
    loc = GoogleLocationHistory()
    exif = ExifToolSubprocess()
    dt_helper = DateTimeHelper()
    
    # このファイルのパスを取得
    mydir = os.path.dirname(os.path.abspath(__file__))
    
    # ロケーション履歴を読み込み
    loc_file_path = os.path.join(mydir, args.gpsfile)
    loc.load(loc_file_path)
    
    # 写真ファイルへのパス（ディレクトリの場合は直下のファイル
    photo_path = os.path.join(mydir, args.fpath)
    if os.path.exists(photo_path) == False:
        print(f'Could not find file or directory: {photo_path}')
        return
    files = []
    if os.path.isfile(photo_path):
        files.append(photo_path)
    elif os.path.isdir(photo_path):
        filter = args.filter
        if filter is None:
            filter = 'JPG'
        path = photo_path + '/**/*.' + filter
        files = glob.glob(path, recursive=True)
        
    # カウンターを用意
    n_new = 0
    n_has = 0
    n_miss = 0
    
    # 写真を1枚ずつ読み込んで処理
    for f in files:
        # ディレクトリは無視
        if os.path.isdir(f):
            continue
        
        # すでにGPS情報がある場合は無視する
        gps_org = exif.get_gps_info(f)
        if gps_org is not None:
            print(f'{os.path.basename(f)} already has GPS Info, {gps_org}')
            n_has += 1
            continue
        
        # ロケーション履歴から撮影時刻と近いGPS情報を検索
        dt_org = exif.get_datetime_original(f)
        gps = loc.find_nearest(dt_org)
        if gps is not None:
            print(
                os.path.basename(f),
                'set new GPS Info',
                gps[0].strftime('%y/%m/%d-%H:%M:%S'),
                gps[1],
                gps[2])
            dt_utc = dt_helper.jst_to_utc_with_time(gps[0])
            exif.set_gps_info(f, dt_utc, gps[1], gps[2])
            n_new += 1
        else:
            print(os.path.basename(f), 'Could not find nearest data')
            n_miss += 1
    
    # 処理結果を出力
    print(f'GPS added = {n_new}, Already has GPS = {n_has}, Error = {n_miss}')
 
if __name__ == "__main__":
    args = parse_arguments()
    main(args)
    