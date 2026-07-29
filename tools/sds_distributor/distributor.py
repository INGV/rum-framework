#!/usr/bin/env python3

import os
import sys
import time
import yaml
import shutil
import queue
import logging
import argparse
import threading
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


# --------------------------------------------------
# UTIL
# --------------------------------------------------

def yesterday():
    return datetime.utcnow() - timedelta(days=1)


def send_mail(cfg, subject, body):
    if not cfg['email']['enabled']:
        return
    os.system(f'echo "{body}" | mail -s "{subject}" {cfg["email"]["to"]}')


# --------------------------------------------------
# CONFIG
# --------------------------------------------------

def load_config(path):
    with open(path) as f:
        return yaml.safe_load(f)


# --------------------------------------------------
# LOCKFILE
# --------------------------------------------------

def acquire_lock(lockfile):
    if os.path.exists(lockfile):
        raise RuntimeError(f"Lockfile exists: {lockfile}")
    with open(lockfile, "w") as f:
        f.write(f"{os.getpid()} {datetime.utcnow().isoformat()}")


def release_lock(lockfile):
    if os.path.exists(lockfile):
        os.remove(lockfile)


# --------------------------------------------------
# SDS SCAN
# --------------------------------------------------

def scan_sds_iter(cfg, year, jdays, net, sta, cha):

    root = os.path.join(cfg['sds']['root'], str(year))
    jday_suffix = None if jdays == 'all' else str(jdays).zfill(3)

    logging.info(f"SDS root scan start: {root}")

    try :
        with os.scandir(root) as nets:
            for net_entry in nets:

                if not net_entry.is_dir():
                    continue

                logging.debug(f"Scanning network dir: {net_entry.name}")

                if net and net_entry.name != net:
                    continue

                with os.scandir(net_entry.path) as stas:
                    for sta_entry in stas:

                        if not sta_entry.is_dir():
                            continue

                        logging.debug(f"  Scanning station dir: {sta_entry.name}")

                        if sta and sta_entry.name != sta:
                            continue

                        with os.scandir(sta_entry.path) as chas:
                            for cha_entry in chas:

                                if not cha_entry.is_dir():
                                    continue

                                logging.debug(f"    Scanning channel dir: {cha_entry.name}")

                                if cha and cha_entry.name != cha:
                                    continue

                                with os.scandir(cha_entry.path) as files:
                                    for f in files:

                                        if not f.is_file():
                                            continue

                                        if jday_suffix is None or f.name.endswith(jday_suffix):
                                            logging.debug(f"      Yielding file: {f.path}")
                                            yield f.path

    except FileNotFoundError:
        logging.warning(f"Skipping missing SDS year: {root}")
        return

# --------------------------------------------------
# WORKER
# --------------------------------------------------

def worker_loop(worker_id, file_queue, dir_queue, cfg, stats, stats_lock):

    logging.info(f"Worker-{worker_id} started")

    error_dir = cfg['error_handling']['error_dir']
    os.makedirs(error_dir, exist_ok=True)

    while True:

        src = file_queue.get()

        if src is None:
            file_queue.task_done()
            break

        try:

            while True:
                dest_dir = dir_queue.get()

                try:
                    current_files = len(os.listdir(dest_dir))
                except Exception as e:
                    logging.error(f"Worker-{worker_id} cannot read dir {dest_dir}: {e}")
                    dir_queue.put(dest_dir)
                    time.sleep(1)
                    continue

                if current_files >= cfg['workers'].get('max_files_per_dir', 5):
                    logging.debug(
                        f"Worker-{worker_id} skipping {dest_dir} "
                        f"(files={current_files})"
                    )
                    dir_queue.put(dest_dir)
                    time.sleep(0.5)
                    continue

                break

            dest = os.path.join(dest_dir, os.path.basename(src))

            t0 = time.time()

            shutil.copy2(src, dest)
            #  file from error_dir → remove it
            error_dir = cfg['error_handling']['error_dir']

            if src.startswith(error_dir):
                try:
                    os.remove(src)
                    logging.debug(f"Worker-{worker_id} removed recovered file {src}")
                except Exception as e:
                    logging.warning(f"Worker-{worker_id} cannot remove {src}: {e}")

            dt = time.time() - t0

            logging.info(
                f"Worker-{worker_id} copied {src} → {dest} "
                f"(time={dt:.3f}s)"
            )

            with stats_lock:
                stats['files_dispatched'] += 1

        except Exception as e:

            logging.error(f"Worker-{worker_id} copy failed {src}: {e}")

            try:
                shutil.copy2(src, os.path.join(error_dir, os.path.basename(src)))
            except Exception as ee:
                logging.error(f"Worker-{worker_id} error_dir failure {src}: {ee}")

            with stats_lock:
                stats['files_failed'] += 1

        finally:

            if 'dest_dir' in locals():
                dir_queue.put(dest_dir)

            file_queue.task_done()

    logging.info(f"Worker-{worker_id} stopped")

# --------------------------------------------------
# ERROR DIR ENQUEUE (PRIORITY)
# --------------------------------------------------

def enqueue_error_dir(cfg, file_queue, stats, stats_lock):
    error_dir = cfg['error_handling']['error_dir']

    if not os.path.exists(error_dir):
        logging.info(f"No error_dir found: {error_dir}")
        return

    files = []

    try:
        for f in os.scandir(error_dir):
            if f.is_file():
                files.append(f.path)
    except Exception as e:
        logging.error(f"Cannot scan error_dir {error_dir}: {e}")
        return

    if not files:
        logging.info("error_dir empty, nothing to recover")
        return

    logging.info(f"Recovering {len(files)} files from error_dir")

    for f in files:
        file_queue.put(f)

        with stats_lock:
            stats['files_discovered'] += 1

    logging.info("error_dir enqueue completed")


# --------------------------------------------------
# MONITOR
# --------------------------------------------------

def monitor_loop(q, stats, stop_event):

    while not stop_event.is_set():

        logging.info(
            "MONITOR "
            f"queue={q.qsize()} "
            f"discovered={stats['files_discovered']} "
            f"dispatched={stats['files_dispatched']} "
            f"failed={stats['files_failed']}"
        )

        time.sleep(30)

    logging.info("Monitor stopped")

# --------------------------------------------------
# POST-RUN WORKER CHECK
# --------------------------------------------------

def post_run_worker_check(cfg):

    base_dir = cfg['workers']['base_dir']
    error_dir = cfg['error_handling']['error_dir']
    workers = cfg['workers']['count']

    os.makedirs(error_dir, exist_ok=True)

    logging.info("Starting post-run worker check")

    for i in range(1, workers + 1):

        worker_dir = os.path.join(base_dir, str(i))

        if not os.path.exists(worker_dir):
            logging.warning(f"Worker dir not found: {worker_dir}")
            continue

        try:
            files = [f for f in os.scandir(worker_dir) if f.is_file()]
        except Exception as e:
            logging.error(f"Cannot scan {worker_dir}: {e}")
            continue

        if not files:
            logging.debug(f"Worker-{i} clean")
            continue

        logging.warning(
            f"Worker-{i} has {len(files)} leftover files → moving to error_dir"
        )

        # --- move files to error_dir ---
        for f in files:
            src = f.path
            dst = os.path.join(error_dir, os.path.basename(src))

            try:
                shutil.move(src, dst)
                logging.info(f"Moved {src} → {dst}")
            except Exception as e:
                logging.error(f"Failed to move {src}: {e}")

        # --- restart container ---
        container_name = f"{cfg['workers']['container_prefix']}-{i}"

        try:
            logging.warning(f"Restarting container {container_name}")
            os.system(f"docker restart {container_name}")
        except Exception as e:
            logging.error(f"Failed to restart {container_name}: {e}")

    logging.info("Post-run worker check completed")

# ----------------------------
# MAIN
# ----------------------------
def main():

    start_time = datetime.utcnow()

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--year")
    parser.add_argument("--jday", default="auto")
    parser.add_argument("--sds-root")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = args.config if os.path.isabs(args.config) else os.path.join(script_dir, args.config)

    cfg = load_config(config_path)
    if args.sds_root:
        logging.info(f"Overriding SDS root: {args.sds_root}")
        cfg['sds']['root'] = args.sds_root

    # --- Logging: file + console ---
    run_id = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    logfile = cfg['logging']['log_file'].replace(".log", f"_{run_id}.log")

    logging.basicConfig(
        level=getattr(logging, cfg['logging']['level']),
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(logfile, mode="w"),
            logging.StreamHandler()
        ]
    )

    logging.info("=== SDS DISTRIBUTOR START ===")
    logging.info(f"Config loaded from: {config_path}")
    logging.info(f"Log file: {logfile}")

    lockfile = cfg['runtime']['lock_file']

    try:
        acquire_lock(lockfile)
    except Exception as e:
        logging.error(str(e))
        sys.exit(1)

    try:

        if args.year is None:
            years = [yesterday().year]

        elif args.year.lower() == "all":
            years = sorted(
                int(d.name)
                for d in os.scandir(cfg['sds']['root'])
                if d.is_dir() and d.name.isdigit()
            )

        else:
            years = [int(args.year)]
        jday = yesterday().strftime("%j") if args.jday == "auto" else args.jday

        logging.info(f"Scanning for year={years}, jday={jday}")

        stats = {
            "files_discovered": 0,
            "files_dispatched": 0,
            "files_failed": 0
        }

        stats_lock = threading.Lock()

        file_queue = queue.Queue(maxsize=5000)
        dir_queue = queue.Queue()

        base = cfg['workers']['base_dir']
        workers = cfg['workers']['count']

        for i in range(1, workers + 1):
            dir_queue.put(os.path.join(base, str(i)))

        monitor_stop = threading.Event()

        monitor_thread = threading.Thread(
            target=monitor_loop,
            args=(file_queue, stats, monitor_stop),
            daemon=True
        )
        monitor_thread.start()
        logging.info("Monitor thread started")

        with ThreadPoolExecutor(max_workers=cfg['parallel']['threads']) as ex:

            for i in range(cfg['parallel']['threads']):
                ex.submit(worker_loop, i + 1, file_queue, dir_queue, cfg, stats, stats_lock)

            # --- PHASE 1: RECOVER ERROR FILES ---
            enqueue_error_dir(cfg, file_queue, stats, stats_lock)

            # --- PHASE 2: NORMAL SDS SCAN ---
            for year in years:

                logging.info(f"Scanning {years} years, jday={jday}")

                for f in scan_sds_iter(
                        cfg,
                        year,
                        jday,
                        cfg['filters']['network'],
                        cfg['filters']['station'],
                        cfg['filters']['channel']
                ):
                    file_queue.put(f)
                    sleep = cfg.get('producer', {}).get('sleep_sec', 0)
                    if sleep > 0:
                        time.sleep(sleep)

                    with stats_lock:
                        stats['files_discovered'] += 1

                    # log solo qualche file di esempio per non appesantire
                    if stats['files_discovered'] <= 20:
                        logging.debug(f"Discovered file: {f}")

            file_queue.join()

            for _ in range(cfg['parallel']['threads']):
                file_queue.put(None)

        monitor_stop.set()
        monitor_thread.join()

        # --- POST-RUN CHECK ---
        post_run_worker_check(cfg)

        elapsed = datetime.utcnow() - start_time

        summary = (
            f"Files discovered: {stats['files_discovered']}\n"
            f"Files dispatched: {stats['files_dispatched']}\n"
            f"Files failed: {stats['files_failed']}\n"
            f"Elapsed time: {elapsed}"
        )

        logging.info("=== RUN SUMMARY ===\n" + summary)

        send_mail(cfg, "SDS Distributor summary", summary)

    finally:

        release_lock(lockfile)
        logging.info("=== SDS DISTRIBUTOR END ===")

if __name__ == "__main__":
    main()
