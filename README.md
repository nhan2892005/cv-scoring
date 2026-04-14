# CV Evaluation — Next.js

AI-powered CV screening app rebuilt in Next.js 14 (App Router).

## Stack

- **Next.js 14** — App Router, Server Components, API Routes
- **Anthropic SDK** — Claude Sonnet 4.6 with streaming
- **pdf-parse + mammoth** — server-side CV parsing
- **Server-Sent Events** — real-time progress streaming to client

## Architecture

```
app/
├── api/analyze/route.ts   ← POST endpoint (SSE stream)
├── page.tsx               ← "use client" UI
├── layout.tsx
└── globals.css

lib/
├── ai-engine.ts           ← Claude calls (3-stage pipeline)
├── prompts.ts             ← JD / CV / Evaluation prompts
├── cv-parser.ts           ← PDF / DOCX / TXT extraction
└── types.ts               ← TypeScript interfaces
```

## Setup

```bash
cp .env.local.example .env.local
# Edit .env.local and add your ANTHROPIC_API_KEY

npm install
npm run dev
```

Open http://localhost:3000

## Environment variables

| Variable | Required | Default |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ | — |
| `CV_SCORING_MODEL` | optional | `claude-sonnet-4-6` |

## Deploy to Vercel

```bash
vercel
# Set ANTHROPIC_API_KEY in Vercel environment variables
```

> Note: Set `maxDuration = 120` in `app/api/analyze/route.ts` requires Vercel Pro.
> For Hobby tier, reduce to 60s or consider chunking the pipeline into 3 separate endpoints.
