# Interactive Feedback Loop Feature

## Overview

The Voice-to-Slide application now supports **AI-powered feedback loop**, allowing users to provide natural language feedback to edit the presentation structure before final generation.

## New Pipeline Flow

```
Audio → Transcription → Structure Analysis → [Feedback Loop] → HTML Generation → Rendering → PPTX
                                              ↑ NEW STEP ↑
```

Instead of manually editing JSON files, you can now:
- **Give feedback in natural language**: "Change slide 2 title to 'Market Overview'"
- **AI edits for you**: Claude understands and updates the structure
- **See updates instantly**: View the updated structure after each edit
- **Iterate freely**: Keep refining until satisfied
- **Type `/start`**: Begin slide generation when ready

## What's New

### New Module: `structure_editor.py`

An AI-powered structure editor using Claude Messages API:

- **Natural language editing**: Understand user feedback like "add a slide about pricing"
- **Smart structure updates**: Claude modifies the JSON structure correctly
- **Validation**: Ensures output is valid and maintains required fields
- **Context-aware**: Understands references like "slide 2", "the introduction", etc.

### Updated Modules

#### `presentation_orchestrator.py`
- Added `allow_feedback_loop()` method for AI-powered editing workflow
- Added `format_structure_preview()` to display structure
- Updated `generate_presentation()` to accept pre-generated structure
- Automatically updates image queries based on edited structure

#### `main.py`
- Added `--interactive` flag to enable feedback loop mode
- Implements feedback collection and structure display callbacks
- Detects `/start` command to exit loop and begin generation

## How to Use

### Basic Usage

Enable interactive mode with the `--interactive` flag:

```bash
uv run voice-to-slide generate recording.mp3 --interactive
```

### With Other Options

Combine interactive mode with themes and other options:

```bash
# With a specific theme
uv run voice-to-slide generate audio.mp3 --theme "Dark Mode" --interactive

# Without images
uv run voice-to-slide generate audio.mp3 --no-images --interactive

# With custom output path
uv run voice-to-slide generate audio.mp3 --output slides.pptx --interactive
```

## Interactive Workflow

When `--interactive` is enabled, the following happens:

1. **Structure Generated**: Claude analyzes the transcription and creates a structure
2. **Preview Shown**: User sees the complete structure preview
3. **Feedback Loop Begins**: System enters interactive mode
   - User sees prompt: `📝 Feedback (or /start to begin):`

4. **User Provides Feedback** (repeat as needed):
   - Type natural language feedback (e.g., "change title of slide 3 to 'Revenue Growth'")
   - AI processes feedback and updates structure
   - Updated structure is displayed automatically
   - Loop continues until user types `/start`

5. **Type `/start`**: When ready to generate slides
   - Exits feedback loop
   - Shows final structure
   - Proceeds to HTML generation

6. **Continue Pipeline**: Generation continues with final edited structure

## Feedback Examples

You can provide feedback in natural language. Here are some examples:

### Editing Titles

```
📝 Feedback: Change the presentation title to "Q4 Marketing Strategy"
📝 Feedback: Rename slide 2 to "Market Overview"
📝 Feedback: Update the title of the introduction slide
```

### Editing Bullet Points

```
📝 Feedback: Add a bullet point to slide 3: "Increase social media engagement by 25%"
📝 Feedback: Remove the second point from slide 4
📝 Feedback: Change the first bullet in slide 2 to "Target audience: millennials"
```

### Adding/Removing Slides

```
📝 Feedback: Add a new slide about pricing strategy after slide 5
📝 Feedback: Remove slide 4
📝 Feedback: Insert a slide about competitor analysis before the conclusion
```

### Changing Image Themes

```
📝 Feedback: Change the image for slide 2 to "data visualization charts"
📝 Feedback: Use "team collaboration" as the image theme for the introduction
```

### Complex Edits

```
📝 Feedback: Split slide 3 into two slides - one for challenges and one for solutions
📝 Feedback: Reorder the slides: move slide 4 to be slide 2
📝 Feedback: Make the presentation more focused on technical details
```

## Error Handling

If the AI cannot understand or process your feedback:

- You'll see an error message
- The structure remains unchanged
- You can try rephrasing your feedback
- The feedback loop continues - just try again

## Use Cases

### When to Use Interactive Mode

1. **Refine AI output**: Claude's structure is good but needs tweaks
2. **Add domain knowledge**: Insert specific technical terms or details
3. **Reorder content**: Restructure the flow of slides
4. **Remove sensitive info**: Delete slides or points that shouldn't be included
5. **Add missing points**: Include important items Claude missed

### When NOT to Use Interactive Mode

1. **Quick generation**: When the AI-generated structure is sufficient
2. **Batch processing**: When automating multiple presentations
3. **Prototyping**: When you just want to see what the AI produces

## Benefits

- ✅ **Natural Language**: No need to edit JSON or learn syntax
- ✅ **AI-Powered**: Claude understands context and intent
- ✅ **Instant Feedback**: See changes immediately after each edit
- ✅ **Iterative**: Refine as many times as needed
- ✅ **No Re-analysis**: Uses existing structure, saves API costs
- ✅ **Safe**: AI validates all changes automatically
- ✅ **Cost-Optimized**: Prompt caching saves 72%+ on multi-turn editing
- ✅ **Fast**: Cache hits reduce latency and API load

## Technical Details

### How It Works

1. **User provides feedback** in natural language
2. **Sent to Claude** along with current structure
3. **Claude edits the structure** based on feedback
4. **Updated structure returned** and validated
5. **Changes displayed** to user immediately
6. **Loop continues** until user types `/start`

### AI Model

- Uses the same Claude model as structure generation (default: `claude-haiku-4-5-20251001`)
- Can be customized via `CONTENT_MODEL` environment variable
- Understands context, references, and complex editing instructions

### Prompt Caching Optimization

The feedback loop uses **Anthropic Prompt Caching** for massive cost savings:

- **Instructions cached**: Editor instructions (500+ tokens) cached across all feedbacks
- **Structure cached**: Current structure JSON cached and reused until edited
- **Only feedback is fresh**: Each new feedback is small (usually <100 tokens)

**Cost Breakdown:**
- First feedback: ~1.25x cost to create cache
- Subsequent feedbacks: **90% cheaper** (0.1x for cache reads)
- Cache TTL: 5 minutes (perfect for editing sessions)

**Example savings** (5-slide structure, 5 feedbacks):
- Without caching: ~5 × 2000 tokens = 10,000 input tokens
- With caching: 2000 + (4 × 200) = 2,800 input tokens (**72% savings**)

### Image Query Updates

When you edit the structure:

- Image queries are automatically extracted from `image_theme` fields
- If you add/remove slides, the image fetching adapts accordingly
- Empty or missing `image_theme` fields are skipped
- No manual URL updating needed - AI handles everything

## Example Session

```
🎙️  Voice-to-Slide Generator
==================================================
Audio file: recording.mp3

📝 Step 1: Transcribing audio...
   Transcribed 5234 characters

🧠 Step 2: Analyzing content and generating structure...
======================================================================
PRESENTATION STRUCTURE
======================================================================

Title: Product Launch Strategy
Total Slides: 5 (including title slide)

----------------------------------------------------------------------

Slide 2: Market Analysis
  Image: market research
  Points:
    • Current market size: $2.5B
    • Growth rate: 15% annually
    • Key competitors identified

Slide 3: Product Features
  Image: product design
  Points:
    • AI-powered analytics
    • Real-time collaboration
    • Cloud-based infrastructure

...

======================================================================

💬 FEEDBACK MODE
==================================================
You can now provide feedback to edit the structure.
Type your feedback and press Enter.
Type '/start' when ready to generate slides.
==================================================

📝 Feedback (or /start to begin): Change the title to "Q4 Product Launch Strategy"

✨ Structure updated!
======================================================================
PRESENTATION STRUCTURE
======================================================================

Title: Q4 Product Launch Strategy
Total Slides: 5 (including title slide)
...
======================================================================

📝 Feedback (or /start to begin): Add a slide about pricing after the features slide

✨ Structure updated!
======================================================================
PRESENTATION STRUCTURE
======================================================================

Title: Q4 Product Launch Strategy
Total Slides: 6 (including title slide)

...

Slide 4: Pricing Strategy
  Image: pricing tiers
  Points:
    • Three-tier pricing model
    • Competitive positioning
    • Special launch discount

...

======================================================================

📝 Feedback (or /start to begin): /start

======================================================================
✅ FINAL STRUCTURE - Ready to generate slides!
======================================================================

🎨 Step 4: Generating presentation (Strategy B: HTML → Images → PPTX)...
   • Theme: Modern Professional
   • Using edited structure from feedback loop
   • Generating HTML slides with Claude Messages API
   • Rendering HTML to high-quality images (Playwright)
   • Fetching images from Unsplash
   • Creating PPTX with rendered slides

✅ Success! Presentation generated:
   📄 File: output/recording.pptx
   🎨 Theme: Modern Professional
   📊 Total slides: 6
   🖼️  Images: 5/5
```

## Migration Notes

This feature is **opt-in** and backward compatible:

- Default behavior unchanged (no `--interactive` flag = no editing)
- Existing scripts and automation continue to work
- No breaking changes to API or file formats

## Future Enhancements

Potential improvements:

- [ ] Show diff between original and edited structure
- [ ] Undo last feedback (revert to previous version)
- [ ] Save/load structure templates
- [ ] Multi-turn conversation history for context
- [ ] Suggest improvements based on presentation best practices
- [ ] Voice input for feedback (speech-to-text)
- [ ] Web UI for visual editing

## Support

If you encounter issues:

1. Try rephrasing your feedback in simpler terms
2. Be specific about which slide or element to modify
3. Use slide numbers for clarity (e.g., "slide 3" instead of "the third one")
4. Check the logs for detailed error messages
5. Report bugs via GitHub issues with example feedback that failed
