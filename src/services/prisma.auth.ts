import {
  BufferJSON,
  initAuthCreds,
  proto,
  type AuthenticationCreds,
  type SignalDataTypeMap,
  type SignalKeyStore,
} from '@whiskeysockets/baileys';
import type { PrismaClient } from '@prisma/client';

type JsonRecord = Record<string, unknown>;
type SerializedSignalKeyBucket = Record<string, Record<string, unknown>>;
type SignalSetPayload = Partial<{ [T in keyof SignalDataTypeMap]: Partial<Record<string, SignalDataTypeMap[T] | null>> }>;

export interface PrismaBaileysAuthState {
  state: {
    creds: AuthenticationCreds;
    keys: SignalKeyStore;
  };
  saveCreds: () => Promise<void>;
}

function toJson(value: unknown): JsonRecord {
  return JSON.parse(JSON.stringify(value, BufferJSON.replacer)) as JsonRecord;
}

function fromJson<TValue>(value: unknown): TValue {
  return JSON.parse(JSON.stringify(value), BufferJSON.reviver) as TValue;
}

function hydrateSignalValue<T extends keyof SignalDataTypeMap>(type: T, value: unknown): SignalDataTypeMap[T] {
  if (type === 'app-state-sync-key') {
    return proto.Message.AppStateSyncKeyData.fromObject(value as Record<string, unknown>) as SignalDataTypeMap[T];
  }
  return value as SignalDataTypeMap[T];
}

async function readKeyBucket(prisma: PrismaClient, accountId: string): Promise<SerializedSignalKeyBucket> {
  const row = await prisma.baileysAuthState.findUniqueOrThrow({ where: { accountId } });
  return fromJson<SerializedSignalKeyBucket>(row.keys ?? {});
}

export async function usePrismaBaileysAuthState(prisma: PrismaClient, accountId: string): Promise<PrismaBaileysAuthState> {
  const row = await prisma.baileysAuthState.upsert({
    where: { accountId },
    create: { accountId, creds: toJson(initAuthCreds()), keys: {} },
    update: {},
  });

  const creds = fromJson<AuthenticationCreds>(row.creds);
  const keys: SignalKeyStore = {
    get: async <T extends keyof SignalDataTypeMap>(type: T, ids: string[]): Promise<Record<string, SignalDataTypeMap[T]>> => {
      const bucket = await readKeyBucket(prisma, accountId);
      const typedBucket = bucket[String(type)] ?? {};
      return ids.reduce<Record<string, SignalDataTypeMap[T]>>((accumulator, id) => {
        const serializedValue = typedBucket[id];
        if (serializedValue !== undefined) {
          accumulator[id] = hydrateSignalValue(type, serializedValue);
        }
        return accumulator;
      }, {});
    },
    set: async (payload: SignalSetPayload): Promise<void> => {
      await prisma.$transaction(async (tx) => {
        const current = await tx.baileysAuthState.findUniqueOrThrow({ where: { accountId } });
        const bucket = fromJson<SerializedSignalKeyBucket>(current.keys ?? {});

        for (const [type, entries] of Object.entries(payload)) {
          bucket[type] = bucket[type] ?? {};
          for (const [id, value] of Object.entries(entries ?? {})) {
            if (value === null || value === undefined) {
              delete bucket[type][id];
            } else {
              bucket[type][id] = toJson(value);
            }
          }
        }

        await tx.baileysAuthState.update({
          where: { accountId },
          data: { keys: toJson(bucket), version: { increment: 1 } },
        });
      });
    },
  };

  const state = { creds, keys };
  const saveCreds = async (): Promise<void> => {
    await prisma.baileysAuthState.update({
      where: { accountId },
      data: { creds: toJson(state.creds), version: { increment: 1 } },
    });
  };

  return { state, saveCreds };
}
