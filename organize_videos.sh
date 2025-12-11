#!/bin/bash
# organize_videos.sh
# Helper script to organize downloaded XHS videos into folders with metadata templates

echo "🎬 XHS Video Organizer"
echo "====================="
echo ""

# Change to videos directory
cd /Volumes/myminihdd/xhsvdo || {
    echo "❌ Error: Cannot access /Volumes/myminihdd/xhsvdo"
    echo "   Make sure your external HDD 'myminihdd' is connected!"
    exit 1
}

# Count MP4 files
mp4_count=$(ls -1 *.mp4 2>/dev/null | wc -l | tr -d ' ')

if [ "$mp4_count" -eq 0 ]; then
    echo "❌ No .mp4 files found in /Volumes/myminihdd/xhsvdo/"
    echo "   Please download videos first using XHS-Downloader"
    exit 1
fi

echo "📹 Found $mp4_count video(s) to organize"
echo ""

counter=1
for video in *.mp4; do
    if [ -f "$video" ]; then
        # Create folder name
        folder_name=$(printf "video_%03d" $counter)
        
        # Skip if folder already exists
        if [ -d "$folder_name" ]; then
            echo "⏭️  Skipping $video (folder $folder_name already exists)"
            ((counter++))
            continue
        fi
        
        # Create folder
        mkdir -p "$folder_name"
        
        # Move video
        mv "$video" "$folder_name/video.mp4"
        
        # Create metadata template
        cat > "$folder_name/metadata.json" << 'EOF'
{
  "title": "请填写中文标题",
  "description": "请填写中文描述",
  "url": "https://www.xiaohongshu.com/explore/xxxxx",
  "tags": ["标签1", "标签2", "标签3"]
}
EOF
        
        echo "✅ Created $folder_name/"
        ((counter++))
    fi
done

echo ""
echo "🎉 Done! Organized $((counter-1)) video(s)"
echo ""
echo "📝 Next steps:"
echo "   1. Edit each metadata.json file with the correct Chinese title and description"
echo "   2. Run: cd /Users/emerson/Desktop/lrbauto && python3 -m src.main"
echo ""
