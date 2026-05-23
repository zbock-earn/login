# All-in-One Utility Tools Website (FastAPI + Tailwind + Vanilla JS)

## Project Structure

```text
.
├── app/
│   ├── api/v1/endpoints/        # Async REST endpoints
│   ├── services/                # Business logic (image/pdf)
│   ├── schemas/                 # Pydantic schemas
│   ├── static/js/               # Vanilla JS modules (dashboard + instant tools)
│   ├── templates/               # Jinja2 templates (dashboard + tool boilerplate)
│   └── main.py                  # FastAPI app entrypoint
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── tests/
```

## Core Implemented
- Responsive dashboard with dark mode, search, and 55 category tool cards.
- Tool page boilerplate with ad-safe placeholders.
- Async backend endpoints:
  - `POST /api/v1/images/compress`
  - `POST /api/v1/pdf/merge`
- Instant JS tools (5): QR URL generator, word counter, password generator, case converter, base64 encode/decode.

## Run
```bash
docker compose up --build
```
