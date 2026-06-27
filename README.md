# Multi-Tenant WhatsApp SaaS Dashboard Backend

Production-oriented TypeScript scaffold for a multi-tenant WhatsApp dashboard using Express, Socket.io, Prisma/PostgreSQL, Baileys, and FFmpeg.

## Highlights

- Tenant-isolated WhatsApp accounts keyed by `userId` and `accountId`.
- Custom Prisma-backed Baileys auth store for `creds` and Signal `keys`; no production filesystem auth.
- Startup bootstrap for previously connected/reconnecting sessions.
- Socket.io tenant rooms (`userId`) for QR, connection, message, and call streams.
- Anti-delete message mirror: `protocolMessage.type === 0` marks `isDeletedBySender` while preserving payload.
- `/api/voice/transform?voiceProfile=...` transforms uploads to WhatsApp-friendly OGG/Opus using 11 native FFmpeg profiles.
- Incoming call logging and optional busy auto-reply / reject behavior.

## API

All `/api` routes require `x-user-id` for tenant routing.

- `GET /api/sessions`
- `POST /api/sessions` body: `{ "label": "Store Support" }`
- `POST /api/sessions/:accountId/connect`
- `GET /api/accounts/:accountId/messages?jid=...&take=100`
- `POST /api/voice/transform?voiceProfile=girl` multipart field: `audio`

## Dashboard rendering contract

Messages returned by the API include `isDeletedBySender`. The WhatsApp clone UI should render the original payload normally and add a visible badge when this flag is true, for example:

```tsx
{message.isDeletedBySender && <span className="deleted-badge">Deleted by Sender</span>}
<MessageBubble payload={message.payload} />
```

## Voice sending with Baileys

After receiving a transformed file path from `transformVoice`, send it with a connected account socket:

```ts
await socket.sendMessage(jid, {
  audio: { url: outputPath },
  mimetype: 'audio/mp4',
  ptt: true,
});
```
