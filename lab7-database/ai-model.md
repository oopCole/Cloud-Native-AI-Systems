OPENROUTER_MODEL=openrouter/free

So the app is using the openrouter/free model (OpenRouter’s free tier).

In code, the backend uses OPENROUTER_MODEL from config and falls back to:
## mistralai/mistral-7b-instruct:free 
