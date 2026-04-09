#!/usr/bin/env python3
"""
==============================================================
 119 Ministries - Vimeo Video Sync Tool
==============================================================
 Compares videos already on disk to what 119 Ministries has
 recently published on Vimeo, then downloads anything missing.

 Requirements:
   pip install yt-dlp requests curl-cffi
   /usr/local/bin/yt-dlp  (standalone binary with impersonation)

 Usage:
   python3 119_ministries_downloader.py
==============================================================
"""

import os
import re
import sys
import subprocess
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

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
VIMEO_USER      = "testeverything"
VIMEO_BASE_URL  = f"https://vimeo.com/{VIMEO_USER}"
YTDLP_BIN       = "/usr/local/bin/yt-dlp"
MAX_MONTHS      = 18
VIDEO_EXTS      = {".mp4", ".mkv", ".webm", ".mov", ".avi", ".m4v"}
# ───────────────────────────────────────────────────────────


def print_banner():
    print()
    print("=" * 62)
    print("   119 Ministries — Vimeo Video Sync Tool")
    print("=" * 62)
    print()
    print("  This script will:")
    print("  1. Ask how many months back you want to check (up to 18)")
    print("  2. Fetch the list of videos 119 Ministries published on")
    print(f"     Vimeo ({VIMEO_BASE_URL})")
    print("     within that time window")
    print("  3. Compare them against the video files already in the")
    print("     directory where this script is run")
    print("  4. Download any videos that are missing, in 1080p MP4")
    print()
    print("=" * 62)
    print()


def ask_months():
    while True:
        try:
            raw = input(f"  How many months back should we check? (1-{MAX_MONTHS}): ").strip()
            months = int(raw)
            if 1 <= months <= MAX_MONTHS:
                return months
            print(f"  Please enter a number between 1 and {MAX_MONTHS}.")
        except ValueError:
            print("  Please enter a valid whole number.")


def get_local_titles(directory):
    """
    Return a set of normalised video titles found on disk.
    Strips resolution tags like (1080p), (720p), file extensions,
    and lowercases + strips punctuation for fuzzy matching.
    """
    titles = set()
    for fname in os.listdir(directory):
        ext = os.path.splitext(fname)[1].lower()
        if ext in VIDEO_EXTS:
            # Strip resolution tag and extension
            name = re.sub(r'\s*\(\d{3,4}p\)', '', os.path.splitext(fname)[0])
            titles.add(normalise(name))
    return titles


def normalise(title):
    """Lowercase, strip punctuation and extra whitespace for comparison."""
    title = title.lower()
    title = re.sub(r"[^\w\s]", "", title)   # remove punctuation
    title = re.sub(r"\s+", " ", title).strip()
    return title


def fetch_vimeo_videos(months):
    """
    Scrape the Vimeo user's video pages to collect videos uploaded
    within the cutoff window. Returns a list of dicts:
      { 'title': str, 'url': str, 'uploaded': datetime }
    """
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
    page = 1
    stop = False

    while not stop:
        url = f"https://vimeo.com/{VIMEO_USER}/videos/page:{page}/sort:date"
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  WARNING: Failed to fetch page {page}: {e}")
            break

        html = resp.text

        # Extract video entries: title and upload time from <time datetime="...">
        # Vimeo's HTML contains anchor tags with the title and a time element
        entries = re.findall(
            r'href="/(testeverything/\d+|(\d{7,12}))"[^>]*title="([^"]+)"',
            html
        )

        # Also extract via the thumbnail link pattern used in Vimeo's video grid
        # Pattern: href="/VIDEOID" followed by title text in the next link tag
        video_blocks = re.findall(
            r'href="https://vimeo\.com/(\d{7,12})"[^>]*>\s*([^<]{5,120}?)\s*<',
            html
        )

        # Primary extraction: look for the structured video card pattern
        # <a href="/VIDEOID" data-...>Title</a> with <time datetime="ISO">
        card_pattern = re.findall(
            r'"https://vimeo\.com/(\d{7,12})"[^>]*>\s*([\w][^\n<]{4,150}?)\s*\n.*?'
            r'(\d+) (second|minute|hour|day|week|month|year)s? ago',
            html, re.DOTALL
        )

        # Simpler reliable extraction from the page structure:
        # Find all video IDs and titles from the thumbnail href+title pattern
        found_on_page = []

        # Match: href="https://vimeo.com/VIDEOID" title="VIDEO TITLE"
        for m in re.finditer(
            r'href="https://vimeo\.com/(\d{7,12})[^"]*"\s+title="([^"]+)"',
            html
        ):
            vid_id, title = m.group(1), m.group(2)
            found_on_page.append((vid_id, title))

        # Also match the pattern: /VIDEOID "TITLE" N units ago
        time_matches = re.findall(
            r'"pubDate":\s*"([^"]+)".*?"link":\s*"https://vimeo\.com/(\d+)".*?"title":\s*"([^"]+)"',
            html, re.DOTALL
        )

        if not found_on_page and not time_matches:
            # Try alternate pattern seen in Vimeo's rendered HTML
            for m in re.finditer(
                r'<a href="/([\d]+)"[^>]*>([\s\S]+?)</a>\s*[\s\S]*?'
                r'(\d+) (second|minute|hour|day|week|month|year)s? ago',
                html
            ):
                pass  # fallback, handled below

        # Extract upload times from "N units ago" relative timestamps
        # Map each video ID to an approximate datetime
        time_ago_map = {}
        now = datetime.now(timezone.utc)
        for m in re.finditer(
            r'vimeo\.com/(\d{7,12})[^"]*"[\s\S]{1,500}?(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago',
            html
        ):
            vid_id = m.group(1)
            if vid_id in time_ago_map:
                continue
            n = int(m.group(2))
            unit = m.group(3)
            delta_map = {
                "second": relativedelta(seconds=n),
                "minute": relativedelta(minutes=n),
                "hour":   relativedelta(hours=n),
                "day":    relativedelta(days=n),
                "week":   relativedelta(weeks=n),
                "month":  relativedelta(months=n),
                "year":   relativedelta(years=n),
            }
            time_ago_map[vid_id] = now - delta_map[unit]

        # Check if any videos on this page are older than cutoff
        page_has_new = False
        for vid_id, title in found_on_page:
            uploaded = time_ago_map.get(vid_id, now)  # default to now if unknown
            if uploaded < cutoff:
                stop = True  # this video is too old, stop after this page
            else:
                page_has_new = True
                videos.append({
                    "title":    title.strip(),
                    "url":      f"https://vimeo.com/{vid_id}",
                    "uploaded": uploaded,
                    "id":       vid_id,
                })

        if not found_on_page:
            break  # no more videos found on this page

        print(f"  Scanned page {page} — {len(found_on_page)} videos found"
              f" ({len(videos)} total within window so far)")
        page += 1

    # Deduplicate by video ID
    seen = set()
    unique = []
    for v in videos:
        if v["id"] not in seen:
            seen.add(v["id"])
            unique.append(v)

    return unique


def find_missing(vimeo_videos, local_titles):
    """Return videos from Vimeo that aren't already on disk."""
    missing = []
    for v in vimeo_videos:
        if normalise(v["title"]) not in local_titles:
            missing.append(v)
    return missing


def download_video(url, title, index, total, output_dir):
    """Download a single video using yt-dlp."""
    print(f"\n  [{index}/{total}] {title}")
    print(f"           {url}")

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

    result = subprocess.run(cmd)
    return result.returncode == 0


def main():
    print_banner()

    # Step 1: Ask how many months back
    months = ask_months()
    print(f"\n  Got it — checking the last {months} month(s).")

    # Step 2: Determine working directory (where script is run from)
    work_dir = os.getcwd()
    print(f"\n  Working directory: {work_dir}")

    # Step 3: Scan local files
    print("  Scanning local video files...")
    local_titles = get_local_titles(work_dir)
    print(f"  Found {len(local_titles)} video file(s) on disk.")

    # Step 4: Fetch Vimeo listing
    vimeo_videos = fetch_vimeo_videos(months)
    if not vimeo_videos:
        print("\n  No videos found on Vimeo within that time window.")
        print("  This may be a scraping issue — try a larger month range.")
        sys.exit(0)

    print(f"\n  Found {len(vimeo_videos)} video(s) on Vimeo within the last {months} month(s).")

    # Step 5: Compare and find missing
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

    # Step 6: Download missing videos
    print()
    print("=" * 62)
    failed = []
    for i, v in enumerate(missing, 1):
        success = download_video(v["url"], v["title"], i, len(missing), work_dir)
        if not success:
            failed.append(v)

    # Step 7: Summary
    print()
    print("=" * 62)
    succeeded = len(missing) - len(failed)
    print(f"  Download complete: {succeeded}/{len(missing)} succeeded.")

    if failed:
        print(f"\n  The following {len(failed)} video(s) failed:")
        for v in failed:
            print(f"    - {v['title']}")
            print(f"      {v['url']}")

    print("=" * 62)
    print()


if __name__ == "__main__":
    main()
