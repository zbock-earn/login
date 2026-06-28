import type { PrismaClient } from '@prisma/client';
import { randomUUID } from 'node:crypto';
import type { WASocket } from '@whiskeysockets/baileys';
import { emitToTenant } from './socketHub.js';

type CallEventPayload = {
  id?: string;
  from?: string;
  chatId?: string;
  fromJid?: string;
  status?: string;
  isVideo?: boolean;
};

function normalizeCall(value: unknown): CallEventPayload {
  const candidate = value as Partial<CallEventPayload>;
  return {
    id: typeof candidate.id === 'string' ? candidate.id : undefined,
    from: typeof candidate.from === 'string' ? candidate.from : undefined,
    chatId: typeof candidate.chatId === 'string' ? candidate.chatId : undefined,
    fromJid: typeof candidate.fromJid === 'string' ? candidate.fromJid : undefined,
    status: typeof candidate.status === 'string' ? candidate.status : undefined,
    isVideo: typeof candidate.isVideo === 'boolean' ? candidate.isVideo : false,
  };
}

export async function handleCallEvent(
  prisma: PrismaClient,
  socket: WASocket,
  accountId: string,
  userId: string,
  calls: readonly unknown[],
): Promise<void> {
  const account = await prisma.whatsAppAccount.findUnique({ where: { id: accountId } });
  for (const rawCall of calls) {
    const call = normalizeCall(rawCall);
    const fromJid = call.from ?? call.chatId ?? call.fromJid ?? 'unknown';
    const status = call.status ?? 'unknown';
    await prisma.whatsAppCallEvent.create({
      data: { accountId, callId: call.id ?? randomUUID(), fromJid, status, isVideo: Boolean(call.isVideo), payload: rawCall as never },
    });
    emitToTenant(userId, 'call.incoming', { accountId, fromJid, status, isVideo: Boolean(call.isVideo) });
    if (account?.busyAutoReply && status === 'offer' && fromJid !== 'unknown') {
      await socket.sendMessage(fromJid, { text: account.busyAutoReply });
    }
    if (account?.autoRejectCalls && status === 'offer' && call.id && fromJid !== 'unknown') {
      await socket.rejectCall(call.id, fromJid).catch(() => undefined);
    }
  }
}
