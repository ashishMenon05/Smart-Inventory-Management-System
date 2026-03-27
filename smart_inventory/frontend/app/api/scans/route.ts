import { NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

// GET /api/scans
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const item_id = searchParams.get('item_id');
    const type = searchParams.get('type');
    const limitParams = searchParams.get('limit');
    
    const limit = limitParams ? parseInt(limitParams, 10) : 50;

    const whereClause: any = {};
    if (item_id) whereClause.item_id = item_id;
    if (type) whereClause.scan_type = type;

    const scans = await prisma.scanLog.findMany({
      where: whereClause,
      include: {
        item: { select: { product_name: true, qr_code_data: true } },
      },
      orderBy: { scan_timestamp: 'desc' },
      take: limit,
    });

    return NextResponse.json({ success: true, data: scans });
  } catch (error) {
    console.error('Failed to fetch scan logs:', error);
    return NextResponse.json({ success: false, error: 'Internal Server Error' }, { status: 500 });
  } finally {
    await prisma.$disconnect();
  }
}

// POST /api/scans
export async function POST(request: Request) {
  try {
    const body = await request.json();

    const newScan = await prisma.scanLog.create({
      data: {
        item_id: body.item_id,
        scan_type: body.scan_type || 'qr',
        alerts_triggered: body.alerts_triggered || null,
        scan_timestamp: new Date(),
      },
    });

    return NextResponse.json({ success: true, data: newScan }, { status: 201 });
  } catch (error) {
    console.error('Failed to log scan:', error);
    return NextResponse.json({ success: false, error: 'Bad Request' }, { status: 400 });
  } finally {
    await prisma.$disconnect();
  }
}
