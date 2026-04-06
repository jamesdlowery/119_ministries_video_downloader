# 119 Ministries — Vimeo Video Sync Tool

A Python script that compares 119 Ministries' public Vimeo channel against your local video library and automatically downloads anything you're missing — in 1080p MP4.

No Vimeo account. No API key. No login required.

---

## Features

- Scrapes 119 Ministries' public Vimeo channel (`vimeo.com/testeverything`) directly
- Scans your local directory and fuzzy-matches titles to avoid re-downloading files you already have
- Lets you choose a lookback window — any number of months, or the entire channel history
- Downloads in 1080p MP4 using `yt-dlp`
- Retries failed downloads automatically (configurable attempts and delay)
- Kills hung downloads after a configurable timeout
- Logs any permanently failed downloads to `failed_downloads.txt` for easy retry

---

## Requirements

- Python 3.8+
- [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) installed at `/usr/local/bin/yt-dlp`
- Firefox (used by `yt-dlp` for cookie-based access to Vimeo)
- Python packages:

```bash
pip install requests python-dateutil
```

---

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/119-ministries-downloader.git
cd 119-ministries-downloader
pip install requests python-dateutil
```

Install `yt-dlp` if you haven't already:

```bash
pip install yt-dlp
# or download the standalone binary:
# https://github.com/yt-dlp/yt-dlp/releases
```

---

## Usage

Navigate to the directory where your video files are stored, then run the script:

```bash
cd /path/to/your/video/library
python3 119_ministries_downloader_v20260406a.py
```

The script will ask how far back to check:

```
How many months back should we check? (number, or 'all' for everything):
```

Enter a number (e.g. `6` for the last 6 months) or `all` to scan the entire channel history.

---

## Configuration

All tuneable settings are at the top of the script:

| Constant | Default | Description |
|---|---|---|
| `VIMEO_USER` | `testeverything` | Vimeo username to scrape |
| `YTDLP_BIN` | `/usr/local/bin/yt-dlp` | Path to the yt-dlp binary |
| `VIDEO_EXTS` | `.mp4 .mkv .webm` etc. | File extensions counted as local videos |
| `DOWNLOAD_RETRIES` | `3` | Attempts per video before giving up |
| `RETRY_DELAY` | `10` | Seconds between retry attempts |
| `DOWNLOAD_TIMEOUT` | `3600` | Seconds before a hung download is killed |
| `FAILED_LOG` | `failed_downloads.txt` | Filename for the failed-download log |

---

## How It Works

1. **Pre-flight check** — confirms `yt-dlp` is present and executable before doing anything else
2. **Local scan** — reads all video files in the current directory, strips resolution tags (e.g. `(1080p)`) and normalises titles for comparison
3. **Vimeo scrape** — pages through `vimeo.com/testeverything/videos` sorted by date, extracting video IDs, titles, and relative upload timestamps
4. **Comparison** — fuzzy-matches Vimeo titles against local titles to find gaps
5. **Download** — runs `yt-dlp` for each missing video with retry logic and a per-download timeout
6. **Failure log** — any videos that fail all retry attempts are appended to `failed_downloads.txt`

---

## Output

Videos are saved to the current working directory using the naming convention:

```
Video Title (1080p).mp4
```

---

## Versioning

Releases follow the convention `vYYYYMMDD` + lowercase letter suffix (e.g. `v20260406a`). The version is reflected in the docstring header, the `VERSION` constant, and the filename.

---

## License

This project is provided for personal archival use. 119 Ministries content is copyright of 119 Ministries. Please respect their terms of use.
