import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const distDir = path.join(__dirname, 'dist');
const indexPath = path.join(distDir, 'index.html');
const outputPath = path.join(distDir, 'CompleteApp.html');

console.log(`Processing: ${indexPath}`);

try {
    let html = fs.readFileSync(indexPath, 'utf-8');

    // Regex definitions
    // We use replace with callback to handle replacements safely in one go for each type

    // 1. Inline JS
    // Pattern: <script type="module" ... src="..."> ... </script>
    html = html.replace(/<script type="module"[^>]+src="([^"]+)"[^>]*><\/script>/g, (match, src) => {
        console.log(`Found JS: ${src}`);
        const filePath = path.join(distDir, src.replace(/^\.\//, ''));
        if (fs.existsSync(filePath)) {
            const content = fs.readFileSync(filePath, 'utf-8');
            console.log(`-> Inlined JS (${content.length} bytes)`);
            return `<script type="module">\n${content}\n</script>`;
        }
        console.warn(`-> Not found: ${filePath}`);
        return match;
    });

    // 2. Inline CSS
    // Pattern: <link ... href="..." ... rel="stylesheet"> or <link ... rel="stylesheet" ... href="...">
    html = html.replace(/<link[^>]+href="([^"]+)"[^>]*rel="stylesheet"[^>]*>|<link[^>]+rel="stylesheet"[^>]*href="([^"]+)"[^>]*>/g, (match, p1, p2) => {
        const href = p1 || p2;
        console.log(`Found CSS: ${href}`);
        const filePath = path.join(distDir, href.replace(/^\.\//, ''));
        if (fs.existsSync(filePath)) {
            const content = fs.readFileSync(filePath, 'utf-8');
            console.log(`-> Inlined CSS (${content.length} bytes)`);
            return `<style>\n${content}\n</style>`;
        }
        console.warn(`-> Not found: ${filePath}`);
        return match;
    });

    fs.writeFileSync(outputPath, html);
    console.log(`\nDONE! Created: ${outputPath}`);

} catch (e) {
    console.error("Fatal Error:", e);
}
