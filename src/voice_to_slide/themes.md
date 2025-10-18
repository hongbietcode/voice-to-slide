# Presentation Themes & Styles

This file defines presentation themes and styles used for HTML slide generation.

## Theme Structure

Each theme defines:
- **Color Palette**: Primary, secondary, accent, background, text colors
- **Typography**: Font families, sizes, weights
- **Layout**: Slide dimensions, padding, spacing
- **Visual Style**: Borders, shadows, animations

## Available Themes

### 1. Modern Professional (default)

Clean, minimalist design for business presentations.

**Colors:**
- Primary: #2C3E50 (dark blue-gray)
- Secondary: #3498DB (bright blue)
- Accent: #E74C3C (coral red)
- Background: #FFFFFF (white)
- Text: #2C3E50 (dark)
- Text Light: #7F8C8D (gray)

**Typography:**
- Font Family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif
- Title Size: 44px
- Heading Size: 32px
- Body Size: 20px
- Line Height: 1.6

**Layout:**
- Slide Size: 960px × 540px (16:9)
- Padding: 60px
- Content Width: 840px

**Style:**
- Border Radius: 8px
- Box Shadow: 0 2px 8px rgba(0,0,0,0.1)
- Transition: all 0.3s ease

---

### 2. Dark Mode

Bold, high-contrast design for impact.

**Colors:**
- Primary: #1A1A1A (almost black)
- Secondary: #BB86FC (purple)
- Accent: #03DAC6 (teal)
- Background: #121212 (dark gray)
- Text: #FFFFFF (white)
- Text Light: #B3B3B3 (light gray)

**Typography:**
- Font Family: 'Inter', 'SF Pro Display', system-ui, sans-serif
- Title Size: 48px
- Heading Size: 36px
- Body Size: 22px
- Line Height: 1.7

**Layout:**
- Slide Size: 960px × 540px (16:9)
- Padding: 70px
- Content Width: 820px

**Style:**
- Border Radius: 12px
- Box Shadow: 0 4px 20px rgba(187,134,252,0.2)
- Transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1)

---

### 3. Vibrant Creative

Colorful, energetic design for creative presentations.

**Colors:**
- Primary: #FF6B6B (coral)
- Secondary: #4ECDC4 (turquoise)
- Accent: #FFE66D (yellow)
- Background: #F7F7F7 (off-white)
- Text: #2D3436 (charcoal)
- Text Light: #636E72 (gray)

**Typography:**
- Font Family: 'Poppins', 'Montserrat', sans-serif
- Title Size: 52px (bold)
- Heading Size: 36px (semibold)
- Body Size: 20px
- Line Height: 1.8

**Layout:**
- Slide Size: 960px × 540px (16:9)
- Padding: 50px
- Content Width: 860px

**Style:**
- Border Radius: 16px
- Box Shadow: 0 8px 24px rgba(78,205,196,0.15)
- Transition: transform 0.3s ease

---

### 4. Minimal Clean

Ultra-minimal design with maximum readability.

**Colors:**
- Primary: #000000 (black)
- Secondary: #666666 (gray)
- Accent: #0066FF (blue)
- Background: #FFFFFF (white)
- Text: #000000 (black)
- Text Light: #999999 (light gray)

**Typography:**
- Font Family: 'Helvetica', 'Arial', sans-serif
- Title Size: 56px (light)
- Heading Size: 40px (regular)
- Body Size: 24px
- Line Height: 2.0

**Layout:**
- Slide Size: 960px × 540px (16:9)
- Padding: 80px
- Content Width: 800px

**Style:**
- Border Radius: 0px
- Box Shadow: none
- Transition: opacity 0.2s ease

---

### 5. Corporate Blue

Traditional corporate style with blue tones.

**Colors:**
- Primary: #003366 (navy)
- Secondary: #0066CC (blue)
- Accent: #FF9900 (orange)
- Background: #F5F5F5 (light gray)
- Text: #333333 (dark gray)
- Text Light: #666666 (gray)

**Typography:**
- Font Family: 'Arial', 'Calibri', sans-serif
- Title Size: 42px
- Heading Size: 32px
- Body Size: 18px
- Line Height: 1.5

**Layout:**
- Slide Size: 960px × 540px (16:9)
- Padding: 60px
- Content Width: 840px

**Style:**
- Border Radius: 4px
- Box Shadow: 0 1px 4px rgba(0,0,0,0.08)
- Transition: all 0.25s ease

---

## HTML Slide Template Structure

Each slide should be generated as a complete HTML page with this structure:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slide {number}</title>
    <style>
        /* Theme-specific styles here */
        body {
            margin: 0;
            padding: 0;
            font-family: {theme.font_family};
            background: {theme.background};
            color: {theme.text};
        }
        
        .slide {
            width: 960px;
            height: 540px;
            padding: {theme.padding};
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
        }
        
        .slide-title {
            font-size: {theme.title_size};
            font-weight: bold;
            color: {theme.primary};
            margin-bottom: 30px;
        }
        
        .slide-content {
            flex: 1;
            display: flex;
            gap: 40px;
        }
        
        .text-column {
            flex: 1;
        }
        
        .image-column {
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        ul {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        li {
            font-size: {theme.body_size};
            line-height: {theme.line_height};
            margin-bottom: 15px;
            padding-left: 30px;
            position: relative;
        }
        
        li::before {
            content: "●";
            color: {theme.accent};
            position: absolute;
            left: 0;
            font-size: 24px;
        }
        
        img {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
            border-radius: {theme.border_radius};
        }
    </style>
</head>
<body>
    <div class="slide">
        <h1 class="slide-title">{slide_title}</h1>
        <div class="slide-content">
            <div class="text-column">
                <ul>
                    {bullet_points}
                </ul>
            </div>
            {image_column_if_available}
        </div>
    </div>
</body>
</html>
```

## Layout Patterns

### 1. Title Slide
- Full-width title (centered)
- Subtitle (optional)
- No bullet points
- Optional background image

### 2. Content Slide (Text Only)
- Title at top
- Bullet points in single column
- Full-width text area

### 3. Content Slide (Text + Image)
- Title at top
- Two-column layout (50/50 or 60/40)
- Text with bullets on left
- Image on right

### 4. Image-Heavy Slide
- Small title
- Large image (80% of slide)
- Optional caption

### 5. Section Divider
- Large centered text
- Accent background
- Optional icon/graphic

## Usage Instructions for Claude

When generating HTML slides:

1. **Read the theme** specified by user (or use "Modern Professional" as default)
2. **Extract theme values** (colors, fonts, sizes) from the theme definition above
3. **Generate complete HTML** for each slide with proper styling
4. **Use semantic HTML** with proper structure
5. **Include inline CSS** for portability
6. **Reference images** by path (will be converted to embedded images later)
7. **Ensure responsive** layout within 960×540 dimensions
8. **Test accessibility** with proper contrast ratios

## Example Theme Application

For theme "Modern Professional" + slide with title "Introduction" + 3 bullets + image:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Slide 2 - Introduction</title>
    <style>
        body { margin: 0; font-family: 'Segoe UI', sans-serif; background: #FFFFFF; }
        .slide { width: 960px; height: 540px; padding: 60px; box-sizing: border-box; }
        .slide-title { font-size: 44px; font-weight: bold; color: #2C3E50; margin-bottom: 30px; }
        .slide-content { display: flex; gap: 40px; }
        .text-column { flex: 1; }
        ul { list-style: none; padding: 0; }
        li { font-size: 20px; line-height: 1.6; margin-bottom: 15px; padding-left: 30px; position: relative; }
        li::before { content: "●"; color: #E74C3C; position: absolute; left: 0; }
        .image-column { flex: 1; display: flex; align-items: center; justify-content: center; }
        img { max-width: 100%; max-height: 100%; object-fit: contain; border-radius: 8px; }
    </style>
</head>
<body>
    <div class="slide">
        <h1 class="slide-title">Introduction</h1>
        <div class="slide-content">
            <div class="text-column">
                <ul>
                    <li>First key point about the topic</li>
                    <li>Second important insight</li>
                    <li>Third critical takeaway</li>
                </ul>
            </div>
            <div class="image-column">
                <img src=".cache/images/slide_01_abc123.jpg" alt="Introduction visual">
            </div>
        </div>
    </div>
</body>
</html>
```
