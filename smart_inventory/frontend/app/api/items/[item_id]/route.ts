import { NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

// GET /api/items/[item_id]
export async function GET(request: Request, { params }: { params: { item_id: string } }) {
  try {
    const item = await prisma.item.findUnique({
      where: { item_id: params.item_id },
      include: {
        stock_movements: { orderBy: { timestamp: 'desc' }, take: 10 },
        scan_logs: { orderBy: { scan_timestamp: 'desc' }, take: 10 },
        alerts: { orderBy: { timestamp: 'desc' } },
      },
    });

    if (!item) {
      return NextResponse.json({ success: false, error: 'Item not found' }, { status: 404 });
    }

    return NextResponse.json({ success: true, data: item });
  } catch (error) {
    console.error('Failed to fetch item by ID:', error);
    return NextResponse.json({ success: false, error: 'Internal Server Error' }, { status: 500 });
  } finally {
    await prisma.$disconnect();
  }
}

// PUT /api/items/[item_id]
export async function PUT(request: Request, { params }: { params: { item_id: string } }) {
  try {
    const body = await request.json();
    
    // Convert valid date strings to Date objects if present
    if (body.expiry_date) body.expiry_date = new Date(body.expiry_date);
    if (body.manufacture_date) body.manufacture_date = new Date(body.manufacture_date);
    if (body.entry_date) body.entry_date = new Date(body.entry_date);

    // Prevent ID/QR changes to avoid strict unique constraints
    delete body.item_id;
    delete body.qr_code_data;

    const updatedItem = await prisma.item.update({
      where: { item_id: params.item_id },
      data: body,
    });

    return NextResponse.json({ success: true, data: updatedItem });
  } catch (error) {
    console.error('Failed to update item:', error);
    return NextResponse.json({ success: false, error: 'Bad Request' }, { status: 400 });
  } finally {
    await prisma.$disconnect();
  }
}

// DELETE /api/items/[item_id] (Soft Delete)
export async function DELETE(request: Request, { params }: { params: { item_id: string } }) {
  try {
    const deletedItem = await prisma.item.update({
      where: { item_id: params.item_id },
      data: { status: 'deleted' }, // Soft delete approach defined in schema
    });

    return NextResponse.json({ success: true, data: deletedItem });
  } catch (error) {
    console.error('Failed to delete item:', error);
    return NextResponse.json({ success: false, error: 'Not Found' }, { status: 404 });
  } finally {
    await prisma.$disconnect();
  }
}
