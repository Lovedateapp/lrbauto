#!/usr/bin/env python3
"""
Quick test script for Bilibili downloader
"""
import sys
sys.path.insert(0, '/Users/emerson/Desktop/lrbauto')

from src.bilibili_downloader import BilibiliDownloader
import logging

logging.basicConfig(level=logging.INFO)

# Test the downloader
downloader = BilibiliDownloader(user_id="1966850363")

print("=" * 60)
print("Testing Bilibili Downloader")
print("=" * 60)

# Test 1: Get latest videos
print("\n1. Fetching latest 3 videos...")
videos = downloader.get_latest_videos(limit=3)

if videos:
    print(f"\n✓ Found {len(videos)} videos:")
    for i, video in enumerate(videos, 1):
        print(f"\n  Video {i}:")
        print(f"    ID: {video['id']}")
        print(f"    Title: {video['title']}")
        print(f"    URL: {video['url']}")
else:
    print("\n✗ No videos found")
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ Bilibili downloader test PASSED!")
print("=" * 60)
