import makeWASocket, { DisconnectReason, fetchLatestBaileysVersion, type WAMessage, type WASocket } from '@whiskeysockets/baileys';
import type { PrismaClient } from '@prisma/client';
import P from 'pino';
import QRCode from 'qrcode';
import { usePrismaBaileysAuthState } from './prisma.auth.js';
import { emitToTenant } from './socketHub.js';

type ConnectionError = { output?: { statusCode?: number } };

type BaileysCallOffer = {
  id?: string;
  from?: string;
  chatId?: string;
  fromJid?: string;
  status?: string;
  isVideo?: boolean;
};

interface DeletedMessageNotice {
  accountId: string;
  waMessageId: string;
  deletedAt: string;
  badge: 'Deleted by Sender';
}

function readDisconnectCode(error: unknown): number | undefined {
  const candidate = error as ConnectionError | undefined;
  return candidate?.output?.statusCode;
}

function getMessageType(message: WAMessage): string {
  return Object.keys(message.message ?? {})[0] ?? 'unknown';
}

function getProtocolDeleteTargetId(message: WAMessage): string | undefined {
  const protocol = message.message?.protocolMessage;
  const protocolType = protocol?.type;
  const revokedId = protocol?.key?.id;
  if ((protocolType === 0 || protocolType?.toString() === 'REVOKE') && revokedId) {
    return revokedId;
  }
  return undefined;
}

function toCallOffer(value: unknown): BaileysCallOffer {
  const candidate = value as Partial<BaileysCallOffer>;
  return {
    id: typeof candidate.id === 'string' ? candidate.id : undefined,
    from: typeof candidate.from === 'string' ? candidate.from : undefined,
    chatId: typeof candidate.chatId === 'string' ? candidate.chatId : undefined,
    fromJid: typeof candidate.fromJid === 'string' ? candidate.fromJid : undefined,
    status: typeof candidate.status === 'string' ? candidate.status : undefined,
    isVideo: typeof candidate.isVideo === 'boolean' ? candidate.isVideo : false,
  };
}

export class BaileysManager {
  private readonly clients = new Map<string, WASocket>();
  private readonly logger = P({ level: process.env.LOG_LEVEL ?? 'info' });

  constructor(private readonly prisma: PrismaClient) {}

  async startAccount(accountId: string): Promise<WASocket> {
    const account = await this.prisma.whatsAppAccount.findUniqueOrThrow({ where: { id: accountId } });
    const existingClient = this.clients.get(accountId);
    if (existingClient) {
      return existingClient;
    }

    await this.prisma.whatsAppAccount.update({ where: { id: accountId }, data: { status: 'CONNECTING' } });
    const { state, saveCreds } = await usePrismaBaileysAuthState(this.prisma, accountId);
    const { version } = await fetchLatestBaileysVersion();
    const socket = makeWASocket({ auth: state, version, printQRInTerminal: false, logger: this.logger.child({ accountId }) });
    this.clients.set(accountId, socket);

    socket.ev.on('creds.update', saveCreds);
    socket.ev.on('connection.update', async ({ connection, lastDisconnect, qr }) => {
      if (qr) {
        const qrCodeDataUrl = await QRCode.toDataURL(qr);
        await this.prisma.whatsAppAccount.update({ where: { id: accountId }, data: { status: 'QR_READY', qrCodeDataUrl } });
        emitToTenant(account.userId, 'wa.qr', { accountId, qrCodeDataUrl });
      }

      if (connection === 'open') {
        await this.prisma.whatsAppAccount.update({
          where: { id: accountId },
          data: { status: 'CONNECTED', qrCodeDataUrl: null, lastConnectedAt: new Date(), phoneNumber: socket.user?.id },
        });
        emitToTenant(account.userId, 'wa.connected', { accountId, phoneNumber: socket.user?.id });
      }

      if (connection === 'close') {
        this.clients.delete(accountId);
        const loggedOut = readDisconnectCode(lastDisconnect?.error) === DisconnectReason.loggedOut;
        await this.prisma.whatsAppAccount.update({
          where: { id: accountId },
          data: { status: loggedOut ? 'LOGGED_OUT' : 'RECONNECTING' },
        });
        emitToTenant(account.userId, 'wa.disconnected', { accountId, loggedOut });
        if (!loggedOut) {
          setTimeout(() => void this.startAccount(accountId), 2_000);
        }
      }
    });

    socket.ev.on('messages.upsert', async ({ messages }) => {
      for (const message of messages) {
        const deletedMessageId = getProtocolDeleteTargetId(message);
        if (deletedMessageId) {
          await this.prisma.whatsAppMessage.updateMany({
            where: { accountId, waMessageId: deletedMessageId },
            data: { isDeletedBySender: true, deletedAt: new Date() },
          });
          const notice: DeletedMessageNotice = {
            accountId,
            waMessageId: deletedMessageId,
            deletedAt: new Date().toISOString(),
            badge: 'Deleted by Sender',
          };
          emitToTenant(account.userId, 'message.deleted_by_sender', notice);
          continue;
        }

        const waMessageId = message.key.id;
        const remoteJid = message.key.remoteJid;
        if (!waMessageId || !remoteJid) {
          continue;
        }

        const stored = await this.prisma.whatsAppMessage.upsert({
          where: { accountId_waMessageId: { accountId, waMessageId } },
          create: {
            accountId,
            waMessageId,
            remoteJid,
            participant: message.key.participant,
            fromMe: Boolean(message.key.fromMe),
            messageTimestamp: message.messageTimestamp ? BigInt(Number(message.messageTimestamp)) : undefined,
            messageType: getMessageType(message),
            pushName: message.pushName,
            payload: message as never,
          },
          update: { payload: message as never, messageType: getMessageType(message) },
        });
        emitToTenant(account.userId, 'message.upsert', { accountId, message: stored });
      }
    });

    socket.ev.on('call', (calls: readonly unknown[]) => {
      void this.handleCalls(socket, accountId, account.userId, calls);
    });

    return socket;
  }

  async bootstrapConnectedAccounts(): Promise<void> {
    const accounts = await this.prisma.whatsAppAccount.findMany({
      where: { status: { in: ['CONNECTED', 'RECONNECTING', 'CONNECTING', 'QR_READY'] } },
    });
    await Promise.allSettled(accounts.map((account) => this.startAccount(account.id)));
  }

  getClient(accountId: string): WASocket | undefined {
    return this.clients.get(accountId);
  }

  private async handleCalls(socket: WASocket, accountId: string, userId: string, calls: readonly unknown[]): Promise<void> {
    const account = await this.prisma.whatsAppAccount.findUnique({ where: { id: accountId } });
    for (const rawCall of calls) {
      const call = toCallOffer(rawCall);
      const fromJid = call.from ?? call.chatId ?? call.fromJid ?? 'unknown';
      const status = call.status ?? 'unknown';
      await this.prisma.whatsAppCallEvent.create({
        data: {
          accountId,
          callId: call.id ?? `${accountId}-${Date.now()}`,
          fromJid,
          status,
          isVideo: Boolean(call.isVideo),
          payload: rawCall as never,
        },
      });

      emitToTenant(userId, 'call.incoming', { accountId, fromJid, status, isVideo: Boolean(call.isVideo) });

      if (status === 'offer' && account?.busyAutoReply && fromJid !== 'unknown') {
        await socket.sendMessage(fromJid, { text: account.busyAutoReply });
      }

      if (status === 'offer' && account?.autoRejectCalls && call.id && fromJid !== 'unknown') {
        await socket.rejectCall(call.id, fromJid).catch(() => undefined);
      }
    }
  }
}
