import os
import glob
from loc_hist import LocationHistory
from exif import ExifToolSubprocess, DateTimeHelper

LOCATION_FILE_PATH = '../data/Records.json'
PHOTOS_DICTIONARY_PATH = '../data/test/'


def main():
    # 必要なクラスのインスタンス化
    loc = LocationHistory()
    exif = ExifToolSubprocess()
    dt_helper = DateTimeHelper()
    
    # このファイルのパスを取得
    mydir = os.path.dirname(os.path.abspath(__file__))
    
    # ロケーション履歴を読み込み
    loc_file_path = os.path.join(mydir, LOCATION_FILE_PATH)
    loc.load(loc_file_path)
    
    # 写真を1枚ずつ読み込んで処理
    photo_dir_path = os.path.join(mydir, PHOTOS_DICTIONARY_PATH)
    files = glob.glob(photo_dir_path + '*.JPG')
    for f in files:
        # すでにGPS情報がある場合は無視する
        gps_org = exif.get_gps_info(f)
        if gps_org is not None:
            print(os.path.basename(f), 'Has GPS', gps_org)
            print('GPS DateTime', exif.get_gps_datetime(f))
            continue
        
        # ロケーション履歴から撮影時刻と近いGPS情報を検索
        dt_org = exif.get_datetime_original(f)
        gps = loc.find_nearest(dt_org)
        if gps is not None:
            print(
                os.path.basename(f),
                'Set new GPS',
                gps[0].strftime('%y/%m/%d-%H:%M:%S'),
                gps[1],
                gps[2])
            dt_utc = dt_helper.jst_to_utc_with_time(gps[0])
            exif.set_gps_info(f, dt_utc, gps[1], gps[2])
        else:
            print(f, 'Could not find nearest data')
 
if __name__ == "__main__":
    main()