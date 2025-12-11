#!/usr/bin/env python3
"""
Scrape all video links from Bilibili user's upload page.
"""
import requests
from bs4 import BeautifulSoup
import json
import re

def scrape_bilibili_videos(uid):
    """Scrape videos from upload page"""
    
    url = f"https://space.bilibili.com/{uid}/video"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://www.bilibili.com/',
    }
    
    print(f"Fetching: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Try to find video data in the page
        html = response.text
        
        # Look for __INITIAL_STATE__ which contains video data
        match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', html, re.DOTALL)
        
        if match:
            data = json.loads(match.group(1))
            
            videos = []
            
            # Try to extract from different possible locations
            if 'sectionEpisodes' in data:
                for section in data.get('sectionEpisodes', {}).values():
                    for ep in section.get('episodes', []):
                        bvid = ep.get('bvid')
                        title = ep.get('title', 'Untitled')
                        if bvid:
                            videos.append({
                                'bvid': bvid,
                                'title': title,
                                'url': f'https://www.bilibili.com/video/{bvid}'
                            })
            
            # Try archive list
            if 'archiveList' in data:
                for video in data['archiveList']:
                    bvid = video.get('bvid')
                    title = video.get('title', 'Untitled')
                    if bvid:
                        videos.append({
                            'bvid': bvid,
                            'title': title,
                            'url': f'https://www.bilibili.com/video/{bvid}'
                        })
            
            # Try vlist
            if 'vlist' in data:
                for video in data['vlist']:
                    bvid = video.get('bvid')
                    title = video.get('title', 'Untitled')
                    if bvid:
                        videos.append({
                            'bvid': bvid,
                            'title': title,
                            'url': f'https://www.bilibili.com/video/{bvid}'
                        })
            
            return videos
        
        # Fallback: parse HTML for BV links
        print("Trying HTML parsing fallback...")
        soup = BeautifulSoup(html, 'html.parser')
        
        videos = []
        seen = set()
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/video/BV' in href:
                # Extract BV ID
                bv_match = re.search(r'(BV[a-zA-Z0-9]+)', href)
                if bv_match:
                    bvid = bv_match.group(1)
                    if bvid not in seen:
                        seen.add(bvid)
                        title = link.get('title', link.get_text(strip=True) or 'Untitled')
                        videos.append({
                            'bvid': bvid,
                            'title': title[:100],  # Limit title length
                            'url': f'https://www.bilibili.com/video/{bvid}'
                        })
        
        return videos
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    uid = "1966850363"
    
    print("=" * 70)
    print(f"Scraping Bilibili user {uid} videos...")
    print("=" * 70)
    
    videos = scrape_bilibili_videos(uid)
    
    print(f"\n✅ Found {len(videos)} videos\n")
    
    if not videos:
        print("❌ No videos found. The page might require login or has anti-bot protection.")
        print("\nTry manually:")
        print(f"1. Visit: https://space.bilibili.com/{uid}/video")
        print("2. Scroll down to load all videos")
        print("3. Copy video URLs manually")
        return
    
    # Save results
    output_dir = "/Volumes/myminihdd/xhsvdo"
    
    # Save URLs only
    with open(f"{output_dir}/bilibili_urls.txt", 'w', encoding='utf-8') as f:
        for video in videos:
            f.write(f"{video['url']}\n")
    
    print(f"✅ Saved URLs to: {output_dir}/bilibili_urls.txt")
    
    # Save detailed list
    with open(f"{output_dir}/bilibili_videos.txt", 'w', encoding='utf-8') as f:
        for i, video in enumerate(videos, 1):
            f.write(f"{i}. {video['title']}\n")
            f.write(f"   {video['url']}\n\n")
    
    print(f"✅ Saved detailed list to: {output_dir}/bilibili_videos.txt")
    
    # Create download script
    with open(f"{output_dir}/download_all.sh", 'w', encoding='utf-8') as f:
        f.write("#!/bin/bash\n\n")
        f.write(f"# Download all {len(videos)} videos from Bilibili user {uid}\n\n")
        
        for i, video in enumerate(videos, 1):
            title_safe = video['title'].replace('"', '\\"')
            f.write(f'echo "Downloading {i}/{len(videos)}: {title_safe}"\n')
            f.write(f'BBDown --work-dir /Volumes/myminihdd/xhsvdo "{video["url"]}"\n\n')
        
        f.write('echo "✅ All downloads complete!"\n')
    
    import os
    os.chmod(f"{output_dir}/download_all.sh", 0o755)
    
    print(f"✅ Created download script: {output_dir}/download_all.sh")
    
    print(f"\n🚀 To download all {len(videos)} videos, run:")
    print(f"   {output_dir}/download_all.sh")

if __name__ == "__main__":
    main()
