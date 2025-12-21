# NotebookLM Visual Remaster Engine (Gemini 3 Pro Edition)

A powerful, strictly client-side AI tool that transforms **PDFs and Images** into high-fidelity, designer-quality PowerPoint decks. By leveraging **Google Gemini 3 Pro (Vision & Image)**, it acts as a "Universal Visual Refiner," deconstructing any input visual—be it a slide, a whiteboard photo, or a raw screenshot—into a polished, professional asset.

> **"Universal Remaster Engine"**: From messy screenshots to 4K presentation slides in seconds.

## ✨ Key Features

### 1. 📂 Universal Import (PDF & Images)
- **PDF Scanning**: Classic slide-by-slide remastering.
- **Image Batching (New)**: Drag & drop multiple `.jpg` or `.png` files directly.
  - Convert **Whiteboard Photos** into clean, digital slides.
  - Transform **Hand-drawn Sketches** into professional diagrams.
  - Polish **Rough Screenshots** into presentation-ready visuals.
  - Clean **Manga/Comics** (text removal/replacement).

### 2. 🧬 AI Forensic Analysis
- Uses **Gemini Vision** to inspect every pixel.
- Extracts the "Design DNA": Layout grids, negative space, lighting, and color palette.
- Intelligently separates **Text** (Content) from **Visuals** (Background).

### 3. 🎨 High-Fidelity "Clean Plate" Generation
- Generates new, high-resolution (4K ready) backgrounds using **Gemini Image Generation**.
- **Context-Aware**: Maintains the original composition and "intent" while upgrading the aesthetic.
- **Text Removal**: Creates guaranteed "Clean Plates" where text areas are kept as negative space for new text overlay.

### 4. ⚡ Director Mode (Individual AI Edit)
- **Granular Control**: Use the `⚡ Edit` button on any slide or image.
- **Natural Language Redesign**: Give prompts like *"Turn this whiteboard sketch into a neon cyber-punk dashboard"* or *"Make this screenshot look like a vector chart"*.
- **Text Preservation**: Even heavily altered backgrounds retain the original text data as editable PowerPoint text boxes.

### 5. 🖌️ Studio Mode (Manual Touch-up)
- **Pixel-Perfect Correction**: Built-in canvas editor for manual refinements.
- **Tools**: Brush, Eraser, Eyedropper (with magnifier loupe), and Pan/Zoom controls.
- **Text Editor**: Add, delete, move, resize, rotate, and style text directly on the canvas.
- **Layering**: Nondestructive editing on top of the original or AI-generated image.

### 6. 📦 Native PPTX Export
- Downloads a fully editable `.pptx` file.
- Unprocessed items remain as images.
- Remastered items become **Image Backgrounds + Native PowerPoint Text Boxes**.

---

## 🚀 How to Use

1. **Open the App**: Open `素晴らしき修正.html` in Chrome or Edge.
2. **Enter API Key**: Input your **Google Gemini API Key** (requires `gemini-pro-vision` access).
3. **Import Files**: 
   - Drag & drop a **PDF** file.
   - OR select multiple **Image files** (JPEG, PNG).
4. **Select & Polish**: 
   - Click images to select them for remastering.
   - Use `⚡ Edit` (Director Mode) for AI-based redesigns.
   - Use `🖌️ Studio` (Studio Mode) for manual corrections and text editing.
5. **Batch Remaster**: Click "REMASTER SELECTED".
6. **Export**: Click "DOWNLOAD PPTX" to get your finished deck.

---

## 🛠 Technical Stack

This is a **Zero-Build, Single-File React Application**.
- **Core**: React 18, Babel Standalone.
- **Styling**: Tailwind CSS (Neon/Dark Theme).
- **Engines**: `pdf.js` (PDF Rendering), `pptxgenjs` (PowerPoint Generation).
- **AI**: Google Gemini API (Direct REST Calls).

---

## 📝 Latest Updates
- **Studio Mode**: A full-featured canvas editor for manual touch-ups and text manipulation.
- **Image Import Support**: Now fully supports direct image processing alongside PDFs.
- **Selection-First Workflow**: Select specific slides/images to process instead of the whole deck.
- **Text Safety Architecture**: Enhanced text extraction logic ensures no content is lost during the "Clean Plate" generation.
