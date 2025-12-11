#!/usr/bin/env python3
"""
Create download script from bilibili_video_links.txt
"""
import os
import sys

# Check common locations
possible_paths = [
    "bilibili_video_links.txt",
    "/Users/emerson/Desktop/lrbauto/bilibili_video_links.txt",
    "/Users/emerson/Desktop/bilibili_video_links.txt",
    "/Users/emerson/Downloads/bilibili_video_links.txt",
    "/Volumes/myminihdd/xhsvdo/bilibili_video_links.txt",
]

input_file = None
for path in possible_paths:
    if os.path.exists(path):
        input_file = path
        break

if not input_file:
    print("❌ Could not find bilibili_video_links.txt")
    print("\nPlease specify the full path:")
    print("  python3 create_bilibili_download.py /path/to/bilibili_video_links.txt")
    print("\nOr move the file to one of these locations:")
    for path in possible_paths:
        print(f"  - {path}")
    sys.exit(1)

print(f"📄 Found file: {input_file}")
print()

# Read URLs
with open(input_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

urls = []
for line in lines:
    line = line.strip()
    if line and (line.startswith('http') or line.startswith('BV')):
        # Handle both full URLs and just BV IDs
        if line.startswith('BV'):
            url = f"https://www.bilibili.com/video/{line}"
        else:
            url = line
        urls.append(url)

print(f"✅ Found {len(urls)} video URLs")
print()

if not urls:
    print("❌ No valid URLs found in file")
    sys.exit(1)

# Create download script
output_script = "/Volumes/myminihdd/xhsvdo/download_all_bilibili.sh"

with open(output_script, 'w', encoding='utf-8') as f:
    f.write("#!/bin/bash\n\n")
    f.write(f"# Download {len(urls)} Bilibili videos\n")
    f.write(f"# Generated from: {input_file}\n\n")
    f.write('echo "🎬 Starting download of all Bilibili videos..."\n')
    f.write('echo ""\n\n')
    
    for i, url in enumerate(urls, 1):
        f.write(f'echo "📥 Downloading {i}/{len(urls)}..."\n')
        f.write(f'BBDown --use-tv-api --work-dir /Volumes/myminihdd/xhsvdo --ffmpeg-path /usr/local/bin/ffmpeg "{url}"\n')
        f.write('echo ""\n\n')
    
    f.write(f'echo "✅ All {len(urls)} downloads complete!"\n')
    f.write('echo ""\n')
    f.write('echo "📁 Videos saved to: /Volumes/myminihdd/xhsvdo/"\n')

os.chmod(output_script, 0o755)

print(f"✅ Created download script: {output_script}")
print()
print("🚀 To download all videos, run:")
print(f"   {output_script}")
print()
print(f"   This will download {len(urls)} videos to your external HDD")
