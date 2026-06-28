import type { Request, Response } from 'express';
import { prisma } from '../lib/prisma.js';
import type { BaileysManager } from '../services/baileysManager.js';

export function sessionController(manager: BaileysManager) {
  return {
    create: async (req: Request, res: Response) => {
      const account = await prisma.whatsAppAccount.create({ data: { userId: req.userId!, label: req.body.label ?? 'Business WhatsApp' } });
      void manager.startAccount(account.id);
      res.status(201).json(account);
    },
    connect: async (req: Request, res: Response) => {
      const account = await prisma.whatsAppAccount.findFirstOrThrow({ where: { id: req.params.accountId, userId: req.userId! } });
      await manager.startAccount(account.id);
      res.json({ ok: true, accountId: account.id });
    },
    list: async (req: Request, res: Response) => {
      res.json(await prisma.whatsAppAccount.findMany({ where: { userId: req.userId! }, orderBy: { createdAt: 'desc' } }));
    },
  };
}
