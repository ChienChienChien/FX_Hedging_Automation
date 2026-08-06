import re
import time
import datetime
from pathlib import Path

import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from dglib.config.globalvar import GlobalVar
from dglib.db.dbutils import pd
from dglib.db.dbutils import DB
from dglib.message.TeamsMsg import TeamsMsg
from dglib.log.nlogE import Elog

GlobalVar.Init(GlobalVar.dglib_DBConnStr_QUANTDATA)
TEAMS_URL = 'https://default97876bedbb9a4617802b94c62e7837.b5.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/8d8c84203091489ebb6973bab91a0089/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=0Pv9WIgcWevcTnJdt7fsMx9XCjWAUo8Ips0gq8usoIM'


# =========================
# 基本設定
# =========================

DATA_DATE_FORMAT = "%Y/%m/%d"

BOT_HOME_URL = "https://rate.bot.com.tw/xrt?Lang=zh-TW"
BOT_TXT_URL = "https://rate.bot.com.tw/xrt/fltxt/0/day"

RAW_FILE_PATTERN = "ExchangeRate@*.txt"

CHALLENGE_KEYWORDS = [
    "Challenge Validation",
    "verify-url",
    "sec-cpt-if",
    "Challenge Content",
]


# 台銀 TXT 原始欄位結構：
# 幣別, 匯率, 現金, 即期, 遠期10天...遠期180天, 匯率, 現金, 即期, 遠期10天...遠期180天
#
# 重新命名後的欄位：
WIDE_COLUMNS = [
    "ccy",
    "bid_label",
    "cash_bid",
    "spot_bid",
    "forward_10d_bid",
    "forward_30d_bid",
    "forward_60d_bid",
    "forward_90d_bid",
    "forward_120d_bid",
    "forward_150d_bid",
    "forward_180d_bid",
    "ask_label",
    "cash_ask",
    "spot_ask",
    "forward_10d_ask",
    "forward_30d_ask",
    "forward_60d_ask",
    "forward_90d_ask",
    "forward_120d_ask",
    "forward_150d_ask",
    "forward_180d_ask",
]


FORWARD_FIELD_MAP = [
    ("10D", "forward_10d_bid", "forward_10d_ask"),
    ("30D", "forward_30d_bid", "forward_30d_ask"),
    ("60D", "forward_60d_bid", "forward_60d_ask"),
    ("90D", "forward_90d_bid", "forward_90d_ask"),
    ("120D", "forward_120d_bid", "forward_120d_ask"),
    ("150D", "forward_150d_bid", "forward_150d_ask"),
    ("180D", "forward_180d_bid", "forward_180d_ask"),
]


# =========================
# 路徑處理
# =========================

def get_project_root():
    """
    取得專案資料夾。

    .py 執行時：使用目前檔案所在資料夾。
    Notebook / interactive 環境：使用目前工作目錄。
    """
    try:
        return Path(__file__).resolve().parent
    except NameError:
        return Path.cwd()


def get_raw_data_dir():
    """
    專案資料夾底下的 raw_data 資料夾。
    不存在就建立。
    """
    raw_data_dir = get_project_root() / "raw_data"
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    return raw_data_dir


# =========================
# Selenium 下載 TXT
# =========================

def is_challenge_text(text):
    return any(keyword in text for keyword in CHALLENGE_KEYWORDS)


def page_has_challenge(driver):
    try:
        title = driver.title or ""
        html = driver.page_source or ""
        return is_challenge_text(title) or is_challenge_text(html)
    except Exception:
        return False


def wait_until_not_challenge(driver, timeout=180):
    """
    等待 Challenge 頁面通過。

    若 headless=False，且台銀需要人工驗證，可以在打開的 Chrome 中手動處理。
    """
    end_time = time.time() + timeout

    while time.time() < end_time:
        if not page_has_challenge(driver):
            return True
        time.sleep(2)

    return False


def get_completed_txt_files(raw_data_dir):
    """
    取得 raw_data 裡已完成下載的 ExchangeRate@*.txt。
    """
    raw_data_dir = Path(raw_data_dir)

    files = []
    for p in raw_data_dir.glob(RAW_FILE_PATTERN):
        if not p.is_file():
            continue

        if p.suffix.lower() in [".crdownload", ".tmp", ".part"]:
            continue

        files.append(p)

    return files


def wait_for_new_txt_download(raw_data_dir, start_time, timeout=90):
    """
    等待 raw_data 出現新的 ExchangeRate@*.txt。
    """
    raw_data_dir = Path(raw_data_dir)
    end_time = time.time() + timeout

    while time.time() < end_time:
        temp_files = list(raw_data_dir.glob("*.crdownload"))

        candidates = [
            p for p in get_completed_txt_files(raw_data_dir)
            if p.stat().st_mtime >= start_time - 1
        ]

        if candidates and not temp_files:
            return max(candidates, key=lambda p: p.stat().st_mtime)

        time.sleep(1)

    raise TimeoutError("等待台銀 TXT 下載逾時，raw_data 中沒有出現新的 ExchangeRate@*.txt。")


def save_browser_text_to_raw_data(driver, raw_data_dir):
    """
    備援：如果 Chrome 沒有下載，而是直接顯示文字內容，
    就把 body 文字存成 ExchangeRate@YYYYMMDDHHMM.txt。

    一般情況下你目前不一定會用到，因為 Selenium 已經會下載 txt。
    """
    body_text = driver.find_element(By.TAG_NAME, "body").text

    if is_challenge_text(body_text):
        raise RuntimeError("瀏覽器仍停在 Challenge Validation，沒有取得台銀 TXT。")

    if "幣別" not in body_text or "遠期10天" not in body_text:
        raise RuntimeError("瀏覽器內容不像台銀 TXT，無法存檔解析。")

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
    file_path = Path(raw_data_dir) / f"ExchangeRate@{timestamp}.txt"
    file_path.write_text(body_text, encoding="utf-8-sig")

    return file_path


def selenium_download_bot_txt(raw_data_dir=None, headless=False):
    """
    用 Selenium 開啟瀏覽器，下載台銀 TXT 到 raw_data。

    建議先用 headless=False，因為你目前會遇到 Challenge。
    """
    if raw_data_dir is None:
        raw_data_dir = get_raw_data_dir()

    raw_data_dir = Path(raw_data_dir).resolve()

    chrome_options = webdriver.ChromeOptions()

    prefs = {
        "download.default_directory": str(raw_data_dir),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "profile.default_content_settings.popups": 0,
    }

    chrome_options.add_experimental_option("prefs", prefs)

    if headless:
        chrome_options.add_argument("--headless=new")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        if headless:
            driver.execute_cdp_cmd(
                "Page.setDownloadBehavior",
                {
                    "behavior": "allow",
                    "downloadPath": str(raw_data_dir),
                }
            )

        driver.get(BOT_HOME_URL)

        if not wait_until_not_challenge(driver, timeout=180):
            raise RuntimeError("台銀 Challenge Validation 未通過，無法下載 TXT。")

        start_time = time.time()

        try:
            # 點擊首頁的「下載文字檔」連結
            txt_link = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'a[href*="/xrt/fltxt/0/day"]')
                )
            )
            driver.execute_script("arguments[0].click();", txt_link)

        except TimeoutException:
            # 找不到連結時，直接開文字檔端點
            driver.get(BOT_TXT_URL)

        try:
            downloaded_file = wait_for_new_txt_download(
                raw_data_dir=raw_data_dir,
                start_time=start_time,
                timeout=90
            )
            return downloaded_file

        except TimeoutError:
            # 備援：若 Chrome 直接顯示文字內容，就把 body 存成 txt
            driver.switch_to.window(driver.window_handles[-1])
            downloaded_file = save_browser_text_to_raw_data(driver, raw_data_dir)
            return downloaded_file

    finally:
        driver.quit()


def get_latest_exchange_rate_txt(raw_data_dir=None):
    """
    取得 raw_data 資料夾中最新的 ExchangeRate@*.txt。

    優先用檔名時間戳判斷最新；
    若檔名不符合格式，才退回用檔案修改時間。
    """
    if raw_data_dir is None:
        raw_data_dir = get_raw_data_dir()

    files = get_completed_txt_files(raw_data_dir)

    if not files:
        raise FileNotFoundError(f"raw_data 沒有 ExchangeRate@*.txt：{raw_data_dir}")

    def sort_key(p):
        try:
            return parse_exchange_rate_filename(p)
        except ValueError:
            return datetime.datetime.fromtimestamp(p.stat().st_mtime)

    return max(files, key=sort_key)


# =========================
# 檔名時間戳處理
# =========================

def parse_exchange_rate_filename(raw_file_path):
    """
    從台銀檔名擷取時間戳。

    ExchangeRate@202606301601.txt
    -> datetime.datetime(2026, 6, 30, 16, 1)
    """
    raw_file_path = Path(raw_file_path)
    filename = raw_file_path.name

    match = re.search(r"ExchangeRate@(\d{12})\.txt$", filename)

    if not match:
        raise ValueError(f"檔名不符合台銀格式 ExchangeRate@YYYYMMDDHHMM.txt：{filename}")

    return datetime.datetime.strptime(match.group(1), "%Y%m%d%H%M")


def get_page_datetime(raw_file_path):
    """
    給資料庫使用的資料日期。

    ExchangeRate@202606301601.txt
    -> 20260630
    """
    quote_dt = parse_exchange_rate_filename(raw_file_path)
    return quote_dt.strftime(DATA_DATE_FORMAT)


def get_quote_datetime(raw_file_path):
    """
    完整報價時間。

    ExchangeRate@202606301601.txt
    -> 2026-06-30 16:01:00
    """
    quote_dt = parse_exchange_rate_filename(raw_file_path)
    return quote_dt.strftime("%Y-%m-%d %H:%M:%S")


def get_file_timestamp(raw_file_path):
    """
    檔名中的原始時間戳。

    ExchangeRate@202606301601.txt
    -> 202606301601
    """
    quote_dt = parse_exchange_rate_filename(raw_file_path)
    return quote_dt.strftime("%Y%m%d%H%M")


# =========================
# TXT 讀取與解析
# =========================

def read_text_file(raw_file_path):
    """
    讀取台銀 TXT。
    依照你上傳的檔案，編碼是 utf-8-sig。
    這裡仍保留 cp950 / big5 作為備援。
    """
    raw_file_path = Path(raw_file_path)

    for encoding in ["utf-8-sig", "utf-8", "cp950", "big5"]:
        try:
            return raw_file_path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue

    return raw_file_path.read_text(encoding="utf-8", errors="replace")


def split_exchange_rate_line(line):
    """
    台銀 TXT 是空白分隔。
    每一列預期會切成 21 個 tokens。
    """
    return re.split(r"\s+", line.strip())


def read_exchange_rate_txt_wide(raw_file_path):
    """
    讀取台銀 TXT，轉成寬表。

    輸出欄位：
    ccy
    bid_label
    cash_bid
    spot_bid
    forward_10d_bid
    forward_30d_bid
    forward_60d_bid
    forward_90d_bid
    forward_120d_bid
    forward_150d_bid
    forward_180d_bid
    ask_label
    cash_ask
    spot_ask
    forward_10d_ask
    forward_30d_ask
    forward_60d_ask
    forward_90d_ask
    forward_120d_ask
    forward_150d_ask
    forward_180d_ask
    """
    txt_text = read_text_file(raw_file_path)

    if is_challenge_text(txt_text):
        raise RuntimeError("讀到的是 Challenge Validation，不是台銀 TXT。")

    lines = [
        line for line in txt_text.splitlines()
        if line.strip()
    ]

    if len(lines) < 2:
        raise ValueError(f"TXT 沒有資料列：{raw_file_path}")

    header_tokens = split_exchange_rate_line(lines[0])

    if len(header_tokens) != len(WIDE_COLUMNS):
        raise ValueError(
            f"TXT 表頭欄位數異常，預期 {len(WIDE_COLUMNS)} 欄，"
            f"實際 {len(header_tokens)} 欄。header={header_tokens}"
        )

    data_rows = []

    for line in lines[1:]:
        tokens = split_exchange_rate_line(line)

        if len(tokens) != len(WIDE_COLUMNS):
            raise ValueError(
                f"TXT 資料列欄位數異常，預期 {len(WIDE_COLUMNS)} 欄，"
                f"實際 {len(tokens)} 欄。line={line}"
            )

        data_rows.append(tokens)

    df = pd.DataFrame(data_rows, columns=WIDE_COLUMNS)

    invalid_label_df = df[
        (df["bid_label"] != "本行買入") |
        (df["ask_label"] != "本行賣出")
    ]

    if len(invalid_label_df) > 0:
        raise ValueError(
            "TXT 的買入 / 賣出標籤不符合預期，可能格式已變更。"
            f"異常資料：{invalid_label_df[['ccy', 'bid_label', 'ask_label']].to_dict('records')}"
        )

    numeric_cols = [
        col for col in WIDE_COLUMNS
        if col not in ["ccy", "bid_label", "ask_label"]
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def get_forward_table(ccy, raw_file_path=None):
    """
    從 raw_data 最新台銀 TXT 取得指定幣別遠期匯率。

    回傳欄位：
    tenor
    bid
    offer
    date
    quote_datetime
    file_timestamp
    ccypair
    source_file
    """
    if raw_file_path is None:
        raw_file_path = get_latest_exchange_rate_txt()

    raw_file_path = Path(raw_file_path)
    ccy = ccy.upper()

    wide_df = read_exchange_rate_txt_wide(raw_file_path)

    matched = wide_df[wide_df["ccy"].str.upper() == ccy]

    if matched.empty:
        raise ValueError(f"台銀 TXT 中找不到幣別：{ccy}")

    row = matched.iloc[0]

    data_date = get_page_datetime(raw_file_path)
    quote_datetime = get_quote_datetime(raw_file_path)
    file_timestamp = get_file_timestamp(raw_file_path)

    records = []

    for tenor, bid_col, ask_col in FORWARD_FIELD_MAP:
        records.append({
            "tenor": tenor,
            "bid": row[bid_col],
            "offer": row[ask_col],
            "date": data_date,
            "quote_datetime": quote_datetime,
            "file_timestamp": file_timestamp,
            "ccypair": ccy + "TWD",
            "source_file": raw_file_path.name,
        })

    df = pd.DataFrame(records)

    if df[["bid", "offer"]].isna().any().any():
        raise ValueError(f"{ccy} 遠期匯率中有無法轉成數字的值。df={df}")

    return df[
        [
            "tenor",
            "bid",
            "offer",
            "date",
            "quote_datetime",
            "file_timestamp",
            "ccypair",
            "source_file",
        ]
    ]


# =========================
# 寫入資料庫
# =========================

def insert_price(df):
    df = df.copy()

    # get_forward_table 已經產生 10D / 30D / ...。
    # 這行保留防呆，避免 tenor 未來變成「遠期10天」或「Forward-10Days」。
    df["tenor"] = df["tenor"].apply(
        lambda x: re.findall(r"\d+", str(x))[0] + "D"
    )

    for index, row in df.iterrows():
        InstrumentId = row["ccypair"] + "-" + row["tenor"]
        CurrencyId = row["ccypair"]
        DataDate = row["date"]
        SettleP = 0.0
        DataSource = "twbank"
        MUser = "ur08173"
        bid = row["bid"]
        ask = row["offer"]

        GlobalVar.Prices.insert(
            InstrumentId,
            CurrencyId,
            DataDate,
            SettleP,
            DataSource,
            MUser,
            BidP=bid,
            AskP=ask
        )


def test_data(data_date):
    sqlstr = f"""
    select * from price
    where InstrumentId in ('EURTWD-10D','EURTWD-120D','EURTWD-150D','EURTWD-180D',
                           'EURTWD-30D','EURTWD-60D','EURTWD-90D','USDTWD-10D',
                           'USDTWD-120D','USDTWD-150D','USDTWD-180D','USDTWD-30D',
                           'USDTWD-60D','USDTWD-90D')
    and datadate = '{data_date}'
    """

    df = DB.query(sqlstr, GlobalVar.dglib_DBConnStr_QUANTDATA)

    return len(df) == 14


# =========================
# 主程式
# =========================

if __name__ == "__main__":
    try:
        crawl_ccys = ["USD", "EUR"]

        raw_data_dir = get_raw_data_dir()

        # 1. 用 Selenium 開啟瀏覽器並下載 TXT 到 raw_data
        downloaded_file = selenium_download_bot_txt(
            raw_data_dir=raw_data_dir,
            headless=False
        )

        Elog.info(f"【dgdf】 台銀 TXT 下載完成：{downloaded_file}")

        # 2. 從 raw_data 讀取最新的 ExchangeRate@*.txt
        latest_file = get_latest_exchange_rate_txt(raw_data_dir)

        data_date = get_page_datetime(latest_file)
        quote_datetime = get_quote_datetime(latest_file)
        file_timestamp = get_file_timestamp(latest_file)

        Elog.info(f"【dgdf】 使用台銀 TXT：{latest_file}")
        Elog.info(f"【dgdf】 資料日期：{data_date}")
        Elog.info(f"【dgdf】 報價時間：{quote_datetime}")
        Elog.info(f"【dgdf】 檔名時間戳：{file_timestamp}")

        # 3. 解析 USD / EUR 遠期匯率並寫入資料庫
        for ccy in crawl_ccys:
            df = get_forward_table(
                ccy=ccy,
                raw_file_path=latest_file
            )

            Elog.info(f"【dgdf】 {ccy} 解析筆數：{len(df)}")

            insert_price(df)

        # 4. 檢查資料是否完整
        if test_data(data_date):
            TeamsMsg.send_by_request("台銀爬蟲：成功", TEAMS_URL)
        else:
            TeamsMsg.send_by_request("台銀爬蟲：失敗(可能有漏資料)", TEAMS_URL)
            Elog.info("【dgdf】 Crawl Failed, something went wrong!")

    except Exception as err:
        err_msg = "【dgdf】 Crawl Failed：" + str(err)
        TeamsMsg.send_by_request("台銀爬蟲：失敗", TEAMS_URL)
        Elog.info(err_msg)