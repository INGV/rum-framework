#!/usr/bin/env python3

import requests
import datetime
import os
import glob
import argparse
import logging
from email.mime.text import MIMEText
import smtplib
from dateutil import parser


STATION_URL = "https://webservices.ingv.it/fdsnws/station/1/query?network=*&level=channel&format=text"

# default parameters
days_before = 2
SDS_ROOT = "/mnt/trust-archive/trust/"
BAD_ROOT = "/mnt/trust-archive/bad/"

# mail config
MAIL_ENABLED = False
SMTP_SERVER = "localhost"
MAIL_FROM = "sds-check@ingv.it"
MAIL_TO = ["data-manager@ingv.it"]

ERROR_MAP = {
    "0": "EMPTY_OR_UNREADABLE",
    "1": "BROKEN_FILE",
    "2": "SDS_VALIDATION_ERROR",
    "21": "UNEXPECTED_ERROR_STEP_2",
    "3": "RATE_ERROR",
    "31": "UNEXPECTED_ERROR_STEP_3",
    "4": "EPOCH_OUT_OF_RANGE",
    "41": "EPOCH_NO_DATA"
}

# --------------------------------------------------
# logging
# --------------------------------------------------

def setup_logging(level):

    numeric = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        level=numeric,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler("check_sds_ingestion.log", mode="w"),
            logging.StreamHandler()
        ]
    )

    logging.info("Logging started")


# --------------------------------------------------
# CLI arguments
# --------------------------------------------------

def parse_args():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--days-back",
        type=int,
        default=days_before,
        help="Number of days before today to check"
    )

    parser.add_argument(
        "--sds-root",
        type=str,
        default=SDS_ROOT,
        help="SDS repository root"
    )

    parser.add_argument(
        "--bad-root",
        type=str,
        default=BAD_ROOT,
        help="BAD repository root"
    )

    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO)"
    )

    return parser.parse_args()


# --------------------------------------------------
# date helpers
# --------------------------------------------------

def get_target_day(days_back):

    target_date = datetime.date.today() - datetime.timedelta(days=days_back)

    year = target_date.year
    jday = target_date.timetuple().tm_yday

    return target_date, year, f"{jday:03d}"


# --------------------------------------------------
# station service
# --------------------------------------------------

def fetch_station_channels():

    logging.info("Fetching station metadata")

    r = requests.get(STATION_URL)
    r.raise_for_status()

    lines = r.text.splitlines()

    channels = []

    for line in lines:

        if line.startswith("#"):
            continue

        parts = line.split("|")

        channels.append({
            "net": parts[0].strip(),
            "sta": parts[1].strip(),
            "loc": parts[2].strip(),
            "cha": parts[3].strip(),
            "start": parts[15].strip(),
            "end": parts[16].strip()
        })

    logging.info(f"Total channels fetched: {len(channels)}")

    return channels


# --------------------------------------------------
# channel activity
# --------------------------------------------------

def channel_active(channel, target_date):

    start = parser.parse(channel["start"]).date()

    end = parser.parse(channel["end"]).date() if channel["end"] else None

    if start > target_date:
        return False

    if end and end < target_date:
        return False

    return True


# --------------------------------------------------
# expected files
# --------------------------------------------------

def build_expected_files(channels, target_date, year, jday):

    expected = set()

    skipped_non_waveform = 0
    skipped_inactive = 0

    VALID_BAND_CODES = {"H", "B", "E", "S", "M", "L", "V", "U"}

    for ch in channels:

        if not channel_active(ch, target_date):
            skipped_inactive += 1
            continue

        
        if ch["cha"][0] not in VALID_BAND_CODES:
            skipped_non_waveform += 1
            continue

        loc = ch["loc"] if ch["loc"] else ""

        filename = f"{ch['net']}.{ch['sta']}.{loc}.{ch['cha']}.D.{year}.{jday}"

        expected.add(filename)

    logging.info(f"Expected files generated: {len(expected)}")
    logging.info(f"Channels skipped (inactive): {skipped_inactive}")
    logging.info(f"Channels skipped (non waveform): {skipped_non_waveform}")

    return expected


# --------------------------------------------------
# scan repository
# --------------------------------------------------

def scan_repository(sds_root, year, jday):

    logging.info("Scanning SDS repository")

    pattern = os.path.join(
        sds_root,
        str(year),
        "*",
        "*",
        "*.D",
        f"*.{year}.{jday}"
    )

    logging.debug(f"SDS scan pattern: {pattern}")

    files = glob.glob(pattern)

    repo = {os.path.basename(f) for f in files}

    logging.info(f"Repository files found: {len(repo)}")

    return repo


# --------------------------------------------------
# scan BAD repository (NEW)
# --------------------------------------------------

def scan_bad_repository(bad_root):

    logging.info("Scanning BAD repository")

    pattern = os.path.join(
        bad_root,
        "*",
        "*",
        "*",
        "*.D",
        "*"
    )

    files = glob.glob(pattern)

    bad = set()
    bad_with_code = {}

    print(len(files))

    for f in files:

        name = os.path.basename(f)
        print(name)
        if "-" in name:
            base, code = name.rsplit("-", 1)
        else:
            base = name
            code = "UNKNOWN"

        bad.add(base)
        bad_with_code[base] = code
        print(code)

    logging.info(f"BAD files found (normalized): {len(bad)}")

    return bad, bad_with_code

# --------------------------------------------------
# mail
# --------------------------------------------------

def send_mail(missing, bad_found):

    body = "SDS ingestion report\n\n"

    body += f"Missing files: {len(missing)}\n"
    for f in sorted(missing):
        body += f"{f}\n"

    body += f"\nRejected (BAD) files: {len(bad_found)}\n"
    for f in sorted(bad_found):
        body += f"{f}\n"

    msg = MIMEText(body)

    msg["Subject"] = "SDS ingestion check report"
    msg["From"] = MAIL_FROM
    msg["To"] = ", ".join(MAIL_TO)

    with smtplib.SMTP(SMTP_SERVER) as s:
        s.sendmail(MAIL_FROM, MAIL_TO, msg.as_string())


# --------------------------------------------------
# main
# --------------------------------------------------

def main():

    args = parse_args()

    setup_logging(args.log_level)

    target_date, year, jday = get_target_day(args.days_back)

    logging.info(f"Checking SDS ingestion for: {target_date}")
    logging.info(f"SDS root: {args.sds_root}")
    logging.info(f"BAD root: {args.bad_root}")

    channels = fetch_station_channels()

    expected = build_expected_files(channels, target_date, year, jday)

    repo = scan_repository(args.sds_root, year, jday)

    bad_repo, bad_with_code = scan_bad_repository(args.bad_root)

    # --------------------------------------------------
    # comparison logic (NEW)
    # --------------------------------------------------

    missing = expected - repo

    # files that are missing BUT present in BAD
    bad_found = missing.intersection(bad_repo)
    # --------------------------------------------------
    # classify BAD files by error code
    # --------------------------------------------------

    error_stats = {}

    for f in bad_found:
        code = bad_with_code.get(f, "UNKNOWN")
        label = ERROR_MAP.get(code, f"UNKNOWN_CODE_{code}")

        error_stats[label] = error_stats.get(label, 0) + 1

    # real missing (not even in BAD)
    real_missing = missing - bad_found

    logging.info(f"Expected files: {len(expected)}")
    logging.info(f"Repository files: {len(repo)}")
    logging.info(f"Rejected (BAD) files matched: {len(bad_found)}")
    logging.info(f"Missing files (true missing): {len(real_missing)}")

    # --------------------------------------------------
    # STATION-LEVEL AGGREGATION (NEW)
    # --------------------------------------------------

    station_data = {}

    def get_station_key(f):
        parts = f.split(".")
        return f"{parts[0]}.{parts[1]}"  # NET.STA

    def get_channel_key(f):
        parts = f.split(".")
        return parts[3]  # CHA

    # expected
    for f in expected:
        sta = get_station_key(f)
        cha = get_channel_key(f)

        station_data.setdefault(sta, {
            "expected": set(),
            "ok": set(),
            "bad": set(),
            "missing": set()
        })

        station_data[sta]["expected"].add(cha)

    # repo (OK)
    for f in repo:
        sta = get_station_key(f)
        cha = get_channel_key(f)

        if sta in station_data:
            station_data[sta]["ok"].add(cha)

    # bad
    for f in bad_found:
        sta = get_station_key(f)
        cha = get_channel_key(f)

        if sta in station_data:
            station_data[sta]["bad"].add(cha)

    # missing
    for f in real_missing:
        sta = get_station_key(f)
        cha = get_channel_key(f)

        if sta in station_data:
            station_data[sta]["missing"].add(cha)

    if bad_found:
        for f in list(sorted(bad_found))[:20]:
            logging.debug(f"BAD example: {f}")

    if real_missing:
        for f in list(sorted(real_missing))[:20]:
            logging.debug(f"Missing example: {f}")

    if MAIL_ENABLED:
        send_mail(real_missing, bad_found)

    if not real_missing:
        logging.info("No missing files (excluding BAD).")

    if error_stats:
        logging.info("BAD files classification:")
        for err, count in sorted(error_stats.items()):
            logging.info(f"  {err}: {count}")
    print (error_stats)

    # --------------------------------------------------
    # CLASSIFICATION
    # --------------------------------------------------

    logging.info("Station-level summary:")

    for sta, data in station_data.items():

        n_exp = len(data["expected"])
        n_ok = len(data["ok"])
        n_bad = len(data["bad"])
        n_missing = len(data["missing"])

        if n_ok == n_exp:
            continue  # tutto ok, skip

        if n_missing == n_exp:
            status = "ALL_MISSING"

        elif n_bad == n_exp:
            status = "ALL_BAD"

        elif n_ok == 0:
            status = "NO_DATA"

        else:
            status = "PARTIAL"

        logging.info(
            f"{sta} → {status} | "
            f"ok={n_ok}/{n_exp}, bad={n_bad}, missing={n_missing}"
        )


if __name__ == "__main__":
    main()

