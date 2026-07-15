# 🚨 BREAKING: Someone just made OpenAI's Whisper transcribe 2.5 hours of audio in ...

- URL: https://x.com/hasantoxr/status/2037612803532656952
- ソース: x
- 言語: en
- テーマ: ai-news
- 取得日: 2026-03-29
- いいね: 550 / RT: 66 / リプライ: 20
- 投稿者: @hasantoxr / フォロワー 431,646

## 投稿内容

🚨 BREAKING: Someone just made OpenAI's Whisper transcribe 2.5 hours of audio in 98 seconds. 100% OPEN SOURCE.

It runs entirely on your GPU. No API keys. No cloud. No subscription.

It's called Insanely Fast Whisper.

You drop in an audio file. One command. You come back and there's a clean, timestamped transcript waiting. Not a rough draft. Not a partial output. The entire thing. Done.

Not a wrapper.
Not a web app.

A CLI that turns your local machine into a transcription engine that makes paid services look embarrassing.

Here's what it does on its own:
→ Transcribes 150 minutes of audio in under 98 seconds using Flash Attention 2, same model, 19x faster, zero quality loss
→ Auto-detects language across dozens of languages, or translates directly into English with a single flag
→ Speaker diarization built in, knows who said what, not just what was said
→ Word-level and chunk-level timestamps so you can jump to any exact moment in any recording
→ Runs on NVIDIA GPUs and Apple Silicon Macs with zero code changes between them
→ Works on Google Colab free tier if you don't own a GPU at all

Here's how fast it actually is:

Standard Whisper large-v3 out of the box: 31 minutes to process 2.5 hours of audio. The same exact model with Flash Attention 2 and batching: 1 minute 38 seconds. Same weights. Same accuracy. One flag difference.

Here's the wildest part:
This never started as a product. It was a benchmark demo to show what Hugging Face Transformers could do. Then the community started using it for real work. Podcast transcription. Legal recordings. Research interviews. Meeting notes at scale. The team kept adding what people actually needed until a benchmark became a full CLI that nobody planned to build.

8.8K GitHub stars. 100% Open Source.

## 要約

（要約は次回 /curate 時に追記）
