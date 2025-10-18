# Custom PPTX Skill Setup Guide

⚠️ **DEPRECATED**: This guide is for the old Strategy A (skill-based) approach. 

**The project now uses Strategy B (Local Generation)** which doesn't require custom skills. See [CLAUDE.md](CLAUDE.md) for current architecture.

---

<details>
<summary>📜 Old documentation (for reference only)</summary>

Hướng dẫn cấu hình custom skill `pptx-enhanced` với hỗ trợ images và charts.

## Cách hoạt động

Hệ thống hỗ trợ 2 chế độ:

1. **Chế độ mặc định**: Sử dụng Anthropic's PPTX skill
2. **Chế độ custom**: Sử dụng skill `pptx-enhanced` đã upload

## Bước 1: Upload Custom Skill (Tùy chọn)

Nếu bạn muốn dùng skill `pptx-enhanced` với hỗ trợ images và charts nâng cao:

### Sử dụng Python SDK

```python
import anthropic
from anthropic.lib import files_from_dir

client = anthropic.Anthropic(api_key="your_api_key")

# Upload skill từ thư mục
skill = client.beta.skills.create(
    display_title="PPTX Enhanced with Images & Charts",
    files=files_from_dir(".claude/skills/pptx-enhanced"),
    betas=["skills-2025-10-02"]
)

print(f"Skill ID: {skill.id}")
print(f"Latest version: {skill.latest_version}")
```

### Hoặc sử dụng curl

```bash
# Nén skill thành zip
cd .claude/skills
zip -r pptx-enhanced.zip pptx-enhanced/

# Upload lên Anthropic
curl https://api.anthropic.com/v1/skills \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: skills-2025-10-02" \
  -F "display_title=PPTX Enhanced with Images & Charts" \
  -F "files=@pptx-enhanced.zip"
```

Bạn sẽ nhận được response với `skill.id`, ví dụ: `skill_01AbCdEfGhIjKlMnOpQrStUv`

## Bước 2: Cấu hình Skill ID

Thêm skill ID vào file `.env`:

```bash
# File .env
CUSTOM_PPTX_SKILL_ID=skill_01AbCdEfGhIjKlMnOpQrStUv
```

**Lưu ý**: Nếu không set `CUSTOM_PPTX_SKILL_ID`, hệ thống sẽ tự động dùng Anthropic's default PPTX skill.

## Bước 3: Kiểm tra cấu hình

```bash
# Chạy lệnh generate để kiểm tra
python3 -m voice_to_slide generate recording.mp3

# Xem log để confirm skill nào đang được dùng:
# - "Using custom PPTX skill: skill_01..." → Đang dùng custom skill
# - "Using Anthropic PPTX skill (default)" → Đang dùng default skill
```

## Skill Enhanced có gì khác?

Custom skill `pptx-enhanced` bao gồm:

### 1. Hướng dẫn sử dụng Unsplash images cache
- Tự động nhận diện images trong `.cache/images/`
- Hướng dẫn cách sử dụng cached images trong slides
- Naming convention: `slide_00_*.jpg`, `slide_01_*.jpg`, etc.

### 2. Chart generation templates
- Matplotlib examples cho bar, line, pie charts
- Best practices: 300 DPI, proper sizing
- Layout patterns cho slides có charts

### 3. Complete workflow examples
- Kết hợp Unsplash images + matplotlib charts
- JavaScript helper functions để load cached images
- Two-column layouts cho text + visuals

## Ví dụ sử dụng

```python
from voice_to_slide.presentation_generator import PresentationGenerator

# Initialize generator
generator = PresentationGenerator()

# Generate presentation (tự động dùng custom skill nếu có)
result = generator.generate_presentation(
    transcription_text="Your presentation content...",
    image_queries=["business meeting", "data analytics"],
    output_path="output/presentation.pptx",
    enhance=True
)
```

## Troubleshooting

### Skill ID không được nhận diện

**Kiểm tra**:
```bash
# Xem skill ID trong .env
cat .env | grep CUSTOM_PPTX_SKILL_ID

# Phải có dạng: skill_01...
```

### Error: "Invalid skill_id"

**Nguyên nhân**: Skill ID sai hoặc skill chưa được upload

**Giải pháp**:
1. Xóa hoặc comment dòng `CUSTOM_PPTX_SKILL_ID` trong `.env` để dùng default
2. Hoặc upload lại skill và lấy ID mới

### Skill không có images/charts

**Kiểm tra**:
1. Skill đã được upload đầy đủ chưa? (bao gồm SKILL.md, scripts/, etc.)
2. Check log khi generate xem có load đúng skill không

## Quản lý Skill versions

### List tất cả skills
```python
skills = client.beta.skills.list(betas=["skills-2025-10-02"])
for skill in skills.data:
    print(f"{skill.id}: {skill.display_title}")
```

### Update skill
```python
# Upload version mới
skill = client.beta.skills.create(
    display_title="PPTX Enhanced with Images & Charts",
    files=files_from_dir(".claude/skills/pptx-enhanced"),
    betas=["skills-2025-10-02"]
)
# Skill ID giữ nguyên, chỉ version thay đổi
```

### Xóa skill
```python
client.beta.skills.delete(
    skill_id="skill_01AbCdEfGhIjKlMnOpQrStUv",
    betas=["skills-2025-10-02"]
)
```

## Tham khảo

- [Anthropic Skills Documentation](https://docs.claude.com/en/docs/agents-and-tools/agent-skills)
- [Skills API Guide](https://docs.claude.com/en/api/skills-guide)
- Custom skill location: `.claude/skills/pptx-enhanced/`

</details>
