import { PrismaClient } from '@prisma/client'
import Database from 'better-sqlite3'
import { PrismaBetterSqlite3 } from '@prisma/adapter-better-sqlite3'

const connectionString = (process.env.DATABASE_URL || "file:../backend/data/inventory.db").replace('file:', '')
const sqlite = new Database(connectionString)
// @ts-ignore: Prisma 7 type mismatch for better-sqlite3 adapter
const adapter = new PrismaBetterSqlite3(sqlite)

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined
}

export const prisma = globalForPrisma.prisma ?? new PrismaClient({ adapter })

if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma
