# SDS Distributor

## Overview
`SDS Distributor` is a Python script designed to scan an SDS archive, select seismic data files according to configurable temporal and metadata filters, and dispatch them to a pool of worker directories for downstream processing.

The script is intended for daily operational ingestion, but also supports manual reprocessing, partial reloads, and recovery from failures.



---

## High-Level Logic

1. Load configuration from YAML
2. Apply CLI overrides
3. Resolve date selection (yesterday, specific JDAY, or all)
4. Scan SDS archive
5. Queue files
6. Dispatch files in parallel
7. Retry safely on busy workers
8. Log everything and optionally send email alerts

---

## Date Handling

Default: yesterday (UTC)

Options:
- `--year YYYY`
- `--jday auto` (default)
- `--jday <N>`
- `--jday all`

Leap years are handled transparently.

---

## Filters

Optional filters for targeted processing:
- `--network` (optional)
- `--station` (requires network)
- `--channel` (requires network and station)

Example:
```bash
python3 sds_distributor.py --year 2023 --jday all --network IV --station AQU
```

---

## Worker Model

Workers are directories:
```
/data/workers/1
/data/workers/2
...
/data/workers/25
```

Important:
> Worker directories act as queues, not locks.

Multiple files may temporarily appear in the same directory and are processed sequentially by worker.

---

## Dispatch Logic

- Round-robin worker selection
- Retry when all workers are busy
- Sleep between retries
- Move unprocessed files to `load-error` directory

No file is silently dropped.

---

## Parallelization

- ThreadPoolExecutor
- Configurable number of threads

---

## Error Handling

Files that fail dispatch after all retries are moved to:
```
/data/test-archive/load-error/
```


---

## Lock File

Optional lock file prevents concurrent executions (e.g. overlapping cron runs).

---

## Logging

- File-based logging
- Configurable level

---

## Email Notifications

Optional email alerts

---

## Dry-Run Mode

`--dry-run` prints selected files without copying.

---

## Configuration

- All defaults live in a YAML file.
- CLI arguments always override config values.

---


##  Quick Reference

### Command Line Usage

```bash
python3 distributor.py [OPTIONS]
```

 ---

| Default Command          | 
|--------------------------| 
| `python3 distributor.py` |  |

_Process yesterday SDS-Archive_

---

#### Optional Filters

| Option       | Description               | Notes                                              | Example                    |
|--------------|---------------------------|----------------------------------------------------|----------------------------|
| `--network`  | Network code              |                                                    | `--network IV`             |
| `--station`  | Station code              | Requires `--network`                               | `--station AQU`            |
| `--channel`  | Channel code              | Requires `--network` + `--station`                 | `--channel HHZ`            |
| `--year`     | Year to process           | Defaults to yesterday's year                       | `--year 2024`              |
| `--jday`     | Julian day(s) to process  | `auto` = yesterday, `all` = entire year, or number | `--jday 25` / `--jday all` |
| `--sds-root` | Override SDS archive root | Absolute path                                      | `--sds-root /mnt/archive`  |


#### Other Useful Options

| Option      | Description                          | Example                            |
| ----------- | ------------------------------------ | ---------------------------------- |
| `--dry-run` | Print selected files without copying | `--dry-run`                        |
| `--config`  | Path to YAML configuration file      | `--config /home/sysop/config.yaml` |


#### Examples

Process yesterday for a network
```bash
python3 distributor.py  --network IV 
```

Process a specific day for a network and station
```bash
python3 distributor.py  --network IV --station AQU --jday 25
```

Process all days of previous year for a station
```bash
python3 distributor.py  --network IV --station AQU --year 2023 --jday all
```

Dry-run mode (no files copied)
```bash
python3 distributor.py  --network IV --station AQU --dry-run
```

Override SDS root and config file
```bash
python3 distributor.py  --network IV --sds-root /mnt/test-archive --config /home/sysop/config.yaml
```


