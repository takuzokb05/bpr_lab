import PptxGenJS from 'pptxgenjs';

const comesFromOriginal = (s) => s.status === 'ORIGINAL' || !s.bgImage;

export const generatePptx = (slides, presentationRatio) => {
    const pptx = new PptxGenJS();
    pptx.layout = presentationRatio === "4:3" ? 'LAYOUT_4x3' : 'LAYOUT_16x9';

    slides.forEach(slide => {
        const s = pptx.addSlide();

        // Logic: If ORIGINAL, just the image. If REMASTERED, clean plate + text.
        const isOriginal = slide.status === 'ORIGINAL' || !slide.bgImage;
        const bgSource = comesFromOriginal(slide) ? slide.originalImage : slide.bgImage;

        s.addImage({ data: bgSource, x: 0, y: 0, w: '100%', h: '100%', sizing: { type: 'contain', w: '100%', h: '100%' } });

        if (!isOriginal && slide.textData) {
            slide.textData.forEach(t => {
                const isTitle = t.role === 'Title';
                const fontSize = isTitle ? 32 : 14;
                const isBold = isTitle;
                s.addText(t.content, {
                    x: `${t.x_pct}%`, y: `${t.y_pct}%`, w: `${t.width_pct}%`, h: 1,
                    fontSize: fontSize, color: t.color_hex ? t.color_hex.replace('#', '') : '363636', bold: isBold,
                    fill: { color: 'FFFFFF', transparency: 100 } // Transparent background for text
                });
            });
        }
    });
    pptx.writeFile({ fileName: `Remastered_Select_${Date.now()}.pptx` });
};
