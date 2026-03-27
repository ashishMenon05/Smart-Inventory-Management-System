import { NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

// PUT /api/alerts/[alert_id]/acknowledge
export async function PUT(request: Request, { params }: { params: { alert_id: string } }) {
  try {
    const alertIdInt = parseInt(params.alert_id, 10);
    if (isNaN(alertIdInt)) {
      return NextResponse.json({ success: false, error: 'Invalid Alert ID' }, { status: 400 });
    }

    const body = await request.json();

    const updatedAlert = await prisma.alert.update({
      where: { alert_id: alertIdInt },
      data: { acknowledged: body.acknowledged ?? true },
    });

    return NextResponse.json({ success: true, data: updatedAlert });
  } catch (error) {
    console.error('Failed to update alert:', error);
    return NextResponse.json({ success: false, error: 'Internal Server Error' }, { status: 500 });
  } finally {
    await prisma.$disconnect();
  }
}
