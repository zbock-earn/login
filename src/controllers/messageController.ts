import type { Request, Response } from 'express';
import { prisma } from '../lib/prisma.js';

export async function listMessages(req: Request, res: Response) {
  const account = await prisma.whatsAppAccount.findFirstOrThrow({ where: { id: req.params.accountId, userId: req.userId! } });
  const messages = await prisma.whatsAppMessage.findMany({
    where: { accountId: account.id, remoteJid: req.query.jid as string | undefined },
    orderBy: { createdAt: 'desc' },
    take: Math.min(Number(req.query.take ?? 100), 500),
  });
  res.json(messages);
}
