import { NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export async function GET() {
  try {
    // We use Prisma aggregations here to do everything efficiently in the DB layer
    const totalItems = await prisma.item.count({
      where: { status: 'active' },
    });

    // Count distinct categories
    // Prisma SQLite doesn't directly support count(distinct) out of the box easily, 
    // so we group by category and count the groups
    const categories = await prisma.item.groupBy({
      by: ['category'],
      where: { status: 'active' },
    });
    const totalCategories = categories.length;

    // Items with low stock (we need raw items mapped, but for stats we join or fetch)
    // Since min_stock_level is an Int column, we can do a quick JS filter if it's small, 
    // but a raw query or fetching items where quantity <= min_stock_level is better.
    // In SQLite, filtering where fieldA <= fieldB requires a raw query:
    const lowStockRaw = await prisma.$queryRaw`
      SELECT count(*) as count FROM Item 
      WHERE status = 'active' AND quantity <= min_stock_level
    `;
    const lowStockCount = Number((lowStockRaw as any)[0].count);

    // Expired items
    const now = new Date();
    const expiredItems = await prisma.item.count({
      where: {
        status: 'active',
        expiry_date: {
          lt: now,
        },
      },
    });

    // Expiring soon (within 7 days)
    const sevenDaysFromNow = new Date();
    sevenDaysFromNow.setDate(now.getDate() + 7);

    const expiringSoonCount = await prisma.item.count({
      where: {
        status: 'active',
        expiry_date: {
          gte: now,
          lte: sevenDaysFromNow,
        },
      },
    });

    // Unread Alerts
    const unreadAlerts = await prisma.alert.count({
      where: {
        acknowledged: false,
      },
    });

    return NextResponse.json({
      success: true,
      data: {
        total_items: totalItems,
        total_categories: totalCategories,
        low_stock_count: lowStockCount,
        expired_count: expiredItems,
        expiring_soon_count: expiringSoonCount,
        unread_alerts: unreadAlerts,
      },
    });
  } catch (error) {
    console.error('Failed to fetch dashboard stats:', error);
    return NextResponse.json(
      { success: false, error: 'Internal Server Error' },
      { status: 500 }
    );
  } finally {
    await prisma.$disconnect();
  }
}
