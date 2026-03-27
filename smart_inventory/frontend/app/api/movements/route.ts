import { NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

// GET /api/movements
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const item_id = searchParams.get('item_id');
    const type = searchParams.get('type');
    const daysStr = searchParams.get('days');

    const whereClause: any = {};
    if (item_id) whereClause.item_id = item_id;
    if (type) whereClause.movement_type = type;

    if (daysStr) {
      const days = parseInt(daysStr, 10);
      const pastDate = new Date();
      pastDate.setDate(pastDate.getDate() - days);
      whereClause.timestamp = { gte: pastDate };
    }

    const movements = await prisma.stockMovement.findMany({
      where: whereClause,
      include: {
        item: { select: { product_name: true, category: true } },
      },
      orderBy: { timestamp: 'desc' },
      take: 100, // Limit results
    });

    return NextResponse.json({ success: true, data: movements });
  } catch (error) {
    console.error('Failed to fetch movements:', error);
    return NextResponse.json({ success: false, error: 'Internal Server Error' }, { status: 500 });
  } finally {
    await prisma.$disconnect();
  }
}

// POST /api/movements
export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { item_id, movement_type, quantity_change, previous_quantity, new_quantity, reason, performed_by } = body;

    if (!item_id || !movement_type || typeof new_quantity !== 'number') {
      return NextResponse.json({ success: false, error: 'Missing required fields' }, { status: 400 });
    }

    // Interactive Transaction to save movement and update quantity synchronously
    const result = await prisma.$transaction(async (tx) => {
      // 1. Log the stock movement
      const movement = await tx.stockMovement.create({
        data: {
          item_id,
          movement_type,
          quantity_change,
          previous_quantity,
          new_quantity,
          reason,
          performed_by: performed_by || 'System',
        },
      });

      // 2. Update the parent Item quantity
      await tx.item.update({
        where: { item_id },
        data: { quantity: new_quantity },
      });

      return movement;
    });

    return NextResponse.json({ success: true, data: result }, { status: 201 });
  } catch (error) {
    console.error('Failed to record stock movement:', error);
    return NextResponse.json({ success: false, error: 'Internal Server Error' }, { status: 500 });
  } finally {
    await prisma.$disconnect();
  }
}
