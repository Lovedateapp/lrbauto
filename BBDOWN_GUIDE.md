# BBDown Quick Reference

## ✅ BBDown is Installed!

Test it: `BBDown --help`

---

## 🎯 Download All Videos from Bilibili User

```bash
# Download all videos to external HDD
BBDown --work-dir /Volumes/myminihdd/xhsvdo "https://space.bilibili.com/1966850363"
```

---

## 📥 Common Commands

```bash
# Download single video
BBDown --work-dir /Volumes/myminihdd/xhsvdo "https://www.bilibili.com/video/BV1234567890"

# Download with better quality (HEVC)
BBDown --work-dir /Volumes/myminihdd/xhsvdo --encoding-priority hevc "https://space.bilibili.com/1966850363"

# Download user's favorites
BBDown --work-dir /Volumes/myminihdd/xhsvdo "https://space.bilibili.com/1966850363/favlist"

# Download with subtitles
BBDown --work-dir /Volumes/myminihdd/xhsvdo --sub-only "VIDEO_URL"
```

---

## 🚀 Complete Workflow

### 1. Download all Bilibili videos
```bash
BBDown --work-dir /Volumes/myminihdd/xhsvdo "https://space.bilibili.com/1966850363"
```

### 2. Organize videos
```bash
cd /Users/emerson/Desktop/lrbauto
./organize_videos.sh
```

### 3. Edit metadata.json files
```bash
cd /Volumes/myminihdd/xhsvdo
# Edit each video_XXX/metadata.json with Chinese title/description
```

### 4. Process and upload to YouTube
```bash
cd /Users/emerson/Desktop/lrbauto
python3 -m src.main
```

---

## 💡 Tips

- Videos download directly to external HDD
- BBDown auto-merges audio and video
- Supports 4K quality
- Can resume interrupted downloads

---

## Ready to Download!

Run this now:
```bash
BBDown --work-dir /Volumes/myminihdd/xhsvdo "https://space.bilibili.com/1966850363"
```
