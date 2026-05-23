# UtilityHub SaaS — All-in-One Utility Tools Website

A complete SaaS-style platform foundation for 55+ micro-tools with FastAPI backend, Tailwind-powered frontend, dark mode, monetization placeholders, and extensible modular architecture.

## Stack
- **Backend:** FastAPI (async), Pillow, PyPDF
- **Frontend:** Jinja2 templates + Tailwind CSS + Vanilla JS modules
- **Deploy:** Docker / Docker Compose

## Architecture
```text
app/
  api/v1/endpoints/
    catalog.py            # Tool catalog API for 55 tools
    image_tools.py        # Image compression endpoint
    pdf_tools.py          # PDF merge endpoint
  services/
    catalog_service.py
    image_service.py
    pdf_service.py
  schemas/
    tool_catalog.py
    tool_responses.py
  templates/
    base.html             # SaaS shell, CTA, ads-safe blocks
    dashboard.html        # Hero, filters, plans, catalog grid
    tool.html             # Tool workspace with instant utility actions
  static/js/
    main.js
    dashboard.js
    instant-tools.js
```

## Implemented Core Features
1. **Complete SaaS Dashboard Experience**
   - Hero section, product highlights, pricing blocks, category pills, and responsive cards.
   - Search + category filtering powered by `/api/v1/tools/catalog`.

2. **55-Tool Catalog Included**
   - All requested categories and tool names are preloaded and returned by API.
   - Metadata flags for backend-supported and premium tools.

3. **Backend File Operations**
   - `POST /api/v1/images/compress`
   - `POST /api/v1/pdf/merge`

4. **Instant Tool Engine (5 ready actions)**
   - QR Code URL Generator
   - Word Counter
   - Password Generator
   - Case Converter
   - Base64 Encoder/Decoder

5. **Ads-Ready Safe Zones**
   - Top banner slots, sidebar slots, native insertion blocks, and CTA widget placeholder containers.

## Run
```bash
docker compose up --build
```
