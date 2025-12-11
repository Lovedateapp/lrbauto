# Local XHS Video Processing - Quick Start Guide

## 🎯 Quick Start (3 Steps)

### 1. Download Videos with XHS-Downloader

```bash
cd /Users/emerson/Desktop/lrbauto/XHS-Downloader_V2.6_macOS_ARM64
./main
```

Download 1-3 videos from Xiaohongshu.

### 2. Organize Your Videos

Move downloaded videos to folders:

```bash
cd /Users/emerson/Desktop/lrbauto/downloads/xhs_videos

# Create folder for each video
mkdir video_001
mv ~/Downloads/your_video.mp4 video_001/video.mp4

# Create metadata.json
nano video_001/metadata.json
```

**Paste this template:**
```json
{
  "title": "中国街头滑板技巧",
  "description": "这是一个关于中国街头滑板的精彩视频",
  "url": "https://www.xiaohongshu.com/explore/xxxxx"
}
```

Replace with your video's **Chinese title, description, and URL**.

### 3. Run Automation

```bash
cd /Users/emerson/Desktop/lrbauto
python3 -m src.main
```

**Done!** Video will be processed and uploaded to YouTube with:
- ✅ Bilingual title: `中文标题 | English Title`
- ✅ Bilingual description (Chinese + English)
- ✅ English subtitles burned in
- ✅ Auto-generated tags

---

## 📁 Folder Structure

```
downloads/xhs_videos/
├── video_001/
│   ├── video.mp4          ← Your downloaded video
│   └── metadata.json      ← Chinese title/description
├── video_002/
│   ├── video.mp4
│   └── metadata.json
└── sample_video_001/      ← Template folder (created)
    ├── metadata.json      ← Template to copy
    └── README.txt
```

---

## 📝 Metadata Template

**Required fields:**
- `title` - Original Chinese title
- `description` - Original Chinese description  
- `url` - Original XHS URL

**Optional fields:**
- `tags` - Array of Chinese tags

**Example:**
```json
{
  "title": "上海街头滑板",
  "description": "在上海外滩附近的滑板表演",
  "url": "https://www.xiaohongshu.com/explore/abc123",
  "tags": ["滑板", "上海", "街头"]
}
```

---

## 🎬 What Gets Uploaded to YouTube

**Title:**
```
上海街头滑板 | Shanghai Street Skateboarding
```

**Description:**
```
原标题: 上海街头滑板
Original Title: Shanghai Street Skateboarding

在上海外滩附近的滑板表演

Skateboarding performance near Shanghai Bund

Original video: https://www.xiaohongshu.com/explore/abc123
```

**Tags:**
```
shanghai, street, skateboarding, 滑板, 上海, china, chinese, 中国
```

---

## ⚙️ Configuration

Edit `src/main.py` to change:
- `DOWNLOAD_LIMIT_PER_RUN = 1` - Videos per run
- `privacy_status="private"` - Change to `"public"` when ready

---

## 🔄 Daily Workflow (10 min)

1. Run XHS-Downloader → Download 3 videos
2. Create folders → Add metadata.json for each
3. Run `python3 -m src.main` → Automation processes all
4. Check YouTube for uploads

---

## ✅ Benefits

- ✅ No anti-bot issues
- ✅ Keep Chinese titles
- ✅ Bilingual content
- ✅ Full control over videos
- ✅ No costs
- ✅ Works offline
