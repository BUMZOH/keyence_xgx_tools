import csv
import sqlite3
from pathlib import Path


# -------------------------------------
#  SETTINGS
# -------------------------------------
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
DOWNLOAD_DIR = BASE_DIR / "download"
DB_PATH = BASE_DIR / DB_FILE


# -------------------------------------
#  MAIN PROCESS
# -------------------------------------
try:
    # CSVファイル一覧を取得
    csv_files = sorted(DOWNLOAD_DIR.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError("CSVファイルがありません")

    # 最初のCSVファイルからヘッダを取得
    with csv_files[0].open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file)
        header = next(reader)

    # 日時カラムを除外
    data_columns = [
        column for column in header if column not in DATETIME_COLUMNS
    ]

    # CREATE TABLE文を生成
    column_definitions = ["measured_at TEXT NOT NULL"]
    column_definitions += [f'"{column}" REAL' for column in data_columns]
    column_definitions.append("UNIQUE (measured_at, prc_count)")

    create_sql = (
        f'CREATE TABLE IF NOT EXISTS "{TABLE_NAME}" ('
        + ",".join(column_definitions)
        + ")"
    )

    # INSERT分を生成
    insert_columns = ["measured_at"] + data_columns
    column_names = ",".join(f'"{column}"' for column in insert_columns)
    placeholders = ",".join("?" for _ in insert_columns)

    insert_sql = (
        f'INSERT OR IGNORE INTO "{TABLE_NAME}" ({column_names}) '
        f"VALUES ({placeholders})"
    )

    # DB・テーブル作成
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(create_sql)

        # CSVファイルを順番に処理
        for csv_file in csv_files:
            with csv_file.open("r", encoding="utf-8-sig", newline="") as file:
                reader = csv.DictReader(file)

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
                    values += [float(row[column]) for column in data_columns]

                    conn.execute(insert_sql, values)

            print("inserted: ", csv_file.name)

    print("Database :", DB_PATH)
    print("Table    :", TABLE_NAME)
    print("Columns  :", ["measured_at"] + data_columns)


except Exception as e:
    print("DB作成エラー")
    print(e)













