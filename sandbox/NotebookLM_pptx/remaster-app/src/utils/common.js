export const safeJsonParse = (text) => {
    try {
        const match = text.match(/\{[\s\S]*\}/);
        if (!match) return null;
        return JSON.parse(match[0]);
    } catch (e) {
        console.error("JSON Parse Error:", e);
        return null;
    }
};

export const base64ToBlobUrl = (base64, mimeType = 'image/png') => {
    try {
        const byteCharacters = atob(base64);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: mimeType });
        return URL.createObjectURL(blob);
    } catch (e) {
        console.error("Blob conversion failed:", e);
        return null;
    }
};

export const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
