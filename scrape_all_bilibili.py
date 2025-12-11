#!/usr/bin/env python3
"""
Scrape all video links from all pages of Bilibili user's upload page.
21 pages × 40 videos = ~840 videos
"""
import requests
from bs4 import BeautifulSoup
import json
import re
import time

def scrape_page(uid, page_num):
    """Scrape a single page of videos"""
    
    url = f"https://space.bilibili.com/{uid}/video"
    
    params = {
        'pn': page_num,  # Page number
        'ps': 30,  # Videos per page
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://www.bilibili.com/',
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        
        html = response.text
        
        # Look for __INITIAL_STATE__ which contains video data
        match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', html, re.DOTALL)
        
        videos = []
        
        if match:
            try:
                data = json.loads(match.group(1))
                
                # Navigate through the data structure
                if 'archive' in data and 'item' in data['archive']:
                    for video in data['archive']['item']:
                        bvid = video.get('bvid')
                        title = video.get('title', 'Untitled')
                        if bvid:
                            videos.append({
                                'bvid': bvid,
                                'title': title,
                                'url': f'https://www.bilibili.com/video/{bvid}'
                            })
            except:
                pass
        
        # Fallback: parse HTML for BV links
        if not videos:
            soup = BeautifulSoup(html, 'html.parser')
            seen = set()
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '/video/BV' in href:
                    bv_match = re.search(r'(BV[a-zA-Z0-9]+)', href)
                    if bv_match:
                        bvid = bv_match.group(1)
                        if bvid not in seen:
                            seen.add(bvid)
                            title = link.get('title', link.get_text(strip=True) or 'Untitled')
                            videos.append({
                                'bvid': bvid,
                                'title': title[:100],
                                'url': f'https://www.bilibili.com/video/{bvid}'
                            })
        
        return videos
        
    except Exception as e:
        print(f"Error on page {page_num}: {e}")
        return []

def main():
    uid = "1966850363"
    total_pages = 21
    
    print("=" * 70)
    print(f"Scraping all videos from Bilibili user {uid}")
    print(f"Total pages: {total_pages}")
    print("=" * 70)
    print()
    
    all_videos = []
    seen_bvids = set()
    
    for page in range(1, total_pages + 1):
        print(f"Scraping page {page}/{total_pages}...", end=' ', flush=True)
        
        videos = scrape_page(uid, page)
        
        # Deduplicate
        new_videos = []
        for video in videos:
            if video['bvid'] not in seen_bvids:
                seen_bvids.add(video['bvid'])
                new_videos.append(video)
                all_videos.append(video)
        
        print(f"Found {len(new_videos)} new videos")
        
        # Be nice to the server
        time.sleep(1)
    
    print()
    print("=" * 70)
    print(f"✅ Total videos collected: {len(all_videos)}")
    print("=" * 70)
    print()
    
    if not all_videos:
        print("❌ No videos found. The scraping method may not be working.")
        print("   This is likely due to JavaScript rendering or anti-bot protection.")
        return
    
    # Save results
    output_dir = "/Volumes/myminihdd/xhsvdo"
    
    # Save URLs only
    with open(f"{output_dir}/bilibili_all_urls.txt", 'w', encoding='utf-8') as f:
        for video in all_videos:
            f.write(f"{video['url']}\n")
    
    print(f"✅ Saved {len(all_videos)} URLs to: {output_dir}/bilibili_all_urls.txt")
    
    # Save detailed list
    with open(f"{output_dir}/bilibili_all_videos.txt", 'w', encoding='utf-8') as f:
        for i, video in enumerate(all_videos, 1):
            f.write(f"{i}. {video['title']}\n")
            f.write(f"   {video['url']}\n\n")
    
    print(f"✅ Saved detailed list to: {output_dir}/bilibili_all_videos.txt")
    
    # Create download script
    with open(f"{output_dir}/download_all_videos.sh", 'w', encoding='utf-8') as f:
        f.write("#!/bin/bash\n\n")
        f.write(f"# Download all {len(all_videos)} videos from Bilibili user {uid}\n")
        f.write(f"# Total pages scraped: {total_pages}\n\n")
        
        for i, video in enumerate(all_videos, 1):
            title_safe = video['title'].replace('"', '\\"').replace('$', '\\$')
            f.write(f'echo "Downloading {i}/{len(all_videos)}: {title_safe}"\n')
            f.write(f'BBDown --work-dir /Volumes/myminihdd/xhsvdo "{video["url"]}"\n')
            f.write(f'echo ""\n\n')
        
        f.write('echo "✅ All {len(all_videos)} downloads complete!"\n')
    
    import os
    os.chmod(f"{output_dir}/download_all_videos.sh", 0o755)
    
    print(f"✅ Created download script: {output_dir}/download_all_videos.sh")
    
    print()
    print("🚀 To download all videos, run:")
    print(f"   {output_dir}/download_all_videos.sh")
    print()
    print(f"   This will download {len(all_videos)} videos to your external HDD")

if __name__ == "__main__":
    main()
