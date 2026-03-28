import { PrismaClient } from '../generated/client'
import { PrismaBetterSqlite3 } from '@prisma/adapter-better-sqlite3'

const connectionString = process.env.DATABASE_URL || "file:../backend/data/inventory.db"

const adapter = new PrismaBetterSqlite3({
  url: connectionString
})

const prisma = new PrismaClient({ adapter })

async function main() {
  console.log('🌱 Seeding demo data...')

  const demoItems = [
    {
      item_id: "ITEM-00001",
      qr_code_data: "ITEM-00001",
      product_name: "Paracetamol 500mg",
      category: "Medicines",
      supplier_name: "HealthFirst Pharma",
      batch_number: "MED-2024-09",
      unit_of_measure: "units",
      quantity: 48,
      min_stock_level: 20,
      shelf_location: "Rack-1, Row-A, Slot-1",
      entry_date: new Date("2024-09-15"),
      expiry_date: new Date("2026-03-31"),
      manufacture_date: new Date("2024-09-01"),
      unit_price: 2.50,
      notes: "Store below 25°C",
      status: "active"
    },
    {
      item_id: "ITEM-00002",
      qr_code_data: "ITEM-00002",
      product_name: "Amoxicillin 250mg",
      category: "Medicines",
      supplier_name: "CureMed Ltd",
      batch_number: "MED-2023-11",
      unit_of_measure: "units",
      quantity: 5,
      min_stock_level: 15,
      shelf_location: "Rack-1, Row-B, Slot-2",
      entry_date: new Date("2023-11-01"),
      expiry_date: new Date("2025-12-01"),
      manufacture_date: new Date("2023-10-15"),
      unit_price: 8.00,
      notes: "Antibiotic — prescription required",
      status: "active"
    },
    {
      item_id: "ITEM-00003",
      qr_code_data: "ITEM-00003",
      product_name: "Hand Sanitizer 500ml",
      category: "Cleaning Supplies",
      supplier_name: "PureCare Co.",
      batch_number: "CLN-2024-05",
      unit_of_measure: "units",
      quantity: 120,
      min_stock_level: 30,
      shelf_location: "Rack-4, Row-A, Slot-1",
      entry_date: new Date("2024-05-20"),
      expiry_date: new Date("2027-06-30"),
      manufacture_date: new Date("2024-05-01"),
      unit_price: 120.00,
      notes: "70% isopropyl alcohol",
      status: "active"
    },
    {
      item_id: "ITEM-00004",
      qr_code_data: "ITEM-00004",
      product_name: "Basmati Rice 1kg",
      category: "Food & Beverages",
      supplier_name: "GrainMart",
      batch_number: "FOOD-2024-08",
      unit_of_measure: "kg",
      quantity: 8,
      min_stock_level: 15,
      shelf_location: "Rack-2, Row-C, Slot-3",
      entry_date: new Date("2024-08-10"),
      expiry_date: new Date("2026-08-15"),
      manufacture_date: new Date("2024-08-01"),
      unit_price: 95.00,
      notes: "Keep dry",
      status: "active"
    },
    {
      item_id: "ITEM-00005",
      qr_code_data: "ITEM-00005",
      product_name: "USB-C Charging Cable",
      category: "Electronics",
      supplier_name: "TechZone",
      batch_number: "ELEC-2024-12",
      unit_of_measure: "units",
      quantity: 45,
      min_stock_level: 10,
      shelf_location: "Rack-5, Row-A, Slot-1",
      entry_date: new Date("2024-12-01"),
      expiry_date: null,
      manufacture_date: new Date("2024-11-15"),
      unit_price: 299.00,
      notes: "1.5m length, nylon braided",
      status: "active"
    },
    {
      item_id: "ITEM-00006",
      qr_code_data: "ITEM-00006",
      product_name: "A4 Paper Ream (500 sheets)",
      category: "Stationery",
      supplier_name: "PaperWorld",
      batch_number: "STAT-2024-07",
      unit_of_measure: "units",
      quantity: 22,
      min_stock_level: 10,
      shelf_location: "Rack-6, Row-B, Slot-1",
      entry_date: new Date("2024-07-15"),
      expiry_date: null,
      manufacture_date: null,
      unit_price: 350.00,
      notes: "75 GSM, bright white",
      status: "active"
    },
    {
      item_id: "ITEM-00007",
      qr_code_data: "ITEM-00007",
      product_name: "Vitamin C Tablets 1000mg",
      category: "Medicines",
      supplier_name: "NutraPlus",
      batch_number: "MED-2024-10",
      unit_of_measure: "units",
      quantity: 200,
      min_stock_level: 50,
      shelf_location: "Rack-1, Row-C, Slot-3",
      entry_date: new Date("2024-10-15"),
      expiry_date: new Date("2026-04-02"),
      manufacture_date: new Date("2024-09-30"),
      unit_price: 4.50,
      notes: "Effervescent tablets",
      status: "active"
    },
    {
      item_id: "ITEM-00008",
      qr_code_data: "ITEM-00008",
      product_name: "Coconut Oil 1 Liter",
      category: "Food & Beverages",
      supplier_name: "NatureFarm",
      batch_number: "FOOD-2024-09",
      unit_of_measure: "liters",
      quantity: 30,
      min_stock_level: 10,
      shelf_location: "Rack-2, Row-A, Slot-2",
      entry_date: new Date("2024-09-20"),
      expiry_date: new Date("2026-09-20"),
      manufacture_date: new Date("2024-09-01"),
      unit_price: 180.00,
      notes: "Cold-pressed, virgin",
      status: "active"
    },
    {
      item_id: "ITEM-00009",
      qr_code_data: "ITEM-00009",
      product_name: "Whiteboard Markers (Set of 4)",
      category: "Stationery",
      supplier_name: "OfficeHub",
      batch_number: "STAT-2024-03",
      unit_of_measure: "units",
      quantity: 3,
      min_stock_level: 8,
      shelf_location: "Rack-6, Row-C, Slot-2",
      entry_date: new Date("2024-03-10"),
      expiry_date: null,
      manufacture_date: null,
      unit_price: 80.00,
      notes: "Black, Blue, Red, Green",
      status: "active"
    },
    {
      item_id: "ITEM-00010",
      qr_code_data: "ITEM-00010",
      product_name: "Dettol Antiseptic 250ml",
      category: "Cleaning Supplies",
      supplier_name: "CleanCo",
      batch_number: "CLN-2023-11",
      unit_of_measure: "units",
      quantity: 15,
      min_stock_level: 10,
      shelf_location: "Rack-4, Row-B, Slot-1",
      entry_date: new Date("2023-11-20"),
      expiry_date: new Date("2025-11-30"),
      manufacture_date: new Date("2023-11-01"),
      unit_price: 95.00,
      notes: "Pine fragrance",
      status: "active"
    },
    {
      item_id: "ITEM-00011",
      qr_code_data: "ITEM-00011",
      product_name: "Thermal Printer Paper Roll",
      category: "Stationery",
      supplier_name: "PrintMart",
      batch_number: "STAT-2024-06",
      unit_of_measure: "rolls",
      quantity: 60,
      min_stock_level: 20,
      shelf_location: "Rack-6, Row-A, Slot-3",
      entry_date: new Date("2024-06-05"),
      expiry_date: null,
      manufacture_date: null,
      unit_price: 45.00,
      notes: "80mm x 50m roll",
      status: "active"
    },
    {
      item_id: "ITEM-00012",
      qr_code_data: "ITEM-00012",
      product_name: "Instant Noodles (Pack of 12)",
      category: "Food & Beverages",
      supplier_name: "QuickBite",
      batch_number: "FOOD-2024-11",
      unit_of_measure: "packets",
      quantity: 0,
      min_stock_level: 5,
      shelf_location: "Rack-3, Row-A, Slot-1",
      entry_date: new Date("2024-11-01"),
      expiry_date: new Date("2026-12-31"),
      manufacture_date: new Date("2024-10-20"),
      unit_price: 120.00,
      notes: "Masala flavour",
      status: "active"
    },
    {
      item_id: "ITEM-00013",
      qr_code_data: "ITEM-00013",
      product_name: "AA Batteries (Pack of 10)",
      category: "Electronics",
      supplier_name: "PowerMax",
      batch_number: "ELEC-2024-08",
      unit_of_measure: "units",
      quantity: 55,
      min_stock_level: 20,
      shelf_location: "Rack-5, Row-B, Slot-2",
      entry_date: new Date("2024-08-20"),
      expiry_date: new Date("2028-01-01"),
      manufacture_date: new Date("2024-08-01"),
      unit_price: 250.00,
      notes: "1.5V alkaline",
      status: "active"
    },
    {
      item_id: "ITEM-00014",
      qr_code_data: "ITEM-00014",
      product_name: "Floor Cleaner 1 Liter",
      category: "Cleaning Supplies",
      supplier_name: "ShineClean",
      batch_number: "CLN-2024-03",
      unit_of_measure: "liters",
      quantity: 4,
      min_stock_level: 8,
      shelf_location: "Rack-4, Row-C, Slot-2",
      entry_date: new Date("2024-03-15"),
      expiry_date: new Date("2026-06-30"),
      manufacture_date: new Date("2024-03-01"),
      unit_price: 85.00,
      notes: "Lavender fragrance, anti-bacterial",
      status: "active"
    },
    {
      item_id: "ITEM-00015",
      qr_code_data: "ITEM-00015",
      product_name: "Stapler + Staple Pins Set",
      category: "Stationery",
      supplier_name: "OfficeHub",
      batch_number: "STAT-2024-04",
      unit_of_measure: "units",
      quantity: 18,
      min_stock_level: 5,
      shelf_location: "Rack-6, Row-D, Slot-1",
      entry_date: new Date("2024-04-10"),
      expiry_date: null,
      manufacture_date: null,
      unit_price: 150.00,
      notes: "Includes 3 boxes of pins",
      status: "active"
    }
  ]

  for (const item of demoItems) {
    await prisma.item.upsert({
      where: { item_id: item.item_id },
      update: item,
      create: item,
    })
  }

  console.log('✅ Seeding complete: 15 items created/updated.')
}

main()
  .catch((e) => {
    console.error(e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
