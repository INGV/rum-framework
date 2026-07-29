# 📦 SDS Check Script — README

## 🧭 Overview

`sd-check` is a Python script designed to verify the **completeness of seismic data ingestion** in an SDS archive (SeisComP Data Structure).

The script compares:

* 📡 **expected active channels** (from FDSN Station Service)
* 📁 **actual files present** in the SDS repository

and identifies any **missing files** for a given day.

---

## ⚙️ How It Works (High-Level)

The workflow is:

1. Fetch channel metadata from the FDSN Station Service
2. Filter channels active on the target date
3. Generate the list of expected SDS files
4. Scan the SDS filesystem
5. Compare expected vs actual files
6. Log results and optionally send email alerts

---

## 📅 Target Date

By default, the script checks:

```
today - 2 days
```

This can be configured via CLI.

---

## 📂 Expected SDS Structure

The script assumes a standard SDS layout:

```
<SDS_ROOT>/<YEAR>/<NET>/<STA>/<CHA>.D/<NET>.<STA>.<LOC>.<CHA>.D.<YEAR>.<JDAY>
```

Example:

```
/mnt/trust-archive/trust/2025/IV/ABCD/BHZ.D/IV.ABCD..BHZ.D.2025.123
```

---

## 🚀 Usage

```
python3 sds_check.py [OPTIONS]
```

### Available Parameters

#### `--days-back`

* Type: `int`
* Default: `2`
* Description: Number of days before today to check

Example:

```
--days-back 5
```

→ checks data from 5 days ago

---

#### `--sds-root`

* Type: `string`
* Default: `/mnt/trust-archive/trust/`
* Description: Path to SDS repository root

Example:

```
--sds-root /data/sds/
```

---

#### `--log-level`

* Type: `string`
* Default: `INFO`
* Allowed values:

  * `DEBUG`
  * `INFO`
  * `WARNING`
  * `ERROR`

Example:

```
--log-level DEBUG
```

---

## 🧪 Full Example

```
python3 sds_check.py \
    --days-back 3 \
    --sds-root /mnt/trust-archive/trust/ \
    --log-level DEBUG
```

---

## 📡 Channel Data Source

Channel metadata is retrieved from:

```
https://webservices.ingv.it/fdsnws/station/1/query
```

Parameters:

* `network=*`
* `level=channel`
* `format=text`

---

## 🔍 Channel Selection Logic

A channel is considered **valid** if:

* it is active on the target date (`start <= target_date <= end`)
* it is a waveform channel:

```python
cha.startswith(("H", "B", "E", "S"))
```

Excluded channels:

* ❌ non-waveform channels (e.g. state-of-health)
* ❌ inactive channels

---

## 📄 Output

### Log File

The script generates:

```
check_sds_ingestion.log
```

It contains:

* configuration details
* number of channels
* expected files
* found files
* missing files

---

### Console Output

Example:

```
Checking SDS ingestion for: 2025-04-15
Expected files: 1250
Repository files: 1242
Missing files: 8
```

---

## ⚠️ Missing Files Handling

If missing files are detected:

* they are logged
* sample entries are shown (max 20 in DEBUG mode)

```python
missing = expected - repo
```

---

## 📧 Email Notifications

Configuration:

```python
MAIL_ENABLED = False
SMTP_SERVER = "localhost"
MAIL_FROM = "sds-check@ingv.it"
MAIL_TO = ["data-manager@ingv.it"]
```

### Enable Email

Set:

```python
MAIL_ENABLED = True
```

### Email Content

* list of missing files
* total count

---

## 📊 Logged Metrics

* total number of channels
* active channels
* skipped channels:

  * inactive
  * non-waveform
* expected files
* repository files
* missing files

---

## ⚡ Performance Considerations

Current approach:

* filesystem scan via `glob`
* in-memory comparison using `set`

Possible future improvements:

* parallel scanning
* station metadata caching
* filesystem indexing
* configuration file (YAML/JSON)

---

## 🧩 Dependencies

```
pip install requests python-dateutil
```

Standard libraries used:

* `datetime`
* `os`
* `glob`
* `argparse`
* `logging`
* `smtplib`

---

## 🧱 Code Structure

| Function                 | Description             |
| ------------------------ | ----------------------- |
| `parse_args`             | CLI parsing             |
| `setup_logging`          | logging configuration   |
| `get_target_day`         | target date calculation |
| `fetch_station_channels` | fetch metadata          |
| `channel_active`         | channel activity check  |
| `build_expected_files`   | generate expected files |
| `scan_repository`        | scan SDS repository     |
| `send_mail`              | send notifications      |
| `main`                   | orchestration           |

---

## 🧠 Design Notes

* **deterministic approach**: expected vs actual
* SDS naming used as logical key
* no database dependency
* easily schedulable (cron)

---

## 🔮 Future Improvements

* ✅ configuration file (YAML)
* ✅ retry + timeout for FDSN service
* ✅ parallel scanning
* ✅ JSON reporting (for pipelines / dashboards)
* ✅ integration with PID / Digital Objects
* ✅ alert thresholds (e.g. > X missing → failure)

---
