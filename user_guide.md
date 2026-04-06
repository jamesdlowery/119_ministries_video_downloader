# User Guide — 119 Ministries Vimeo Video Sync Tool

This guide walks through everything you need to get the script running, understand what it's doing, and deal with common problems.

---

## Table of Contents

1. [Before You Start](#before-you-start)
2. [First-Time Setup](#first-time-setup)
3. [Running the Script](#running-the-script)
4. [Walkthrough of a Typical Session](#walkthrough-of-a-typical-session)
5. [Configuration Reference](#configuration-reference)
6. [Understanding the Title Matching](#understanding-the-title-matching)
7. [Handling Failed Downloads](#handling-failed-downloads)
8. [Troubleshooting](#troubleshooting)
9. [Tips and Recommended Workflows](#tips-and-recommended-workflows)

---

## Before You Start

You need three things installed before the script will run:

**1. Python 3.8 or later**

Check your version:
```bash
python3 --version
```

If you need to install Python, download it from [python.org](https://www.python.org/downloads/).

**2. yt-dlp**

`yt-dlp` is the download engine the script hands off to. The script expects it at `/usr/local/bin/yt-dlp`. Install it:

```bash
pip install yt-dlp
```

Or download the standalone binary directly from the [yt-dlp releases page](https://github.com/yt-dlp/yt-dlp/releases) and place it at `/usr/local/bin/yt-dlp`, then make it executable:

```bash
chmod +x /usr/local/bin/yt-dlp
```

If your `yt-dlp` binary is somewhere else, update the `YTDLP_BIN` constant at the top of the script to match.

**3. Python packages**

```bash
pip install requests python-dateutil
```

**4. Firefox**

`yt-dlp` reads cookies from your Firefox browser to authenticate with Vimeo. Firefox must be installed and you should have visited Vimeo at least once so the cookie store exists. You don't need to be logged in.

---

## First-Time Setup

Clone or download the repository, then install the Python dependencies:

```bash
git clone https://github.com/YOUR_USERNAME/119-ministries-downloader.git
cd 119-ministries-downloader
pip install requests python-dateutil
```

No other configuration is needed for a standard setup.

---

## Running the Script

Always run the script from inside the directory where your video files live (or where you want them saved). The script uses the current working directory as both the source for comparison and the destination for downloads.

```bash
cd /Volumes/MyDrive/119_Ministries_Videos
python3 119_ministries_downloader_v20260406a.py
```

---

## Walkthrough of a Typical Session

**Step 1 — Banner**

The script opens with a version banner and a brief summary of what it's about to do.

**Step 2 — Choose your lookback window**

```
How many months back should we check? (number, or 'all' for everything):
```

- Enter a number like `3`, `6`, or `24` to check only that many months of uploads
- Enter `all` (or just press Enter) to scan the entire channel from the beginning
- For routine weekly/monthly sync runs, `3` or `6` months is usually plenty
- For a first-time full archive run, use `all`

**Step 3 — Local scan**

The script scans your current directory for existing video files. It recognises `.mp4`, `.mkv`, `.webm`, `.mov`, `.avi`, and `.m4v` files.

```
Scanning local video files...
Found 312 video file(s) on disk.
```

**Step 4 — Vimeo scrape**

The script pages through 119 Ministries' Vimeo channel, collecting video titles and approximate upload dates. You'll see progress per page:

```
Scanned page 1 — 12 videos found (12 total within window so far)
Scanned page 2 — 12 videos found (24 total within window so far)
...
```

**Step 5 — Comparison and missing list**

After scraping, the script compares what's on Vimeo against what you have on disk. Any gaps are listed:

```
8 video(s) need to be downloaded:

    1. Strange Fire: When Sincerity is Not Enough
    2. The Brit Hadasha Series - The MEM Mystery
    ...
```

**Step 6 — Confirmation**

```
Download all 8 video(s) now? [y/N]:
```

Type `y` and press Enter to proceed. Anything else cancels without downloading.

**Step 7 — Downloads**

Each video is downloaded in turn. If a download fails, it is automatically retried up to 3 times (configurable) with a 10-second pause between attempts.

```
[1/8] Strange Fire: When Sincerity is Not Enough
      https://vimeo.com/1160353542
```

**Step 8 — Summary**

```
Download complete: 7/8 succeeded.

The following 1 video(s) failed:
  - The Brit Hadasha Series - The MEM Mystery
    https://vimeo.com/1158684483

Failed URLs written to: failed_downloads.txt
```

---

## Configuration Reference

All configuration is at the top of the script file, clearly labelled. You can edit these without touching any of the logic.

| Constant | Default | What it does |
|---|---|---|
| `VIMEO_USER` | `testeverything` | The Vimeo username to scrape. Change this if you want to use the script for a different channel. |
| `YTDLP_BIN` | `/usr/local/bin/yt-dlp` | Full path to the yt-dlp binary. Update this if yours is installed elsewhere (e.g. `/opt/homebrew/bin/yt-dlp`). |
| `VIDEO_EXTS` | `.mp4 .mkv .webm .mov .avi .m4v` | File extensions the script treats as video files when scanning your local library. |
| `DOWNLOAD_RETRIES` | `3` | How many times to attempt each download before logging it as failed. Set to `1` to disable retries. |
| `RETRY_DELAY` | `10` | Seconds to wait between retry attempts. Increase this if Vimeo seems to be rate-limiting you. |
| `DOWNLOAD_TIMEOUT` | `3600` | Maximum seconds a single download is allowed to run before it's force-killed. 3600 = 1 hour. Increase for very large files on slow connections. |
| `FAILED_LOG` | `failed_downloads.txt` | Name of the file where failed download URLs are logged. Written to the current working directory. |

---

## Understanding the Title Matching

The script uses fuzzy title matching to decide whether a Vimeo video is already on disk. Specifically, it:

1. Strips resolution tags from your local filenames — `(1080p)`, `(720p)`, etc.
2. Strips the file extension
3. Lowercases everything
4. Removes all punctuation
5. Collapses extra whitespace

The same normalisation is applied to titles fetched from Vimeo. If the normalised strings match, the video is considered already present.

**What this means in practice:**

- `Strange Fire When Sincerity is Not Enough (1080p).mp4` → matches `Strange Fire: When Sincerity is Not Enough` ✓
- `strange fire when sincerity is not enough.mp4` → also matches ✓
- `StrangeFire_WhenSincerityIsNotEnough.mp4` → will NOT match (word boundaries lost)

If you find the script re-downloading things you already have, check whether your local filenames are substantially different from the Vimeo titles.

---

## Handling Failed Downloads

When a video fails all retry attempts, its URL and title are appended to `failed_downloads.txt` in your working directory. The file is cumulative — each run appends a new timestamped block, so you never lose previous failure records.

Example contents:

```
# Failed downloads — 2026-04-06 14:32:01
https://vimeo.com/1158684483   # The Brit Hadasha Series - The MEM Mystery
```

To retry failed downloads, simply run the script again — as long as the videos are still within your chosen lookback window, they'll appear in the missing list and be attempted again.

Alternatively, you can pass the URLs directly to `yt-dlp` manually:

```bash
/usr/local/bin/yt-dlp --format "bestvideo[height<=1080]+bestaudio/best" \
  --merge-output-format mp4 \
  --cookies-from-browser firefox \
  https://vimeo.com/1158684483
```

---

## Troubleshooting

**`ERROR: yt-dlp not found at '/usr/local/bin/yt-dlp'`**

Your `yt-dlp` binary is either not installed or is in a different location. Find it with:
```bash
which yt-dlp
```
Then update `YTDLP_BIN` in the script to match that path.

---

**`ERROR: yt-dlp at '...' is not executable`**

The binary exists but doesn't have execute permissions:
```bash
chmod +x /usr/local/bin/yt-dlp
```

---

**`WARNING: Failed to fetch page 1`**

The script couldn't reach Vimeo. Check your internet connection. If Vimeo is reachable in a browser but the script fails, Vimeo may have changed their page structure in a way that blocks the request headers. Try updating the `User-Agent` string in `fetch_vimeo_videos()` to match your current browser version.

---

**No videos found even though there should be some**

Vimeo's HTML structure occasionally changes, which can break the scraping regex. This is the fundamental tradeoff of scraping versus using an API. Signs of this: the script reports `Scanned page 1 — 0 videos found`. If this happens, open an issue on the repository with the date so the regex pattern can be updated.

---

**Videos keep re-downloading even though I have them**

The title on Vimeo doesn't match your local filename closely enough for the fuzzy matcher to catch it. Check the exact title on Vimeo and compare it to your filename after mentally stripping the resolution tag and extension. Special characters, subtitle separators (`:` vs `—`), or extra words in the filename are common culprits.

---

**Download is very slow or stalls**

Vimeo throttles downloads. The `--sleep-interval` and `--max-sleep-interval` flags in the `yt-dlp` command add a randomised delay between requests to reduce this. If stalling is frequent, increase `DOWNLOAD_TIMEOUT` so the script doesn't kill legitimate slow downloads prematurely.

---

## Tips and Recommended Workflows

**Routine sync (weekly or monthly)**
Run with `6` months as your window. This is fast and catches anything recent without re-scanning the entire channel history.

**First-time full archive run**
Run with `all`. This will page through every video 119 Ministries has ever published on Vimeo and download anything you don't have. Expect this to take a long time if your library is large.

**Keeping yt-dlp current**
Vimeo periodically updates its platform in ways that require `yt-dlp` patches. Update it regularly:
```bash
pip install --upgrade yt-dlp
```

**Running unattended**
The script prompts for confirmation before downloading. If you want to automate it (e.g. via cron), you could pipe `y` to stdin:
```bash
echo "y" | python3 119_ministries_downloader_v20260406a.py
```
Note that the months prompt would also need to be handled — consider a small wrapper script that feeds both inputs.
