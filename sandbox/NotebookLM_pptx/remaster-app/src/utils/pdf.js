import { getDocument, GlobalWorkerOptions } from 'pdfjs-dist';
// Vite handles worker URL
import pdfWorker from 'pdfjs-dist/build/pdf.worker.min.js?url';
GlobalWorkerOptions.workerSrc = pdfWorker;

import { base64ToBlobUrl } from './common';

export async function scanPdf(file, { onProgress, onLog }) {
    try {
        const reader = new FileReader();
        return new Promise((resolve, reject) => {
            reader.onload = async function () {
                try {
                    const typedarray = new Uint8Array(this.result);
                    const pdf = await getDocument(typedarray).promise;
                    const totalPages = pdf.numPages;

                    // Detect Ratio from Page 1
                    const page1 = await pdf.getPage(1);
                    const vp = page1.getViewport({ scale: 1.0 });
                    const ratioVal = vp.width / vp.height;
                    const detectedRatio = ratioVal < 1.5 ? "4:3" : "16:9";

                    if (onLog) onLog(`📐 Ratio Detected: ${detectedRatio}`);

                    const scannedSlides = [];
                    for (let i = 1; i <= totalPages; i++) {
                        if (onProgress) onProgress(i, totalPages, `Scanning Page ${i}...`);
                        try {
                            const page = await pdf.getPage(i);
                            const viewport = page.getViewport({ scale: 2.0 });
                            const canvas = document.createElement('canvas');
                            canvas.width = viewport.width;
                            canvas.height = viewport.height;
                            const ctx = canvas.getContext('2d');
                            await page.render({ canvasContext: ctx, viewport }).promise;
                            const base64 = canvas.toDataURL('image/jpeg', 0.8);
                            const blobUrl = base64ToBlobUrl(base64.split(',')[1], 'image/jpeg');

                            scannedSlides.push({
                                id: i,
                                status: 'ORIGINAL', // ORIGINAL, PROCESSING, REMASTERED, ERROR
                                isSelected: false,
                                originalImage: base64,
                                displayImage: blobUrl, // Init with original
                                bgImage: null, // Filled only if remastered
                                textData: [], // Filled only if remastered
                                bgType: 'ORIGINAL'
                            });
                        } catch (e) {
                            if (onLog) onLog(`Scan Error Page ${i}: ${e.message}`);
                        }
                    }
                    resolve({ slides: scannedSlides, ratio: detectedRatio });
                } catch (e) {
                    reject(e);
                }
            };
            reader.readAsArrayBuffer(file);
        });
    } catch (e) {
        throw e;
    }
}
