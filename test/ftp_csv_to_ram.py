import csv
import sqlite3
from ftplib import FTP
from io import BytesIO, TextIOWrapper


ftp = FTP("192.168.8.3")
ftp.login("Administrator", "0000")
print(ftp.getwelcome()) # 接続確認

csv_data = BytesIO()

ftp.retrbinary(
    "RETR /SD2/xg/result/sample.csv",
    csv_data.write,
)

csv_data.seek(0)

text_data = TextIOWrapper(
    csv_data,
    encoding="shift_jis",
    newline="",
)

reader = csv.reader(text_data)
for row in reader:
    print(row)

ftp.quit()