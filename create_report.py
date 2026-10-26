import subprocess
import sys
from datetime import datetime
from pathlib import Path

import papermill as pm


# ================================================
#   Settings
# ================================================
NOTEBOOK_PATH = "xgx_data_analysis.ipynb"
OUTPUT_NOTEBOOK_PATH = "output_report.ipynb"

DATA_DIR = Path("data")
DESKTOP_PATH = Path.home() / "Desktop"


# ================================================
#   Functions
# ================================================
def normalize_datetime(value, default_time):
    formats = [
        "%Y-%m-%d %H:%M",
        "%y-%m-%d %H:%M",
        "%m-%d %H:%M",
        "%Y-%m-%d",
        "%y-%m-%d",
        "%m-%d",
    ]

    for format_string in formats:
        try:
            date = datetime.strptime(value, format_string)

            if format_string.startswith("%m-"):
                date = date.replace(year=datetime.now().year)

            if "%H:%M" not in format_string:
                date = date.replace(
                    hour=default_time.hour,
                    minute=default_time.minute,
                    second=default_time.second,
                )

            return date.strftime("%Y-%m-%d %H:%M:%S")

        except ValueError:
            continue

    raise ValueError(
        "日時は YYYY-M-D HH:MM / YY-M-D HH:MM / M-D HH:MM "
        "または日付のみで入力してください。"
    )


def select_db_file():
    db_files = sorted(DATA_DIR.glob("*.db"))

    if not db_files:
        raise FileNotFoundError("dataフォルダにDBファイルがありません")

    print("DBファイルを選択してください")
    print()

    for index, db_file in enumerate(db_files, start=1):
        print(f"{index}: {db_file}")

    print()

    while True:
        value = input("番号: ")

        if value.isdigit():
            index = int(value)

            if 1 <= index <= len(db_files):
                return db_files[index - 1]

        print("正しい番号を入力してください")


def confirm_csv_output():
    while True:
        value = input("CSVファイルを出力しますか？ [y/N]: ")
        value = value.strip().lower()

        if value == "y":
            return True

        if value in ("", "n"):
            return False

        print("Y または N を入力してください")



# ================================================
#   Select database
# ================================================
db_file = select_db_file()


# ================================================
#   Input datetime
# ================================================
start_datetime = normalize_datetime(
    input("開始日時: "),
    datetime.min.time(),
)

end_datetime = normalize_datetime(
    input("終了日時: "),
    datetime.max.time().replace(microsecond=0),
)

csv_output = confirm_csv_output()

start_datetime_text = datetime.strptime(
    start_datetime,
    "%Y-%m-%d %H:%M:%S",
).strftime("%Y%m%d_%H%M%S")

end_datetime_text = datetime.strptime(
    end_datetime,
    "%Y-%m-%d %H:%M:%S",
).strftime("%Y%m%d_%H%M%S")

output_file_name = (
    f"xgx_data_analysis_"
    f"{start_datetime_text}_{end_datetime_text}"
)

output_html_path = DESKTOP_PATH / f"{output_file_name}.html"
output_csv_path = DESKTOP_PATH / f"{output_file_name}.csv"


# ================================================
#   Execute notebook
# ================================================
print()
print(f"対象期間: {start_datetime} ～ {end_datetime}")
print("Notebookを実行しています...")

pm.execute_notebook(
    NOTEBOOK_PATH,
    OUTPUT_NOTEBOOK_PATH,
    parameters={
        "DB_FILE": str(db_file),
        "START_DATETIME": start_datetime,
        "END_DATETIME": end_datetime,
        "CSV_OUTPUT": csv_output,
        "CSV_FILE": str(output_csv_path),
    },
)

print("Notebookの実行が完了しました。")


# ================================================
#   Export HTML
# ================================================
print("HTMLを作成しています...")

subprocess.run(
    [
        sys.executable,
        "-m",
        "jupyter",
        "nbconvert",
        "--to",
        "html",
        "--no-input",
        "--no-prompt",
        "--output",
        output_html_path,
        OUTPUT_NOTEBOOK_PATH,
    ],
    check=True,
)

print(f"HTMLの作成が完了しました: {output_html_path}")


# ================================================
#   Delete temporary notebook
# ================================================
Path(OUTPUT_NOTEBOOK_PATH).unlink()

print("一時Notebookを削除しました。")