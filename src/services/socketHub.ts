import type { Server, Socket } from 'socket.io';

let io: Server | undefined;

export function registerSocketServer(server: Server) {
  io = server;
  io.on('connection', (socket: Socket) => {
    const userId = socket.handshake.auth.userId ?? socket.handshake.query.userId;
    if (typeof userId === 'string' && userId.length > 0) {
      socket.join(userId);
      socket.emit('tenant.joined', { userId });
    }
  });
}

export function emitToTenant(userId: string, event: string, payload: unknown) {
  io?.to(userId).emit(event, payload);
}
