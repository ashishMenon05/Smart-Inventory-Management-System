import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

// GET /api/alerts
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const item_id = searchParams.get('item_id');
    const severity = searchParams.get('severity');
    const ackParam = searchParams.get('acknowledged');

    const whereClause: any = {};
    if (item_id) whereClause.item_id = item_id;
    if (severity) whereClause.severity = severity;
    if (ackParam !== null && ackParam !== '') {
      whereClause.acknowledged = ackParam === 'true';
    }

    const alerts = await prisma.alert.findMany({
      where: whereClause,
      include: {
        item: { select: { product_name: true, category: true, quantity: true, expiry_date: true } },
      },
      orderBy: { timestamp: 'desc' },
    });

    return NextResponse.json({ success: true, data: alerts });
  } catch (error) {
    console.error('Failed to fetch alerts:', error);
    return NextResponse.json({ success: false, error: 'Internal Server Error' }, { status: 500 });
  } finally {
    await prisma.$disconnect();
  }
}

// POST /api/alerts
export async function POST(request: Request) {
  try {
    const body = await request.json();

    const newAlert = await prisma.alert.create({
      data: {
        item_id: body.item_id,
        alert_type: body.alert_type,
        alert_message: body.alert_message,
        severity: body.severity,
        acknowledged: false,
      },
    });

    return NextResponse.json({ success: true, data: newAlert }, { status: 201 });
  } catch (error) {
    console.error('Failed to create alert:', error);
    return NextResponse.json({ success: false, error: 'Bad Request' }, { status: 400 });
  } finally {
    await prisma.$disconnect();
  }
}
