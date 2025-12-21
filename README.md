# NotebookLM Remaster App

A powerful tool to remaster slide images using Google Gemini 3 Pro Vision & Image models. Refactored from a single HTML file to a modern React + Vite application.

## Features

-   **PDF & Image Import**: Scan slides from local PDF files or images.
-   **AI Analysis**: Uses Gemini 1.5 Pro (Vision) to analyze slide layout and design DNA.
-   **AI Remastering**: Generates high-definition, text-free backgrounds using Gemini 1.5 Pro (Image).
-   **Studio Mode**: Real-time canvas editor for manual touch-ups using brush/eraser and AI redesigns.
-   **PPTX Export**: Export remastered slides back to PowerPoint format.

## Setup

1.  **Install Dependencies**:
    ```bash
    npm install
    ```

2.  **Environment Variables** (Optional):
    You can create a `.env` file, but the app primarily uses the API Key input in the UI (persisted to localStorage).

3.  **Run Development Server**:
    ```bash
    npm run dev
    ```

4.  **Build for Production**:
    ```bash
    npm run build
    ```
    The output will be in the `dist` folder.

## tech Stack

-   **Frontend**: React, Vite
-   **Styling**: Tailwind CSS
-   **PDF Handling**: PDF.js
-   **PPTX Generation**: PptxGenJS
-   **AI**: Google Gemini API

## Notes

-   **PDF.js Worker**: Configured to load independently via Vite to ensure broad compatibility.
-   **WASM**: Enabled in Vite config for optimal PDF parsing performance.
