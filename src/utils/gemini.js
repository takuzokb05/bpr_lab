import { safeJsonParse, base64ToBlobUrl } from './common';

export const callGemini = async (apiKey, model, data) => {
    const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`;
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!response.ok) {
            if (response.status === 503) throw new Error("503 Service Overloaded - Retrying...");
            const errText = await response.text();
            let errObj;
            try { errObj = JSON.parse(errText); } catch (e) { errObj = { error: { message: errText } }; }
            throw new Error(errObj.error?.message || `API Error ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Gemini API Call Failed:", error);
        throw error;
    }
};

export async function analyzeSlide(apiKey, modelConfig, base64Image, pageNum) {
    // Correctly extract MIME type and clean Base64
    const match = base64Image.match(/^data:(image\/[a-zA-Z+]+);base64,(.+)$/);
    const mimeType = match ? match[1] : "image/jpeg";
    const cleanData = match ? match[2] : base64Image.split(',')[1] || base64Image;

    const visionPrompt = `
    You are a Forensic Design Analyst. Your task is to deconstruct this slide image into a STRICT "Blueprint" (DNA).
    [MANDATORY ANALYSIS PROTOCOLS]
    1. SPATIAL LAYOUT & NEGATIVE SPACE: Identify grid and "VOID" (Negative Space) for text.
    2. MEDIUM DNA: "Vector Art", "3D Render", "Corporate Memphis", etc.
    3. PHYSICS: Lighting, Texture.
    4. COLOR ROLES: Background, Accent.

    Return JSON: { "design_dna": { "medium_tag": "", "composition_prompt": "", "lighting_modifier": "", "color_palette": "" }, "texts": [{ "content": "", "role": "Title|Body|Caption", "color_hex": "", "x_pct": number, "y_pct": number, "width_pct": number }] }
    `;

    try {
        const res = await callGemini(apiKey, modelConfig.vision, {
            contents: [{ parts: [{ text: visionPrompt }, { inline_data: { mime_type: mimeType, data: cleanData } }] }]
        });
        const parsed = safeJsonParse(res.candidates[0].content.parts[0].text);
        if (parsed) return parsed;
    } catch (e) {
        console.error(`Analysis failed for ${pageNum}`, e);
    }
    return { texts: [], design_dna: { medium_tag: "Corporate", composition_prompt: "", lighting_modifier: "", color_palette: "" } };
}

export async function performRemaster(apiKey, modelConfig, slide, presentationRatio, onProgress) {
    // Correctly extract MIME type and clean Base64
    const match = slide.originalImage.match(/^data:(image\/[a-zA-Z+]+);base64,(.+)$/);
    const mimeType = match ? match[1] : "image/jpeg";
    const cleanData = match ? match[2] : slide.originalImage.split(',')[1];

    // Step 1: Analysis
    if (onProgress) onProgress(`🔍 Analyzing layout & structure (Slide ${slide.id})...`);
    const analysis = await analyzeSlide(apiKey, modelConfig, slide.originalImage, slide.id);

    // Step 2: Generation Setup
    if (onProgress) onProgress(`🎨 Reconstructing background DNA...`);
    const cleanPlatePrompt = `
    [TASK] Create a professional 4K background for this slide.
    [CRITICAL] REMOVE ALL TEXT. The output must be a clean background image ready for text overlay.
    [STYLE] Modern, Premium, High Definition. DNA: ${analysis.design_dna.medium_tag}. Lighting: ${analysis.design_dna.lighting_modifier}.
    [CONSTRAINTS] Maintain original layout and Aspect Ratio (${presentationRatio}). High Fidelity, No Artifacts, Photorealistic or Vector Art (matching original style).
    `;

    // Step 3: AI Painting
    if (onProgress) onProgress(`✨ Polishing pixels & removing artifacts...`);
    const imgRes = await callGemini(apiKey, modelConfig.image, {
        contents: [{
            parts: [
                { text: cleanPlatePrompt },
                { inline_data: { mime_type: mimeType, data: cleanData } }
            ]
        }],
        generationConfig: {
            responseModalities: ["TEXT", "IMAGE"]
        }
    });

    const imgPart = imgRes.candidates?.[0]?.content?.parts?.find(p => p.inline_data || p.inlineData);
    if (!imgPart) throw new Error("Image Generation Failed");

    const data = imgPart.inline_data || imgPart.inlineData;
    const finalBgImage = `data:${data.mime_type || data.mimeType};base64,${data.data}`;
    const finalBlobUrl = base64ToBlobUrl(data.data, data.mime_type || data.mimeType);

    return {
        bgImage: finalBgImage,
        displayImage: finalBlobUrl,
        bgType: 'AI_REMASTERED',
        textData: analysis.texts || []
    };
}
