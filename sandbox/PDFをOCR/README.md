# PDF OCR System with Gemini API

Stateful sliding-window OCR system that processes multi-page PDFs using Gemini 3 Flash/Pro API, maintaining logical structure and outputting Markdown.

## Features

- ✅ **Stateful Processing**: Resume from any point with `progress.json`
- ✅ **Sliding Window**: 10-page batches with 1-page overlap for context continuity
- ✅ **Smart Prompting**: 3-layer prompt structure (Context + Task + Format)
- ✅ **Error Recovery**: Exponential backoff retry with detailed error logging
- ✅ **Progress Tracking**: Real-time progress bar and status updates
- ✅ **Chapter Detection**: Automatically tracks document structure
- ✅ **Quality OCR**: LaTeX math, footnotes, tables, and figures preserved

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: `pdf2image` requires `poppler-utils`:
- **Windows**: Download from [poppler releases](https://github.com/oschwartz10612/poppler-windows/releases/) and add to PATH
- **Mac**: `brew install poppler`
- **Linux**: `sudo apt-get install poppler-utils`

### 2. Setup API Key

Create `API_KEY.txt` with your Google API key:
```
Google
YOUR_API_KEY_HERE
```

Get your API key from: https://aistudio.google.com/app/apikey

## Usage

### Basic Usage

```bash
# Process a PDF file
python main.py --input document.pdf

# Resume from saved state
python main.py --resume
```

### Advanced Options

```bash
# Custom batch size
python main.py --input document.pdf --batch-size 5

# Use different model
python main.py --input document.pdf --model gemini-3-pro

# Force reconvert PDF
python main.py --input document.pdf --force

# Clean up temp files
python main.py --cleanup
```

## Configuration

Edit `config.yaml` to customize settings:

```yaml
api:
  model: "gemini-3-flash"          # Primary model
  fallback_model: "gemini-3-pro"   # For complex pages
  max_retries: 3                    # Retry attempts
  timeout: 60                       # API timeout (seconds)

processing:
  batch_size: 10                    # Pages per batch
  overlap: 1                        # Overlap pages for context
  dpi: 300                          # Image quality
  image_format: "png"               # png or jpg

output:
  markdown_file: "output.md"        # Output file
  log_dir: "logs"                   # Error logs
  temp_dir: "temp_pages"            # Temporary images
```

## How It Works

### 1. PDF Preprocessing
- Converts PDF to individual page images (PNG/JPG)
- Saves to `temp_pages/` with zero-padded filenames (P001.png, P002.png, ...)

### 2. Sliding Window Processing
- Processes 10 pages at a time (configurable)
- Includes 1 page before and after for context
- Example: To output pages 10-19, inputs pages 9-20

### 3. State Management
- Saves progress after each batch to `progress.json`
- Tracks: last processed page, last 3 lines, current chapter
- Enables resume from any point

### 4. Prompt Structure (3-Layer)
1. **Context Layer**: Editor role, formatting rules (LaTeX, footnotes, etc.)
2. **Task Layer**: Page range, continuity info, current chapter
3. **Format Layer**: Few-shot examples of ideal output

### 5. Error Handling
- Exponential backoff: 1s, 2s, 4s (max 3 retries)
- Saves state before shutdown on fatal errors
- User-friendly error messages with resume commands

## Output Format

The system outputs structured Markdown with:

- **Headings**: Proper hierarchy (#, ##, ###)
- **Math**: LaTeX format ($inline$, $$display$$)
- **Footnotes**: `[^1]` format
- **Figures**: `> [図X: 説明]`
- **Tables**: Markdown table syntax
- **Lists**: Bullets (-) or numbered (1. 2. 3.)

## Directory Structure

```
PDFをOCR/
├── main.py                 # Main orchestrator
├── ocr_engine.py          # Gemini API integration
├── pdf_processor.py       # PDF to image conversion
├── state_manager.py       # State persistence
├── error_handler.py       # Error handling & retry
├── prompts.py             # Prompt templates
├── config.yaml            # Configuration
├── requirements.txt       # Dependencies
├── API_KEY.txt           # Your API key (create this)
├── progress.json         # Runtime state (auto-generated)
├── output.md             # Final output (auto-generated)
├── temp_pages/           # Page images (auto-generated)
└── logs/                 # Error logs (auto-generated)
```

## Troubleshooting

### API Connection Failed
```bash
# Check API key
cat API_KEY.txt

# Test connection
python -c "from ocr_engine import load_api_key, OCREngine; OCREngine(load_api_key()).test_connection()"
```

### Missing Page Images
```bash
# Reconvert PDF
python main.py --input document.pdf --force
```

### Rate Limit Errors
Wait for rate limit reset, then resume:
```bash
python main.py --resume
```

### Out of Memory
Reduce batch size:
```bash
python main.py --input document.pdf --batch-size 5
```

## Examples

### Example 1: Process Academic Paper
```bash
python main.py --input paper.pdf --model gemini-3-pro
```

### Example 2: Resume After Interruption
```bash
# Start processing
python main.py --input book.pdf

# Press Ctrl+C to stop

# Resume later
python main.py --resume
```

### Example 3: Process with Custom Settings
```bash
python main.py --input document.pdf --batch-size 5 --model gemini-3-flash
```

## License

MIT License

## Credits

Built according to "実装契約書（The Contract）" specifications.
