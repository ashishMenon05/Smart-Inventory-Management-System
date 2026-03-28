const { PrismaClient } = require('@prisma/client')
const Database = require('better-sqlite3')
const { PrismaBetterSqlite3 } = require('@prisma/adapter-better-sqlite3')

async function test() {
  try {
    const dbUrl = "file:../backend/data/inventory.db"
    const connectionString = dbUrl.replace('file:', '')
    console.log('Testing connection to:', connectionString)
    const sqlite = new Database(connectionString)
    const adapter = new PrismaBetterSqlite3(sqlite)
    const prisma = new PrismaClient({ adapter })
    
    const items = await prisma.item.findMany()
    console.log(`Success! Found ${items.length} items.`)
    await prisma.$disconnect()
  } catch (e) {
    console.error('Test failed:', e)
  }
}

test()
