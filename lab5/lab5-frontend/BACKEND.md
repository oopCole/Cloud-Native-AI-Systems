# Lab 4 backend (for frontend integration)

The Lab 5 frontend calls the Lab 4 backend. Ensure the backend is running before using summarize features.

## Base URL

- **http://localhost:8000**

## Endpoint

- **POST /summarize**

Request body (JSON):

- `text` (string, required, non-empty)
- `max_length` (integer, optional, default 100)

Response (JSON):

- `summary` (string)
- `model` (string)
- `truncated` (boolean)

## Authentication

Send the development JWT on every request to `/summarize`:

```
Authorization: Bearer <DEV_JWT_TOKEN>
```

In this lab, the dev token is: **dev-token**

Example header:

```
Authorization: Bearer dev-token
```

Without a valid token, the backend returns **401 Unauthorized**.

## Health check

- **GET http://localhost:8000/health** (no auth required)
- Returns `{"status":"ok"}` when the backend is up.
