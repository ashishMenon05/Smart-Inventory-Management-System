import { NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

// GET /api/items  (List all items, optional query params ?category=, ?status=, ?search=)
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const category = searchParams.get('category');
    const status = searchParams.get('status') || 'active';
    const search = searchParams.get('search');

    const whereClause: any = { status };
    if (category && category !== 'All Categories') {
      whereClause.category = category;
    }
    if (search) {
      whereClause.OR = [
        { product_name: { contains: search } },
        { item_id: { contains: search } },
        { supplier_name: { contains: search } },
      ];
    }

    const items = await prisma.item.findMany({
      where: whereClause,
      orderBy: { created_at: 'desc' },
    });

    return NextResponse.json({ success: true, data: items });
  } catch (error) {
    console.error('Failed to fetch items:', error);
    return NextResponse.json(
      { success: false, error: 'Internal Server Error' },
      { status: 500 }
    );
  } finally {
    await prisma.$disconnect();
  }
}

// POST /api/items  (Create a new item)
export async function POST(request: Request) {
  try {
    const body = await request.json();

    const newItem = await prisma.item.create({
      data: {
        item_id: body.item_id,
        qr_code_data: body.qr_code_data || body.item_id,
        product_name: body.product_name,
        category: body.category,
        supplier_name: body.supplier_name,
        batch_number: body.batch_number,
        unit_of_measure: body.unit_of_measure,
        quantity: body.quantity || 0,
        min_stock_level: body.min_stock_level || 10,
        shelf_location: body.shelf_location,
        entry_date: new Date(body.entry_date || new Date()),
        expiry_date: body.expiry_date ? new Date(body.expiry_date) : null,
        manufacture_date: body.manufacture_date ? new Date(body.manufacture_date) : null,
        unit_price: body.unit_price,
        notes: body.notes,
        status: 'active',
      },
    });

    return NextResponse.json({ success: true, data: newItem }, { status: 201 });
  } catch (error) {
    console.error('Failed to create item:', error);
    return NextResponse.json(
      { success: false, error: 'Bad Request or Internal Server Error' },
      { status: 400 }
    );
  } finally {
    await prisma.$disconnect();
  }
}
