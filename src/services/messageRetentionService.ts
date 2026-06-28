import type { PrismaClient } from '@prisma/client';
import type { WAMessage } from '@whiskeysockets/baileys';

function messageType(message: WAMessage) {
  return Object.keys(message.message ?? {})[0] ?? 'unknown';
}

export async function mirrorMessage(prisma: PrismaClient, accountId: string, message: WAMessage) {
  const waMessageId = message.key.id;
  const remoteJid = message.key.remoteJid;
  if (!waMessageId || !remoteJid) return undefined;

  const protocol = message.message?.protocolMessage;
  const deletedKey = protocol?.key;
  if (protocol?.type === 0 && deletedKey?.id) {
    return prisma.whatsAppMessage.updateMany({
      where: { accountId, waMessageId: deletedKey.id },
      data: { isDeletedBySender: true, deletedAt: new Date() },
    });
  }

  return prisma.whatsAppMessage.upsert({
    where: { accountId_waMessageId: { accountId, waMessageId } },
    create: {
      accountId,
      waMessageId,
      remoteJid,
      participant: message.key.participant,
      fromMe: Boolean(message.key.fromMe),
      messageTimestamp: message.messageTimestamp ? BigInt(Number(message.messageTimestamp)) : undefined,
      messageType: messageType(message),
      pushName: message.pushName,
      payload: message as never,
    },
    update: {
      payload: message as never,
      messageType: messageType(message),
    },
  });
}
