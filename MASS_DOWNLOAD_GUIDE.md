# Mass Download XHS Videos to External HDD

## 🎯 Setup Complete!

Your videos will be stored on external HDD: **myminihdd**

**Path:** `/Volumes/myminihdd/xhsvdo/`

---

## 📥 How to Mass Download Videos

### Step 1: Run XHS-Downloader

```bash
cd /Users/emerson/Desktop/lrbauto/XHS-Downloader_V2.6_macOS_ARM64
./main
```

### Step 2: Configure Download Location

In XHS-Downloader settings:
- **Set download folder to:** `/Volumes/myminihdd/xhsvdo/`
- Download as many videos as you want!

### Step 3: Organize Videos

After downloading, organize into folders:

```bash
cd /Volumes/myminihdd/xhsvdo

# For each video, create a folder
mkdir video_001
mv downloaded_video_1.mp4 video_001/video.mp4

mkdir video_002
mv downloaded_video_2.mp4 video_002/video.mp4

# etc...
```

### Step 4: Create metadata.json for each

For each video folder, create `metadata.json`:

```bash
cd video_001
nano metadata.json
```

**Template:**
```json
{
  "title": "视频的中文标题",
  "description": "视频的中文描述",
  "url": "https://www.xiaohongshu.com/explore/xxxxx"
}
```

**Repeat for all videos.**

---

## 🤖 Batch Processing Script

To make it easier, here's a helper script to create folders:

```bash
#!/bin/bash
# Save as: organize_videos.sh

cd /Volumes/myminihdd/xhsvdo

counter=1
for video in *.mp4; do
    if [ -f "$video" ]; then
        folder_name=$(printf "video_%03d" $counter)
        mkdir -p "$folder_name"
        mv "$video" "$folder_name/video.mp4"
        
        # Create template metadata
        cat > "$folder_name/metadata.json" << EOF
{
  "title": "请填写中文标题",
  "description": "请填写中文描述",
  "url": "https://www.xiaohongshu.com/explore/xxxxx"
}
EOF
        
        echo "Created $folder_name"
        ((counter++))
    fi
done

echo "Done! Now edit each metadata.json file with the correct Chinese title and description."
```

**Usage:**
```bash
chmod +x organize_videos.sh
./organize_videos.sh
```

---

## 🚀 Run Automation

Process all videos at once:

```bash
cd /Users/emerson/Desktop/lrbauto
python3 -m src.main
```

**Note:** By default, it processes **1 video per run**. To process more:

Edit `src/main.py`:
```python
DOWNLOAD_LIMIT_PER_RUN = 10  # Process 10 videos per run
```

Or run multiple times:
```bash
# Process 10 videos (run 10 times)
for i in {1..10}; do python3 -m src.main; done
```

---

## 📁 Folder Structure on External HDD

```
/Volumes/myminihdd/xhsvdo/
├── video_001/
│   ├── video.mp4
│   └── metadata.json
├── video_002/
│   ├── video.mp4
│   └── metadata.json
├── video_003/
│   ├── video.mp4
│   └── metadata.json
└── ... (as many as you want!)
```

---

## ✅ Benefits of External HDD

- ✅ **Unlimited storage** - Download hundreds of videos
- ✅ **Organized** - All videos in one place
- ✅ **Portable** - Take your video library anywhere
- ✅ **Safe** - Doesn't fill up your Mac's internal drive
- ✅ **Fast processing** - Automation reads directly from HDD

---

## 💡 Tips

1. **Keep HDD connected** when running automation
2. **Edit all metadata.json files** before processing
3. **Use batch script** to save time organizing
4. **Process in batches** of 10-20 videos at a time
5. **Check YouTube** after each batch

---

## 🔧 Configuration Updated

The system is now configured to use:
- **Videos directory:** `/Volumes/myminihdd/xhsvdo/`
- **Sample folder created:** `sample_video_001/`

**Ready to download!** 🎉
