#!/usr/bin/env python3
"""
Process video URLs from a text file and create download script.
"""

def create_download_script():
    print("=" * 70)
    print("Bilibili Batch Downloader - URL Input Method")
    print("=" * 70)
    print()
    print("Since automated scraping is blocked, please:")
    print("1. Visit: https://space.bilibili.com/1966850363/video")
    print("2. Scroll down to see all videos")
    print("3. Copy each video URL (right-click → Copy Link)")
    print("4. Paste URLs into: video_urls.txt (one per line)")
    print()
    print("Then run this script again to generate download_all.sh")
    print()
    
    # Create template file
    with open("video_urls.txt", 'w', encoding='utf-8') as f:
        f.write("# Bilibili Video URLs\n")
        f.write("# Paste video URLs here (one per line)\n")
        f.write("# Format: https://www.bilibili.com/video/BVxxxxxxxxx\n\n")
        f.write("# Example:\n")
        f.write("# https://www.bilibili.com/video/BV1234567890\n\n")
        f.write("# Add your URLs below:\n\n")
    
    print("✅ Created template file: video_urls.txt")
    print()
    
    # Check if URLs exist
    try:
        with open("video_urls.txt", 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        urls = [line.strip() for line in lines 
                if line.strip() and not line.strip().startswith('#')]
        
        if urls:
            print(f"Found {len(urls)} URLs in video_urls.txt")
            
            # Create download script
            with open("/Volumes/myminihdd/xhsvdo/download_all.sh", 'w', encoding='utf-8') as f:
                f.write("#!/bin/bash\n\n")
                f.write(f"# Download {len(urls)} Bilibili videos\n\n")
                
                for i, url in enumerate(urls, 1):
                    f.write(f'echo "Downloading {i}/{len(urls)}..."\n')
                    f.write(f'BBDown --work-dir /Volumes/myminihdd/xhsvdo "{url}"\n\n')
                
                f.write('echo "✅ All downloads complete!"\n')
            
            import os
            os.chmod("/Volumes/myminihdd/xhsvdo/download_all.sh", 0o755)
            
            print("✅ Created: /Volumes/myminihdd/xhsvdo/download_all.sh")
            print()
            print("🚀 To download all videos, run:")
            print("   /Volumes/myminihdd/xhsvdo/download_all.sh")
        else:
            print("No URLs found yet. Please add URLs to video_urls.txt")
    
    except FileNotFoundError:
        pass

if __name__ == "__main__":
    create_download_script()
