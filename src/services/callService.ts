import type { PrismaClient } from '@prisma/client';
import { randomUUID } from 'node:crypto';
import type { WASocket } from '@whiskeysockets/baileys';
import { emitToTenant } from './socketHub.js';

export async function handleCallEvent(prisma: PrismaClient, socket: WASocket, accountId: string, userId: string, calls: any[]) {
  const account = await prisma.whatsAppAccount.findUnique({ where: { id: accountId } });
  for (const call of calls) {
    const fromJid = call.from ?? call.chatId ?? call.fromJid ?? 'unknown';
    await prisma.whatsAppCallEvent.create({
      data: { accountId, callId: call.id ?? randomUUID(), fromJid, status: call.status ?? 'unknown', isVideo: Boolean(call.isVideo), payload: call },
    });
    emitToTenant(userId, 'call.incoming', { accountId, fromJid, status: call.status, isVideo: Boolean(call.isVideo) });
    if (account?.busyAutoReply && call.status === 'offer') {
      await socket.sendMessage(fromJid, { text: account.busyAutoReply });
    }
    if (account?.autoRejectCalls && call.id && fromJid !== 'unknown') {
      await socket.rejectCall(call.id, fromJid).catch(() => undefined);
    }
  }
}
