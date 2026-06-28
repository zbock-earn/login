# WhatsApp Web-Style SaaS Dashboard Feature Plan

This frontend is designed as a WhatsApp Web-like operator console wrapped in SaaS account management.

## Core WhatsApp Web parity

1. **Left account rail**: tenant profile, connected WhatsApp accounts, create account, reconnect, QR status, and active account switching.
2. **Conversation list**: searchable chat rows, last-message previews, unread/deleted indicators, pinned-style visual priority, and live updates from Socket.io.
3. **Chat workspace**: WhatsApp-like message bubbles, timestamps, outgoing/incoming alignment, deleted-by-sender badge while keeping retained content visible, and empty states.
4. **Composer**: text input, emoji/action buttons, attachment action affordances, push-to-talk voice transform controls, and send-state indicators.
5. **Right details panel**: contact identity, retention status, media/category summaries, call automation configuration hints, and session diagnostics.
6. **Real-time streams**: QR events, connection lifecycle events, message upserts, anti-delete alerts, and incoming call alerts are displayed in the UI.
7. **Voice studio**: 11 server-side FFmpeg profiles with upload, transform, optional dispatch through connected account, and audio preview/download.
8. **SaaS controls**: tenant id setup, account labels, plan/status cards, and multi-account switching.

## Backend endpoints consumed

- `GET /api/sessions`
- `POST /api/sessions`
- `POST /api/sessions/:accountId/connect`
- `GET /api/accounts/:accountId/messages?take=200`
- `POST /api/voice/transform?voiceProfile=...`

All requests include `x-user-id` from the dashboard tenant switcher.
