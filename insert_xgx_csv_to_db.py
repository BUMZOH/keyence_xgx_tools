import csv
import sqlite3
from ftplib import FTP
from io import BytesIO, TextIOWrapper
from pathlib import Path


# -------------------------------------
#  SETTINGS
# -------------------------------------
HOST = "192.168.8.3"
USER = "Administrator"
PASSWORD = "0000"
TARGET_DIR = "/SD2/xg/result"

DB_FILE = "xgx_inspection_data.db"
TABLE_NAME = "result"

DATETIME_COLUMNS = {
    "year",
    "month",
    "day",
    "hour",
    "minute",
    "second",
}

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / DB_FILE


# -------------------------------------
#  Get CSV files
# -------------------------------------
def get_csv_files(ftp):
    file_names = sorted(ftp.nlst(TARGET_DIR))

    csv_files = [
        file_name
        for file_name in file_names
        if file_name.lower().endswith(".csv")
    ]

    return csv_files


# -------------------------------------
#  Download CSV to RAM
# -------------------------------------
def download_csv_to_ram(ftp, remote_path):
    csv_data = BytesIO()

    ftp.retrbinary(
        f"RETR {remote_path}",
        csv_data.write,
    )

    csv_data.seek(0)

    return csv_data


# -------------------------------------
#  Insert CSV data to database
# -------------------------------------
def insert_csv_to_db(conn, csv_data, file_name):
    with TextIOWrapper(
        csv_data,
        encoding="utf-8-sig",
        newline="",
    ) as text_data:
        reader = csv.DictReader(text_data)

        if reader.fieldnames is None:
            raise ValueError(f"CSVヘッダがありません: {file_name}")

        header = reader.fieldnames

        # 日時カラムを除外
        data_columns = [
            column
            for column in header
            if column not in DATETIME_COLUMNS
        ]

        # CREATE TABLE文を生成
        column_definitions = ["measured_at TEXT NOT NULL"]
        column_definitions += [
            f'"{column}" REAL'
            for column in data_columns
        ]
        column_definitions.append(
            "UNIQUE (measured_at, prc_count)"
        )

        create_sql = (
            f'CREATE TABLE IF NOT EXISTS "{TABLE_NAME}" ('
            + ",".join(column_definitions)
            + ")"
        )

        # INSERT文を生成
        insert_columns = ["measured_at"] + data_columns
        column_names = ",".join(
            f'"{column}"'
            for column in insert_columns
        )
        placeholders = ",".join(
            "?"
            for _ in insert_columns
        )

        insert_sql = (
            f'INSERT OR IGNORE INTO "{TABLE_NAME}" '
            f"({column_names}) VALUES ({placeholders})"
        )

        conn.execute(create_sql)

        # CSVデータをDBへ登録
        for row in reader:
            measured_at = (
                f"{int(row['year']):04d}-"
                f"{int(row['month']):02d}-"
                f"{int(row['day']):02d} "
                f"{int(row['hour']):02d}:"
                f"{int(row['minute']):02d}:"
                f"{int(row['second']):02d}"
            )

            values = [measured_at]
            values += [
                float(row[column])
                for column in data_columns
            ]

            conn.execute(insert_sql, values)


# -------------------------------------
#  Main
# -------------------------------------
def main():
    with FTP(HOST) as ftp:
        ftp.login(USER, PASSWORD)
        print(ftp.getwelcome())

        csv_files = get_csv_files(ftp)

        if not csv_files:
            raise FileNotFoundError("CSVファイルがありません")

        with sqlite3.connect(DB_PATH) as conn:
            for file_name in csv_files:
                remote_path = f"{TARGET_DIR}/{file_name}"

                csv_data = download_csv_to_ram(
                    ftp,
                    remote_path,
                )

                insert_csv_to_db(
                    conn,
                    csv_data,
                    file_name,
                )

                # このCSVのDB登録を確定
                conn.commit()
                print("Inserted :", file_name)

                # DB登録成功後にXG-X側CSVを削除
                ftp.delete(remote_path)
                print("Deleted  :", file_name)

        print("Database :", DB_PATH)
        print("Table    :", TABLE_NAME)


# -------------------------------------
#  Entry point
# -------------------------------------
if __name__ == "__main__":
    try:
        main()

    except Exception as e:
        print("処理エラー")
        print(e)