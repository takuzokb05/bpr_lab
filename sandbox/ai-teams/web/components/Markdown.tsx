"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/**
 * 発言・議事録の Markdown 描画ラッパ。
 * 各ペルソナ(特に Opus 4.8)が多用する ## 見出し / --- / 箇条書き / **強調** / 表 /
 * > 引用 / コードブロックを、UIUX 正典(報道番組系の静かな上質さ)に沿って描く。
 *
 * 安全性: rehype-raw は使わない。生 HTML を無効化したまま(XSS 安全を維持)。
 * 装飾は @theme トークン(--color-ink / ink-muted / surface / line / accent /
 * accent-weak)のみを使い、ハードコード色を避ける。サイズは text-sm 基調。
 */
export function Markdown({ children }: { children: string }) {
  return (
    <div className="text-sm leading-relaxed text-[var(--color-ink)] [overflow-wrap:anywhere]">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // 見出しは明朝(font-display)を控えめなサイズで。巨大見出しにはしない。
          h1: ({ children }) => (
            <h1 className="font-display mt-4 mb-1.5 text-base font-medium leading-snug first:mt-0">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="font-display mt-4 mb-1.5 text-base font-medium leading-snug first:mt-0">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="font-display mt-3 mb-1 text-sm font-medium leading-snug first:mt-0">
              {children}
            </h3>
          ),
          h4: ({ children }) => (
            <h4 className="font-display mt-3 mb-1 text-sm font-medium leading-snug first:mt-0">
              {children}
            </h4>
          ),
          h5: ({ children }) => (
            <h5 className="mt-2 mb-1 text-sm font-medium leading-snug first:mt-0">
              {children}
            </h5>
          ),
          h6: ({ children }) => (
            <h6 className="mt-2 mb-1 text-sm font-medium leading-snug first:mt-0 text-[var(--color-ink-muted)]">
              {children}
            </h6>
          ),
          p: ({ children }) => (
            <p className="my-2 text-sm leading-relaxed first:mt-0 last:mb-0">
              {children}
            </p>
          ),
          // リスト記号付き(現在 "- " が生で出る問題を解消)・適切な字下げ
          ul: ({ children }) => (
            <ul className="my-2 list-disc pl-5 first:mt-0 last:mb-0 marker:text-[var(--color-ink-muted)]">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="my-2 list-decimal pl-5 first:mt-0 last:mb-0 marker:text-[var(--color-ink-muted)]">
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className="my-0.5 text-sm leading-relaxed">{children}</li>
          ),
          strong: ({ children }) => (
            <strong className="font-medium">{children}</strong>
          ),
          em: ({ children }) => <em className="italic">{children}</em>,
          del: ({ children }) => (
            <del className="text-[var(--color-ink-muted)]">{children}</del>
          ),
          // 引用は左に 2px の accent 罫 + 補助色。派手にしない。
          blockquote: ({ children }) => (
            <blockquote className="my-2 border-l-2 border-[var(--color-accent)] pl-3 text-[var(--color-ink-muted)]">
              {children}
            </blockquote>
          ),
          // --- を上品な細い区切りに
          hr: () => (
            <hr className="my-4 border-0 border-t border-[var(--color-line)]" />
          ),
          a: ({ children, href }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[var(--color-accent)] underline decoration-[var(--color-line)] underline-offset-2 hover:decoration-[var(--color-accent)]"
            >
              {children}
            </a>
          ),
          // インライン/ブロックのコードを描き分ける。
          // react-markdown v9 では code に inline フラグが渡らないため、
          // ブロックの装飾(背景/角丸/スクロール)は pre 側に寄せ、inline は className 無の code で判定する。
          code: ({ className, children, ...props }) => {
            const isBlock = /language-/.test(className ?? "");
            if (isBlock) {
              return (
                <code
                  className={`${className ?? ""} font-mono text-[13px] leading-relaxed`}
                  {...props}
                >
                  {children}
                </code>
              );
            }
            return (
              <code
                className="rounded bg-[var(--color-surface)] px-1 py-0.5 font-mono text-[0.85em] text-[var(--color-ink)] ring-1 ring-[var(--color-line)]"
                {...props}
              >
                {children}
              </code>
            );
          },
          pre: ({ children }) => (
            <pre className="my-2 overflow-x-auto rounded-md border border-[var(--color-line)] bg-[var(--color-surface)] p-3 text-[13px] leading-relaxed">
              {children}
            </pre>
          ),
          // 表は細罫のみ。重い装飾は禁止。
          table: ({ children }) => (
            <div className="my-2 overflow-x-auto">
              <table className="w-full border-collapse text-sm">{children}</table>
            </div>
          ),
          thead: ({ children }) => <thead>{children}</thead>,
          tbody: ({ children }) => <tbody>{children}</tbody>,
          tr: ({ children }) => (
            <tr className="border-b border-[var(--color-line)]">{children}</tr>
          ),
          th: ({ children }) => (
            <th className="border border-[var(--color-line)] px-2.5 py-1.5 text-left font-medium text-[var(--color-ink-muted)]">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="border border-[var(--color-line)] px-2.5 py-1.5 align-top">
              {children}
            </td>
          ),
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
