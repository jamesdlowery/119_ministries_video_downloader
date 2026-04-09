#!/bin/bash
# ============================================================
# 119 Ministries - Missing Videos Downloader
# Downloads 53 missing English videos from Vimeo in 1080p
# Requires: yt-dlp  (install with: pip install yt-dlp)
# Usage:    bash download_missing_videos.sh
# ============================================================

OUTPUT_DIR="./119_Ministries_Missing_Videos"
mkdir -p "$OUTPUT_DIR"

# Download one video at a time, best quality up to 1080p,
# named by video title, skipping any already downloaded.
YTDLP_OPTS=(
    --format "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"
    --merge-output-format mp4
    --output "$OUTPUT_DIR/%(title)s (%(height)sp).%(ext)s"
    --no-playlist
    --sleep-interval 3
    --max-sleep-interval 8
    --no-overwrites
    --continue
    --progress
    --impersonate "Chrome-133"
    --cookies-from-browser firefox
)

YTDLP=/usr/local/bin/yt-dlp

VIDEOS=(
    # --- Newer videos (~past year) ---
    "https://vimeo.com/1160353542"   # Strange Fire: When Sincerity is Not Enough
    "https://vimeo.com/1158684483"   # The Brit Hadasha Series - The MEM Mystery
    "https://vimeo.com/1156378505"   # Why Bible Prophecy Is Hidden from the Masses
    "https://vimeo.com/1151994940"   # All That I Have Commanded You: Torah to the Nations
    "https://vimeo.com/1151055813"   # Refined by Fire: Faithfulness in the Midst of Suffering
    "https://vimeo.com/1149878108"   # God's Law on the Menu | 119 Scripture Sketches
    "https://vimeo.com/1147491546"   # 2025 - End of Year Update
    "https://vimeo.com/1134195229"   # Peoples of the Bible: The Babylonians
    "https://vimeo.com/1129337332"   # What the Bible Says about Modest Clothing for Men and Women
    "https://vimeo.com/1128783974"   # Created for Good Works: Torah as the Foundation of Righteous Living
    "https://vimeo.com/1127687983"   # Love Your Enemies (Matthew 5:43-48)
    "https://vimeo.com/1123739761"   # "Do Whatever They Tell You": Scribes, Pharisees, and Moses' Seat
    "https://vimeo.com/1121204102"   # Justification, Sanctification, and Salvation - Understanding the Relationship
    "https://vimeo.com/1120096139"   # A Biblical Test of the Pre-Trib Rapture Doctrine
    "https://vimeo.com/1118721930"   # Praise and Worship: Is There a Difference?
    "https://vimeo.com/1115642188"   # Clouds That Are Not Clouds: Unveiling the Heavenly Vessels of Scripture
    "https://vimeo.com/1112207589"   # Paul Was Not an Antinomian: A Rebuttal to Rabbi Tovia Singer
    "https://vimeo.com/1108342143"   # Peoples of the Bible: The Egyptians
    "https://vimeo.com/1105822406"   # Moses is Proclaimed Every Sabbath in the Synagogues (Acts 15:21)
    "https://vimeo.com/1104003215"   # The Antichrist Agenda and the Great Delusion
    "https://vimeo.com/1100207622"   # The Greatest Problem | Why Nothing Matters Without the Resurrection
    "https://vimeo.com/1099272207"   # The Sabbath in Luke-Acts: The Practice of the Earliest Christians
    "https://vimeo.com/1094596344"   # The Exiled Prophet, Part 14: Awake to Everlasting Life (Daniel 12)
    "https://vimeo.com/1091326201"   # Grafted Branches: The Identity of the Redeemed | Audio Sermon
    "https://vimeo.com/1090827511"   # Looking With Lustful Intent (Matthew 5:27-30)
    "https://vimeo.com/1085409725"   # The Exiled Prophet, Part 13: Wars and Desolations (Daniel 11)
    "https://vimeo.com/1084318600"   # 119 Shorts - Why is Christ Freedom?
    "https://vimeo.com/1081681069"   # Christ's Sacrifice Once for All: Is the Levitical Priesthood Replaced?
    "https://vimeo.com/1078162337"   # The Age To Come: How to Time Travel to the Future
    "https://vimeo.com/1076785532"   # 119 Shorts | 1,000 Years of Bondage
    "https://vimeo.com/1075749536"   # Hebrews 4: In His Rest Now or Later? -- NOTE: verify if already owned
    "https://vimeo.com/1074212238"   # Strange Math: Does Good Friday to Resurrection Sunday Add Up?
    "https://vimeo.com/1067726844"   # Is Michael the Archangel Another Name for the Messiah?
    "https://vimeo.com/1066248712"   # Eating Clean, Living Clean | Audio Sermon
    "https://vimeo.com/1065333196"   # The Sabbath: A Test of the Heart | Audio Sermon
    "https://vimeo.com/1065327451"   # Persevering Through the Fire | Audio Sermon
    "https://vimeo.com/1065320504"   # The Weight of Sin | Audio Sermon
    "https://vimeo.com/1064700137"   # God's Law in Prophecy
    "https://vimeo.com/1062212434"   # The Narrow Path | Audio Sermon
    "https://vimeo.com/1061177212"   # Do Not Resist the One who is Evil (Matthew 5:38-42)
    "https://vimeo.com/1060784258"   # Hair, Beards, and Markings in Ancient Mourning Practices
    "https://vimeo.com/1059098974"   # God's Law for Our Good
    "https://vimeo.com/1058906570"   # Confusion and Contradictions
    "https://vimeo.com/1056626104"   # 119 Ministries | Important Update
    "https://vimeo.com/1056142519"   # Have you misunderstood what the NT teaches about God's Law?
    "https://vimeo.com/1053374970"   # Was God's Tabernacle a Circle?
    "https://vimeo.com/1050989647"   # Speaking in Tongues Part 3: FAQ
    "https://vimeo.com/1048927227"   # Peoples of the Bible: The Assyrians
    "https://vimeo.com/1043091131"   # Peoples of the Bible: The Canaanites
    "https://vimeo.com/1044311463"   # Confirm Your Calling: The Error of Lawless People (2 Peter 3:14-18)
    "https://vimeo.com/1025576170"   # Exciting News From 119 Ministries!
    "https://vimeo.com/901078044"    # "I Gave Them Statutes That Were Not Good" (Ezekiel 20:25-26)

    # --- Additional missing (~2-3 years ago) ---
    "https://vimeo.com/829075543"    # Tangled: Sabbath Reflections | The Parable of the Sower
    "https://vimeo.com/772427465"    # 2022 End of Year Update
)

YTDLP=/usr/local/bin/yt-dlp

TOTAL=${#VIDEOS[@]}
COUNT=0
FAILED=()

echo "=============================================="
echo " 119 Ministries Missing Videos Downloader"
echo " Output folder: $OUTPUT_DIR"
echo " Total videos:  $TOTAL"
echo "=============================================="
echo ""

for URL in "${VIDEOS[@]}"; do
    COUNT=$((COUNT + 1))
    echo "[$COUNT/$TOTAL] Downloading: $URL"
    if $YTDLP "${YTDLP_OPTS[@]}" "$URL"; then
        echo "  -> Done."
    else
        echo "  -> FAILED: $URL"
        FAILED+=("$URL")
    fi
    echo ""
done

echo "=============================================="
echo "Download complete: $((TOTAL - ${#FAILED[@]}))/$TOTAL succeeded."

if [ ${#FAILED[@]} -gt 0 ]; then
    echo ""
    echo "FAILED URLs (${#FAILED[@]}):"
    for F in "${FAILED[@]}"; do
        echo "  $F"
    done
fi
echo "=============================================="
