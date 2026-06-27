import makeWASocket, { DisconnectReason, fetchLatestBaileysVersion } from '@whiskeysockets/baileys';
import type { WASocket } from '@whiskeysockets/baileys';
import type { PrismaClient } from '@prisma/client';
import P from 'pino';
import QRCode from 'qrcode';
import { usePrismaBaileysAuthState } from './baileysAuthStore.js';
import { mirrorMessage } from './messageRetentionService.js';
import { handleCallEvent } from './callService.js';
import { emitToTenant } from './socketHub.js';

export class BaileysManager {
  private clients = new Map<string, WASocket>();
  private logger = P({ level: process.env.LOG_LEVEL ?? 'info' });

  constructor(private prisma: PrismaClient) {}

  async startAccount(accountId: string) {
    const account = await this.prisma.whatsAppAccount.findUniqueOrThrow({ where: { id: accountId } });
    if (this.clients.has(accountId)) return this.clients.get(accountId)!;

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
        await this.prisma.whatsAppAccount.update({ where: { id: accountId }, data: { status: 'CONNECTED', qrCodeDataUrl: null, lastConnectedAt: new Date(), phoneNumber: socket.user?.id } });
        emitToTenant(account.userId, 'wa.connected', { accountId, phoneNumber: socket.user?.id });
      }
      if (connection === 'close') {
        this.clients.delete(accountId);
        const code = (lastDisconnect?.error as any)?.output?.statusCode;
        const loggedOut = code === DisconnectReason.loggedOut;
        await this.prisma.whatsAppAccount.update({ where: { id: accountId }, data: { status: loggedOut ? 'LOGGED_OUT' : 'RECONNECTING' } });
        emitToTenant(account.userId, 'wa.disconnected', { accountId, loggedOut });
        if (!loggedOut) setTimeout(() => void this.startAccount(accountId), 2_000);
      }
    });

    socket.ev.on('messages.upsert', async ({ messages }) => {
      for (const message of messages) {
        await mirrorMessage(this.prisma, accountId, message);
        emitToTenant(account.userId, 'message.upsert', { accountId, message });
      }
    });
    socket.ev.on('call', (calls) => void handleCallEvent(this.prisma, socket, accountId, account.userId, calls));
    return socket;
  }

  async bootstrapConnectedAccounts() {
    const accounts = await this.prisma.whatsAppAccount.findMany({ where: { status: { in: ['CONNECTED', 'RECONNECTING', 'CONNECTING', 'QR_READY'] } } });
    await Promise.allSettled(accounts.map((account) => this.startAccount(account.id)));
  }

  getClient(accountId: string) {
    return this.clients.get(accountId);
  }
}
