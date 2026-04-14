# Workspace

## Overview

pnpm workspace monorepo using TypeScript. Each package manages its own dependencies.

## Stack

- **Monorepo tool**: pnpm workspaces
- **Node.js version**: 24
- **Package manager**: pnpm
- **TypeScript version**: 5.9
- **API framework**: Express 5
- **Database**: PostgreSQL + Drizzle ORM
- **Validation**: Zod (`zod/v4`), `drizzle-zod`
- **API codegen**: Orval (from OpenAPI spec)
- **Build**: esbuild (CJS bundle)

## Artifacts

### PM Feedback Synthesizer (`artifacts/pm-feedback-synthesizer/`)
- React + Vite single-page app at `/` (preview path)
- Sends user feedback text to Claude via `/api/feedback/analyze`
- Returns structured analysis: themes, sentiment, priority levels, executive summary
- Uses `useAnalyzeFeedback` mutation hook from `@workspace/api-client-react`

### API Server (`artifacts/api-server/`)
- Express 5 backend at `/api`
- `/api/feedback/analyze` — POST endpoint calling Claude claude-sonnet-4-6 via Anthropic AI integration
- Uses `@workspace/integrations-anthropic-ai` for Claude access (Replit AI Integrations, no user API key needed)

## AI Integration
- Provider: Anthropic (via Replit AI Integrations)
- Model: claude-sonnet-4-6
- Env vars: `AI_INTEGRATIONS_ANTHROPIC_BASE_URL`, `AI_INTEGRATIONS_ANTHROPIC_API_KEY` (auto-provisioned)

## Key Commands

- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- `pnpm --filter @workspace/api-server run dev` — run API server locally

See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details.
