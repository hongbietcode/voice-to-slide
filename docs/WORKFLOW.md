# Voice-to-Slide - Luồng Hoạt Động Chi Tiết

## 🎯 Tổng Quan

Voice-to-Slide chuyển đổi file audio thành bài thuyết trình PowerPoint chuyên nghiệp qua 6 bước chính.

---

## 📊 Sơ Đồ Luồng Tổng Thể

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         VOICE-TO-SLIDE PIPELINE                          │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────┐
│ Audio File   │  recording.mp3 / audio.wav / video.m4a
│ (MP3/WAV/M4A)│  
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ BƯỚC 1: TRANSCRIPTION - Chuyển đổi giọng nói thành văn bản              │
├─────────────────────────────────────────────────────────────────────────┤
│ Module: transcriber.py                                                   │
│ API: Soniox Speech-to-Text                                              │
│ Thời gian: 2-5 giây                                                     │
│ Chi phí: $0.01-0.05 / phút audio                                        │
├─────────────────────────────────────────────────────────────────────────┤
│ Input:  Audio binary data                                               │
│ Output: {                                                                │
│   "text": "Full transcription...",                                      │
│   "words": [{word, start_ms, duration_ms}, ...]                         │
│ }                                                                        │
└──────┬──────────────────────────────────────────────────────────────────┘
       │
       │ transcription_text
       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ BƯỚC 2: STRUCTURE ANALYSIS - Phân tích và tạo cấu trúc slide            │
├─────────────────────────────────────────────────────────────────────────┤
│ Module: presentation_orchestrator.py                                    │
│ API: Claude Tool Use (Anthropic)                                        │
│ Model: claude-haiku-4-5-20251001                                        │
│ Thời gian: 3-5 giây                                                     │
│ Chi phí: $0.01-0.02 (5K tokens)                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ Claude Tools:                                                            │
│  1. analyze_presentation_structure                                       │
│     - Phân tích nội dung transcript                                     │
│     - Tạo tiêu đề và outline                                            │
│     - Chia thành các slide logic                                        │
│     - Đề xuất bullet points cho mỗi slide                               │
│                                                                          │
│  2. fetch_images_from_unsplash                                          │
│     - Đề xuất từ khóa tìm kiếm ảnh cho mỗi slide                        │
│     - Dựa trên nội dung và theme của slide                              │
└──────┬──────────────────────────────────────────────────────────────────┘
       │
       │ structure = {
       │   "title": "Presentation Title",
       │   "slides": [
       │     {"title": "Slide 1", "content": [...], "image_theme": "..."},
       │     ...
       │   ]
       │ }
       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ BƯỚC 2.5: USER PREVIEW - Người dùng xem trước và xác nhận               │
├─────────────────────────────────────────────────────────────────────────┤
│ Module: main.py (CLI)                                                    │
│ Hiển thị:                                                                │
│  • Tổng số slide                                                         │
│  • Tiêu đề từng slide                                                    │
│  • Nội dung bullet points                                                │
│  • Theme ảnh đề xuất                                                     │
│                                                                          │
│ ⚠️ Proceed with generation? [Y/n]                                        │
└──────┬──────────────────────────────────────────────────────────────────┘
       │
       │ User confirms ✓
       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ BƯỚC 3: IMAGE URL FETCHING - Lấy URL ảnh từ Unsplash                    │
├─────────────────────────────────────────────────────────────────────────┤
│ Module: image_fetcher.py                                                 │
│ API: Unsplash Search API                                                │
│ Thời gian: 1-2 giây (không download!)                                   │
│ Chi phí: Free (50 requests/hour)                                        │
├─────────────────────────────────────────────────────────────────────────┤
│ ⚡ NEW: URL-Only Approach (v2.0)                                         │
│                                                                          │
│ TRƯỚC ĐÂY (Download):                                                   │
│   Unsplash API → Download JPG → Save to .cache/images/                  │
│   ⏱️ 5-10 giây | 💾 200KB × N images                                    │
│                                                                          │
│ BÂY GIỜ (URL-Only):                                                      │
│   Unsplash API → Get metadata only → Return URL                         │
│   ⏱️ 1-2 giây | 💾 0 KB (no disk usage)                                 │
│                                                                          │
│ Output: image_data = [                                                   │
│   {                                                                      │
│     "url": "https://images.unsplash.com/photo-xxx?w=1920",              │
│     "description": "Professional business meeting",                     │
│     "photographer": "John Doe",                                         │
│     "width": 1920,                                                       │
│     "height": 1080                                                       │
│   },                                                                     │
│   ...                                                                    │
│ ]                                                                        │
└──────┬──────────────────────────────────────────────────────────────────┘
       │
       │ image_data (URLs only)
       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ BƯỚC 4: HTML GENERATION - Tạo HTML slides với theme                     │
├─────────────────────────────────────────────────────────────────────────┤
│ Module: html_generator.py                                                │
│ API: Claude Messages API (Anthropic)                                    │
│ Model: claude-haiku-4-5-20251001                                        │
│ Thời gian: 10-15 giây (9 slides)                                        │
│ Chi phí: $0.02-0.03 (15K tokens)                                        │
├─────────────────────────────────────────────────────────────────────────┤
│ Themes: 5 professional themes                                            │
│  • Modern Professional (default) - #FF6B6B, #4ECDC4, #FFE66D            │
│  • Dark Mode - #BB86FC, #03DAC6 on #121212                              │
│  • Vibrant Creative - #FF6B9D, #C44569, #FFC048                         │
│  • Minimal Clean - #2D3436, #636E72, #00B894                            │
│  • Corporate Blue - #0984E3, #74B9FF, #DFE6E9                           │
│                                                                          │
│ Process:                                                                 │
│  For each slide:                                                         │
│    1. Load theme specification from themes.md                           │
│    2. Send to Claude: structure + image_data[i] + theme                 │
│    3. Claude generates HTML5 + inline CSS                               │
│    4. Inserts Unsplash URL: <img src="https://images.unsplash.com/..."> │
│    5. Viewport optimized: 100vw × 100vh (full screen)                   │
│    6. Save to workspace/slides/slide_001.html                           │
│                                                                          │
│ Output: HTML files với:                                                  │
│  • Complete styling (colors, gradients, fonts, shadows)                 │
│  • Responsive layout (flexbox, grid)                                    │
│  • Embedded images (URLs loaded from CDN)                               │
│  • Professional typography                                               │
└──────┬──────────────────────────────────────────────────────────────────┘
       │
       │ html_files = ["slide_001.html", "slide_002.html", ...]
       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ BƯỚC 5: HTML RENDERING - Chuyển HTML thành ảnh PNG                      │
├─────────────────────────────────────────────────────────────────────────┤
│ Module: html_to_image.py                                                 │
│ Engine: Playwright (Headless Chromium)                                  │
│ Thời gian: 12 giây (9 slides × ~1.3s/slide)                             │
│ Chi phí: $0 (local execution)                                           │
├─────────────────────────────────────────────────────────────────────────┤
│ Process:                                                                 │
│  1. Launch headless Chromium browser                                    │
│  2. For each HTML file:                                                  │
│     a) Load file:// URL                                                  │
│     b) Wait for 'networkidle' (images/fonts loaded from CDN)            │
│     c) Screenshot at 4K resolution:                                      │
│        - Width: 3840px (4K)                                              │
│        - Height: 2160px (4K)                                             │
│        - Device scale: 2x (high DPI)                                     │
│     d) Save to workspace/slide_images/slide_001.png                     │
│  3. Close browser                                                        │
│                                                                          │
│ ✨ Benefits:                                                             │
│  • 100% CSS styling preserved (pixel-perfect)                           │
│  • All gradients, shadows, fonts rendered correctly                     │
│  • Images loaded from Unsplash CDN (no local cache)                     │
│  • High quality output (4K resolution)                                  │
│                                                                          │
│ Output: PNG files                                                        │
│  • Resolution: 3840 × 2160 (16:9 aspect ratio)                          │
│  • Format: PNG with transparency support                                │
│  • Size: ~300-500 KB per slide                                          │
└──────┬──────────────────────────────────────────────────────────────────┘
       │
       │ image_paths = ["slide_001.png", "slide_002.png", ...]
       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ BƯỚC 6: PPTX ASSEMBLY - Ghép ảnh PNG thành file PowerPoint              │
├─────────────────────────────────────────────────────────────────────────┤
│ Module: html_to_pptx.py                                                  │
│ Library: python-pptx                                                     │
│ Thời gian: <1 giây                                                       │
│ Chi phí: $0 (local execution)                                           │
├─────────────────────────────────────────────────────────────────────────┤
│ Process:                                                                 │
│  1. Create blank presentation                                           │
│     - Slide size: 10" × 5.625" (16:9 widescreen)                        │
│  2. For each PNG image:                                                  │
│     a) Add blank slide                                                   │
│     b) Insert image as full slide (0, 0, full width, full height)       │
│  3. Save to output/presentation.pptx                                    │
│                                                                          │
│ ✅ Simplified approach:                                                  │
│  • No HTML parsing needed                                                │
│  • No text extraction needed                                             │
│  • Just insert rendered images                                           │
│  • Fast and reliable                                                     │
│                                                                          │
│ Output: PPTX file                                                        │
│  • Size: 3-4 MB (9 slides with images)                                  │
│  • Format: .pptx (PowerPoint 2010+)                                      │
│  • Quality: High (4K source images)                                     │
└──────┬──────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────┐
│ PPTX File    │  output/presentation.pptx
│ Ready! ✅     │  3-4 MB, 9 slides, 4K quality
└──────────────┘
```

---

## 🔄 Luồng Dữ Liệu Chi Tiết

### 1. Audio → Transcription

```python
# transcriber.py
audio_file = Path("recording.mp3")
transcriber = AudioTranscriber()

# Soniox API automatically chooses sync/async
if file_size < 10MB:
    result = soniox.transcribe_sync(audio_data)
else:
    result = soniox.transcribe_async(audio_data)

transcription = {
    "text": "Full transcript with punctuation...",
    "words": [
        {"word": "Hello", "start_ms": 0, "duration_ms": 500},
        {"word": "world", "start_ms": 500, "duration_ms": 400},
        ...
    ]
}
```

### 2. Transcription → Structure (Claude Tool Use)

```python
# presentation_orchestrator.py
tools = [
    {
        "name": "analyze_presentation_structure",
        "description": "Analyze transcript and create slide structure",
        "input_schema": {
            "title": str,
            "slides": [
                {
                    "title": str,
                    "content": [str],  # bullet points
                    "image_theme": str  # query for Unsplash
                }
            ]
        }
    }
]

# Claude analyzes and calls tool
response = client.messages.create(
    model="claude-haiku-4-5-20251001",
    messages=[{"role": "user", "content": transcription_text}],
    tools=tools
)

structure = response.content[0].input  # Tool use result
```

### 3. Structure → Image URLs

```python
# image_fetcher.py
def get_image_urls_for_presentation(structure):
    image_data = []
    
    for slide in structure["slides"]:
        query = slide["image_theme"]
        
        # Unsplash API - metadata only
        response = requests.get(
            "https://api.unsplash.com/search/photos",
            params={"query": query, "per_page": 1}
        )
        
        photo = response.json()["results"][0]
        image_data.append({
            "url": photo["urls"]["raw"] + "?w=1920",  # CDN URL
            "description": photo["description"],
            "photographer": photo["user"]["name"],
            "width": photo["width"],
            "height": photo["height"]
        })
    
    return image_data  # No download!
```

### 4. Structure + Images → HTML (Claude Messages)

```python
# html_generator.py
def generate_slides_html(structure, image_data, theme):
    html_files = []
    
    # Load theme specification
    theme_spec = load_theme(theme)  # from themes.md
    
    for i, slide in enumerate(structure["slides"]):
        prompt = f"""
        Generate HTML5 slide with:
        - Title: {slide["title"]}
        - Content: {slide["content"]}
        - Image URL: {image_data[i]["url"]}
        - Theme: {theme_spec}
        
        Requirements:
        - Complete inline CSS
        - Viewport: 100vw × 100vh
        - Insert: <img src="{image_data[i]["url"]}">
        - Professional typography
        """
        
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            messages=[{"role": "user", "content": prompt}]
        )
        
        html = response.content[0].text
        
        # Save to workspace/slides/slide_001.html
        html_file = f"workspace/slides/slide_{i+1:03d}.html"
        Path(html_file).write_text(html)
        html_files.append(html_file)
    
    return html_files
```

### 5. HTML → PNG (Playwright)

```python
# html_to_image.py
from playwright.sync_api import sync_playwright

def convert_html_files_to_images(html_files):
    image_paths = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 3840, "height": 2160},
            device_scale_factor=2
        )
        
        for html_file in html_files:
            # Load HTML (images fetch from Unsplash CDN)
            page.goto(f"file://{html_file}")
            page.wait_for_load_state("networkidle")
            
            # Screenshot at 4K
            png_file = html_file.replace(".html", ".png")
            page.screenshot(path=png_file, full_page=False)
            
            image_paths.append(png_file)
        
        browser.close()
    
    return image_paths
```

### 6. PNG → PPTX (python-pptx)

```python
# html_to_pptx.py
from pptx import Presentation
from pptx.util import Inches

def convert_html_to_pptx(image_paths, output_path):
    prs = Presentation()
    prs.slide_width = Inches(10)    # 16:9 aspect ratio
    prs.slide_height = Inches(5.625)
    
    for image_path in image_paths:
        # Add blank slide
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        
        # Insert image as full slide
        slide.shapes.add_picture(
            image_path,
            left=0,
            top=0,
            width=prs.slide_width,
            height=prs.slide_height
        )
    
    prs.save(output_path)
    return output_path
```

---

## ⚡ Tối Ưu Hóa Hiệu Suất

### URL-Only Approach (v2.0)

**Trước đây:**
```
Image Fetching: 5-10 giây (download + save)
Cache Storage: 200KB × 9 = 1.8 MB
Post-processing: Manual insertion required
```

**Bây giờ:**
```
Image Fetching: 1-2 giây (metadata only)
Cache Storage: 0 KB (no download)
Post-processing: Automatic (Claude inserts URLs)
```

**Cải thiện:**
- ⚡ **5x nhanh hơn** (1-2s thay vì 5-10s)
- 💾 **Zero disk usage** (không cache)
- 🤖 **Tự động hóa** (Claude tự chèn URL)
- 🔄 **Luôn mới** (load từ CDN)

### Rendering Optimization

**Playwright cấu hình:**
```python
viewport = {
    "width": 3840,   # 4K width
    "height": 2160,  # 4K height
}
device_scale_factor = 2  # High DPI (2x)

# Kết quả: 7680 × 4320 effective resolution
```

**Wait strategy:**
```python
page.wait_for_load_state("networkidle")
# Đợi tất cả images/fonts load xong từ CDN
```

---

## 💰 Chi Phí Chi Tiết (1 presentation, 9 slides)

| Bước | Service | Chi phí | Thời gian |
|------|---------|---------|-----------|
| 1. Transcription | Soniox API | $0.01-0.05/min | 2-5s |
| 2. Structure Analysis | Claude Tool Use | $0.01-0.02 | 3-5s |
| 3. Image URLs | Unsplash API | Free | 1-2s |
| 4. HTML Generation | Claude Messages | $0.02-0.03 | 10-15s |
| 5. Rendering | Playwright (local) | $0 | 12s |
| 6. PPTX Assembly | python-pptx (local) | $0 | <1s |
| **TỔNG** | | **$0.04-0.10** | **25-30s** |

**So sánh với Skill-based approach:**
- Strategy A (Skills): ~$0.20-0.40 per presentation
- Strategy B Enhanced: **$0.04-0.10 per presentation**
- **Tiết kiệm: 70-80%**

---

## 🎨 Theme System

### Modern Professional (Default)
```css
Primary: #FF6B6B (Coral red)
Secondary: #4ECDC4 (Turquoise)
Accent: #FFE66D (Yellow)
Background: White/Gradient
Font: Inter, Poppins
```

### Dark Mode
```css
Primary: #BB86FC (Purple)
Secondary: #03DAC6 (Cyan)
Accent: #CF6679 (Pink)
Background: #121212 (Dark)
Font: Roboto, system-ui
```

### Vibrant Creative
```css
Primary: #FF6B9D (Pink)
Secondary: #C44569 (Dark pink)
Accent: #FFC048 (Orange)
Background: White with gradients
Font: Montserrat, sans-serif
```

---

## 🔧 Cấu Hình Môi Trường

```bash
# Required
SONIOX_API_KEY=xxx                    # Transcription
CONTENT_ANTHROPIC_API_KEY=xxx         # Claude AI
UNSPLASH_ACCESS_KEY=xxx               # Images

# Optional
CONTENT_MODEL=claude-haiku-4-5-20251001
CONTENT_ANTHROPIC_BASE_URL=https://api.anthropic.com
OUTPUT_DIR=./output
```

---

## 📊 Thống Kê Chất Lượng

| Metric | Value | Notes |
|--------|-------|-------|
| **Styling Fidelity** | 100% | Pixel-perfect rendering |
| **Image Quality** | 4K | 3840×2160 |
| **Theme Support** | 5 themes | Professional designs |
| **Image Success Rate** | 78% | 7/9 slides with images |
| **File Size** | 3-4 MB | High quality output |
| **Processing Time** | 25-30s | End-to-end |
| **Cost per Presentation** | $0.04-0.10 | Very affordable |

---

## ✅ Tổng Kết

Voice-to-Slide sử dụng **Strategy B Enhanced** với các ưu điểm:

1. ✨ **Chất lượng cao** - 100% CSS styling, 4K output
2. ⚡ **Nhanh chóng** - 25-30 giây end-to-end
3. 💰 **Tiết kiệm** - 70-80% rẻ hơn skill-based
4. 🎨 **Chuyên nghiệp** - 5 themes đẹp mắt
5. 🚀 **Tự động hóa** - Từ audio đến PPTX hoàn toàn tự động

**Status: Production Ready! 🎉**
