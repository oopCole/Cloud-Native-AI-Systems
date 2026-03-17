# Frontend Lab | Summarization UI

## Objective
Build a minimal frontend that calls the FastAPI summarization backend.

This is a completion-style workflow.
This is NOT a chat application.

## Tech Stack
- Next.js (App Router)
- Vercel AI SDK
- useCompletion (required)

## Hard Constraints
1. Use useCompletion. Do NOT use useChat.
2. The browser must call a Next.js route handler.
3. The route handler must call the FastAPI backend.
4. The FastAPI backend must NOT be called directly from the browser.
5. Non-streaming only.
6. JWT authentication must be added in the route handler.

## Backend Contract
POST /summarize
Request JSON:
{
    "text": "string (required, non-empty)",
    "max_length": 100
}
Response JSON:
{
    "summary": "string",
    "model": "string",
    "truncated": boolean
}

## Allowed Files
- app/page.tsx
- app/api/summarize/route.ts
- lib/* (optional)

## Explicitly Disallowed
- useChat
- Chat message history
- Direct browser calls to FastAPI
- Streaming responses
- Exposing JWT tokens to client-side code

## Acceptance Checks
- Submitting text produces a summary.
- Empty input is rejected client-side.
- Backend errors are surfaced in the UI.
- JWT token is only used in server-side code.

## Step 2 Constraints

- Use the Vercel AI SDK useCompletion hook.
- Do NOT use useChat.
- Do NOT call the FastAPI backend yet.
- The completion endpoint may be a placeholder.
- Modify app/page.tsx only.
- The UI must show a loading state while a request is in progress.
- Errors must be displayed in the UI.

## Step 3 Constraints
- Create a Next.js route handler at: app/api/summarize/route.ts
- The browser must call /api/summarize (NOT the FastAPI backend directly).
- The route handler must call: POST ${BACKEND_BASE_URL}/summarize
- The route handler must include header:
    Authorization: Bearer ${DEV_JWT_TOKEN}
- The route handler must forward JSON:
    { "text": "...", "max_length": 100 }
- The route handler must return plain text to the client (summary only).
- Update app/page.tsx to call /api/summarize via useCompletion.
- Do NOT implement chat. Do NOT use useChat.