import { BufferJSON, initAuthCreds, proto, type AuthenticationCreds, type SignalDataTypeMap, type SignalKeyStoreWithTransaction } from '@whiskeysockets/baileys';
import type { PrismaClient } from '@prisma/client';

type KeyBucket = Record<string, Record<string, unknown>>;

function serialize(data: unknown) {
  return JSON.parse(JSON.stringify(data, BufferJSON.replacer));
}

function deserialize<T>(data: unknown): T {
  return JSON.parse(JSON.stringify(data), BufferJSON.reviver) as T;
}

export async function usePrismaBaileysAuthState(prisma: PrismaClient, accountId: string) {
  const row = await prisma.baileysAuthState.upsert({
    where: { accountId },
    create: { accountId, creds: serialize(initAuthCreds()), keys: {} },
    update: {},
  });

  const state = {
    creds: deserialize<AuthenticationCreds>(row.creds),
    keys: {
      get: async <T extends keyof SignalDataTypeMap>(type: T, ids: string[]) => {
        const latest = await prisma.baileysAuthState.findUniqueOrThrow({ where: { accountId } });
        const keyBucket = deserialize<KeyBucket>(latest.keys) ?? {};
        const values: { [id: string]: SignalDataTypeMap[T] } = {};
        for (const id of ids) {
          const value = keyBucket[type]?.[id];
          if (value) {
            values[id] = type === 'app-state-sync-key'
              ? proto.Message.AppStateSyncKeyData.fromObject(value as never) as SignalDataTypeMap[T]
              : value as SignalDataTypeMap[T];
          }
        }
        return values;
      },
      set: async (data) => {
        const latest = await prisma.baileysAuthState.findUniqueOrThrow({ where: { accountId } });
        const keyBucket = deserialize<KeyBucket>(latest.keys) ?? {};
        for (const [type, entries] of Object.entries(data)) {
          keyBucket[type] ??= {};
          for (const [id, value] of Object.entries(entries ?? {})) {
            if (value) keyBucket[type][id] = serialize(value);
            else delete keyBucket[type][id];
          }
        }
        await prisma.baileysAuthState.update({ where: { accountId }, data: { keys: serialize(keyBucket), version: { increment: 1 } } });
      },
    } satisfies SignalKeyStoreWithTransaction,
  };

  const saveCreds = async () => {
    await prisma.baileysAuthState.update({
      where: { accountId },
      data: { creds: serialize(state.creds), version: { increment: 1 } },
    });
  };

  return { state, saveCreds };
}
