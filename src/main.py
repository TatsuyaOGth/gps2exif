import os
import glob
import argparse
from gps import GoogleLocationHistory
from exif import ExifToolSubprocess, DateTimeHelper


def parse_arguments():
    parser = argparse.ArgumentParser(description='Adding GPS to Exif')
    parser.add_argument('fpath', help='Photo file path or directory.', type=str)
    parser.add_argument('gpsfile', help='Path to Google location history(Records.json)', type=str)
    parser.add_argument('-f', '--filter', help='File filter (ex. JPG, DNG. default = \'*\')', default='*', type=str)
    parser.add_argument(
        '-O', '--overwrite', help='Overwrite GPS if has specific keyword (footprint) that this tool wrote in metadata.', action='store_true')
    parser.add_argument(
        '-F', '--footprint', help='Adding specific keyword (footprint) when add new GPS.', action='store_true')
    parser.add_argument(
        '-k', '--keyword', help='Additional keyword (footprint) when added new GPS (default = gps2exif).', default='gps2exif', type=str)
    return parser.parse_args()
    
def has_footprint(args, exif, f) -> bool:
    if args.overwrite:
        keywords = exif.get_keywords(f)
        if keywords is not None:
            if type(keywords) is str:
                return str(args.keyword) == keywords
            elif type(keywords) is list:
                return str(args.keyword) in keywords
    return False
                

def main(args):
    # 必要なクラスのインスタンス化
    loc = GoogleLocationHistory()
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
        
    # ログ用の変数
    n_files = len(files)
    n_new = 0
    n_has = 0
    n_notdata = 0
    n_err = 0
    i = -1
    indent = '      '
    
    print(f'Photos={args.fpath}, GPS file={args.gpsfile}, N={n_files}')
    
    # 写真を1枚ずつ読み込んで処理
    for f in files:
        i += 1
        print(f, f'({i}/{n_files})')
        
        try:
            # ディレクトリは無視
            if os.path.isdir(f):
                print(indent, 'is directory')
                continue
            
            with ExifToolSubprocess() as exif:
                # すでにGPS情報がある場合は無視する
                gps_org = exif.get_gps_info(f)
                if gps_org is not None and has_footprint(args, exif, f) == False:
                    print(indent, 'already has GPS', gps_org)
                    n_has += 1
                    continue
                
                # 撮影時刻を取得
                dt_org = exif.get_datetime_original(f)
                if dt_org is None:
                    print(indent, 'datetime original is not found')
                    continue
                
                # ロケーション履歴から撮影時刻と近いGPS情報を検索
                gps = loc.find_nearest(dt_org)
                if gps is not None:
                    dt_utc = dt_helper.jst_to_utc_with_time(gps[0])
                    exif.set_gps_info(f, dt_utc, gps[1], gps[2])
                    print(
                        indent,
                        'GPS added',
                        gps[0].strftime('%y/%m/%d-%H:%M:%S'),
                        gps[1],
                        gps[2])
                    if args.footprint:
                        if not args.keyword:
                            print(indent, 'footprint requested but keyword is null or empty')
                        else:
                            exif.set_keywords(f, str(args.keyword))
                            print(indent, 'keyword added', args.keyword)
                    n_new += 1
                else:
                    print(indent, 'could not find nearest data')
                    n_notdata += 1
        except Exception as ex:
            print(indent, ex)
            n_err += 1
            
    
    # 処理結果を出力
    print(f'DONE: GPS added={n_new}, Already has GPS={n_has}, No data={n_notdata}, Error={n_err}')
 
if __name__ == "__main__":
    args = parse_arguments()
    main(args)
    