from pathlib import Path
from ftplib import FTP

# -------------------------------------
#  SETTINGS
# -------------------------------------
HOST = "192.168.8.3"
USER = "Administrator"
PASSWORD = "0000"
TARGET_DIR = "/SD2/xg/result"

BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "download"
DOWNLOAD_DIR.mkdir(exist_ok=True)


# -------------------------------------
#  MAIN PROCESS
# -------------------------------------
try:
    with FTP(HOST) as ftp:
        ftp.login(USER, PASSWORD)

        # 絶対パスを指定して一発で移動
        ftp.cwd(TARGET_DIR)
        print("Current Directory :", ftp.pwd())

        # CSVファイル一覧を取得
        file_names = ftp.nlst()

        for file_name in file_names:
            if not file_name.lower().endswith(".csv"):
                continue

            download_path = DOWNLOAD_DIR / file_name

            with download_path.open("wb") as file:
                ftp.retrbinary(f"RETR {file_name}", file.write)
            print("Downloaded: ", file_name)

            ftp.delete(file_name)
            print("Deleted   : ", file_name)
            
except Exception as e:
    print("FTP通信エラー")
    print(e)