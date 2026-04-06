#!/usr/bin/env python3
"""
==============================================================
 119 Ministries - Vimeo Video Sync Tool
 Version: v20260406a
==============================================================
 Compares videos already on disk to what 119 Ministries has
 recently published on Vimeo, then downloads anything missing.

 Requirements:
   pip install requests python-dateutil
   /usr/local/bin/yt-dlp  (standalone binary)

 Usage:
   python3 119_ministries_downloader_v20260406a.py
==============================================================
"""

import os
import re
import sys
import time
import subprocess
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    print("ERROR: 'requests' is not installed. Run: pip install requests")
    sys.exit(1)

try:
    from dateutil.relativedelta import relativedelta
except ImportError:
    print("ERROR: 'python-dateutil' is not installed. Run: pip install python-dateutil")
    sys.exit(1)


# ── Configuration ──────────────────────────────────────────
VERSION          = "v20260406a"
VIMEO_USER       = "testeverything"
YTDLP_BIN        = "/usr/local/bin/yt-dlp"
VIDEO_EXTS       = {".mp4", ".mkv", ".webm", ".mov", ".avi", ".m4v"}
DOWNLOAD_RETRIES = 3          # attempts per video before giving up
RETRY_DELAY      = 10         # seconds to wait between retry attempts
DOWNLOAD_TIMEOUT = 3600       # seconds before a single download is force-killed (1 hour)
FAILED_LOG       = "failed_downloads.txt"
# ───────────────────────────────────────────────────────────


def check_ytdlp():
    """Verify yt-dlp binary exists and is executable before we start."""
    if not os.path.isfile(YTDLP_BIN):
        print(f"\n  ERROR: yt-dlp not found at '{YTDLP_BIN}'")
        print("  Install it with:  pip install yt-dlp")
        print("  Or download from: https://github.com/yt-dlp/yt-dlp/releases")
        sys.exit(1)
    if not os.access(YTDLP_BIN, os.X_OK):
        print(f"\n  ERROR: yt-dlp at '{YTDLP_BIN}' is not executable.")
        print(f"  Fix with:  chmod +x {YTDLP_BIN}")
        sys.exit(1)


def print_banner():
    print()
    print("=" * 62)
    print("   119 Ministries — Vimeo Video Sync Tool")
    print(f"   {VERSION}")
    print("=" * 62)
    print()
    print("  This script will:")
    print("  1. Ask how many months back you want to check,")
    print("     or 'all' to scan the entire channel history")
    print("  2. Fetch the list of videos 119 Ministries published on")
    print(f"     Vimeo (https://vimeo.com/{VIMEO_USER})")
    print("     within that time window")
    print("  3. Compare them against the video files already in the")
    print("     directory where this script is run")
    print("  4. Download any videos that are missing, in 1080p MP4")
    print()
    print("=" * 62)
    print()


def ask_months():
    """
    Ask how far back to scan. Returns an integer (months) or None (all-time).
    Accepts any positive whole number, or 'all' / '0' for the full channel history.
    """
    while True:
        raw = input("  How many months back should we check? (number, or 'all' for everything): ").strip().lower()
        if raw in ("all", "0", ""):
            return None
        try:
            months = int(raw)
            if months > 0:
                return months
            print("  Please enter a positive number, or 'all'.")
        except ValueError:
            print("  Please enter a whole number, or 'all'.")


def normalise(title):
    """Lowercase, strip punctuation and extra whitespace for comparison."""
    title = title.lower()
    title = re.sub(r"[^\w\s]", "", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title


def get_local_titles(directory):
    """
    Return a set of normalised video titles found on disk.
    Strips resolution tags like (1080p), (720p) and file extensions
    before normalising for fuzzy matching.
    """
    titles = set()
    for fname in os.listdir(directory):
        ext = os.path.splitext(fname)[1].lower()
        if ext in VIDEO_EXTS:
            name = re.sub(r'\s*\(\d{3,4}p\)', '', os.path.splitext(fname)[0])
            titles.add(normalise(name))
    return titles


def parse_relative_time(n, unit):
    """Convert a 'N units ago' pair into an approximate datetime."""
    now = datetime.now(timezone.utc)
    delta_map = {
        "second": relativedelta(seconds=n),
        "minute": relativedelta(minutes=n),
        "hour":   relativedelta(hours=n),
        "day":    relativedelta(days=n),
        "week":   relativedelta(weeks=n),
        "month":  relativedelta(months=n),
        "year":   relativedelta(years=n),
    }
    return now - delta_map[unit]


def fetch_vimeo_videos(months):
    """
    Scrape the Vimeo user's video pages to collect videos uploaded
    within the cutoff window. Returns a list of dicts:
      { 'title': str, 'url': str, 'uploaded': datetime, 'id': str }

    Pass months=None to fetch the entire channel history.
    """
    if months is None:
        cutoff = None
        print("\n  Fetching all videos from the channel history...\n")
    else:
        cutoff = datetime.now(timezone.utc) - relativedelta(months=months)
        print(f"\n  Fetching Vimeo videos published after "
              f"{cutoff.strftime('%B %d, %Y')}...\n")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/133.0.0.0 Safari/537.36"
        )
    }

    videos = []
    seen_ids = set()
    page = 1

    while True:
        url = f"https://vimeo.com/{VIMEO_USER}/videos/page:{page}/sort:date"
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  WARNING: Failed to fetch page {page}: {e}")
            break

        html = resp.text

        # ── Extract video IDs and titles ───────────────────
        # Matches: href="https://vimeo.com/VIDEOID" title="VIDEO TITLE"
        found_on_page = [
            (m.group(1), m.group(2))
            for m in re.finditer(
                r'href="https://vimeo\.com/(\d{7,12})[^"]*"\s+title="([^"]+)"',
                html
            )
        ]

        if not found_on_page:
            break  # no more videos on this page

        # ── Extract relative upload times ──────────────────
        # Matches: vimeo.com/VIDEOID ... N unit(s) ago
        time_ago_map = {}
        now = datetime.now(timezone.utc)
        for m in re.finditer(
            r'vimeo\.com/(\d{7,12})[^"]*"[\s\S]{1,500}?(\d+)\s+'
            r'(second|minute|hour|day|week|month|year)s?\s+ago',
            html
        ):
            vid_id = m.group(1)
            if vid_id not in time_ago_map:
                time_ago_map[vid_id] = parse_relative_time(int(m.group(2)), m.group(3))

        # ── Build video list, stop when past cutoff ────────
        stop = False
        for vid_id, title in found_on_page:
            if vid_id in seen_ids:
                continue
            uploaded = time_ago_map.get(vid_id, now)
            if cutoff is not None and uploaded < cutoff:
                stop = True
                break
            seen_ids.add(vid_id)
            videos.append({
                "title":    title.strip(),
                "url":      f"https://vimeo.com/{vid_id}",
                "uploaded": uploaded,
                "id":       vid_id,
            })

        print(f"  Scanned page {page} — {len(found_on_page)} videos found"
              f" ({len(videos)} total within window so far)")

        if stop:
            break

        page += 1

    return videos


def find_missing(vimeo_videos, local_titles):
    """Return videos from Vimeo that aren't already on disk."""
    return [v for v in vimeo_videos if normalise(v["title"]) not in local_titles]


def download_video(url, title, index, total, output_dir):
    """
    Download a single video using yt-dlp, with retry logic.
    Returns True on success, False if all attempts fail.
    """
    cmd = [
        YTDLP_BIN,
        "--format", "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
        "--merge-output-format", "mp4",
        "--output", os.path.join(output_dir, "%(title)s (%(height)sp).%(ext)s"),
        "--no-playlist",
        "--sleep-interval", "3",
        "--max-sleep-interval", "8",
        "--no-overwrites",
        "--continue",
        "--progress",
        "--impersonate", "Chrome-133",
        "--cookies-from-browser", "firefox",
        url,
    ]

    for attempt in range(1, DOWNLOAD_RETRIES + 1):
        attempt_label = f"attempt {attempt}/{DOWNLOAD_RETRIES}" if DOWNLOAD_RETRIES > 1 else ""
        print(f"\n  [{index}/{total}] {title}")
        if attempt > 1:
            print(f"           Retrying... ({attempt_label})")
        print(f"           {url}")

        try:
            result = subprocess.run(
                cmd,
                timeout=DOWNLOAD_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            print(f"  WARNING: Download timed out after {DOWNLOAD_TIMEOUT}s — "
                  f"{attempt_label}")
            if attempt < DOWNLOAD_RETRIES:
                print(f"           Waiting {RETRY_DELAY}s before retry...")
                time.sleep(RETRY_DELAY)
            continue
        except FileNotFoundError:
            print(f"  ERROR: yt-dlp binary not found at '{YTDLP_BIN}'")
            sys.exit(1)

        if result.returncode == 0:
            return True

        print(f"  WARNING: yt-dlp exited with code {result.returncode} — {attempt_label}")
        if attempt < DOWNLOAD_RETRIES:
            print(f"           Waiting {RETRY_DELAY}s before retry...")
            time.sleep(RETRY_DELAY)

    print(f"  FAILED after {DOWNLOAD_RETRIES} attempt(s): {title}")
    return False


def write_failed_log(failed, output_dir):
    """Write a plain-text log of failed downloads for easy retry later."""
    log_path = os.path.join(output_dir, FAILED_LOG)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"\n# Failed downloads — {timestamp}\n")
        for v in failed:
            f.write(f"{v['url']}   # {v['title']}\n")
    print(f"\n  Failed URLs written to: {log_path}")


def main():
    check_ytdlp()
    print_banner()

    months = ask_months()
    if months is None:
        print("\n  Got it — scanning the entire channel history.")
    else:
        print(f"\n  Got it — checking the last {months} month(s).")

    work_dir = os.getcwd()
    print(f"\n  Working directory: {work_dir}")

    print("  Scanning local video files...")
    local_titles = get_local_titles(work_dir)
    print(f"  Found {len(local_titles)} video file(s) on disk.")

    vimeo_videos = fetch_vimeo_videos(months)
    if not vimeo_videos:
        print("\n  No videos found on Vimeo within that window.")
        print("  This may be a scraping issue — try a different range or 'all'.")
        sys.exit(0)

    window_label = "all time" if months is None else f"the last {months} month(s)"

    print(f"\n  Found {len(vimeo_videos)} video(s) on Vimeo within {window_label}.")

    missing = find_missing(vimeo_videos, local_titles)
    if not missing:
        print("\n  ✓ You're up to date! No missing videos found.")
        sys.exit(0)

    print(f"\n  {len(missing)} video(s) need to be downloaded:")
    print()
    for i, v in enumerate(missing, 1):
        print(f"    {i:>3}. {v['title']}")

    print()
    confirm = input(f"  Download all {len(missing)} video(s) now? [y/N]: ").strip().lower()
    if confirm != "y":
        print("\n  Cancelled. No files were downloaded.")
        sys.exit(0)

    print()
    print("=" * 62)
    failed = []
    for i, v in enumerate(missing, 1):
        success = download_video(v["url"], v["title"], i, len(missing), work_dir)
        if not success:
            failed.append(v)

    print()
    print("=" * 62)
    succeeded = len(missing) - len(failed)
    print(f"  Download complete: {succeeded}/{len(missing)} succeeded.")

    if failed:
        print(f"\n  The following {len(failed)} video(s) failed:")
        for v in failed:
            print(f"    - {v['title']}")
            print(f"      {v['url']}")
        write_failed_log(failed, work_dir)

    print("=" * 62)
    print()


if __name__ == "__main__":
    main()
