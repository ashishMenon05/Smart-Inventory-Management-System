import { prisma } from './prisma'
import { addDays, isBefore, isAfter } from 'date-fns'

export async function generateAlerts() {
  console.log('[Alert Utils] Starting generateAlerts...')
  try {
    console.log('[Alert Utils] prisma is:', typeof prisma)
    console.log('[Alert Utils] prisma.item is:', typeof (prisma as any).item)
    const items = await prisma.item.findMany({
      where: { status: 'active' }
    })
    console.log('[Alert Utils] Successfully fetched items:', items?.length)
    
    const now = new Date()
    const expiringThreshold = addDays(now, 7)
    
    for (const item of items) {
      if (item.expiry_date && isBefore(new Date(item.expiry_date), now)) {
        await createOrUpdateAlert(item.item_id, 'expired', `Item "${item.product_name}" has expired!`, 'high')
      } 
      else if (item.expiry_date && isBefore(new Date(item.expiry_date), expiringThreshold)) {
         await createOrUpdateAlert(item.item_id, 'expiring_soon', `Item "${item.product_name}" is expiring within 7 days.`, 'medium')
      }
      
      if (item.quantity <= item.min_stock_level) {
         await createOrUpdateAlert(item.item_id, 'low_stock', `Item "${item.product_name}" is low on stock (${item.quantity} remaining).`, 'warning')
      }
    }
  } catch (e: any) {
    console.error('[Alert Utils] Error generating alerts:', e)
    throw e // Re-throw to see the original stack trace
  }
}

async function createOrUpdateAlert(itemId: string, type: string, message: string, severity: string) {
  console.log(`[Alert Utils] Checking for existing alert: ${itemId} - ${type}`)
  const existing = await prisma.alert.findFirst({
    where: {
      item_id: itemId,
      alert_type: type,
      acknowledged: false
    }
  })
  
  if (!existing) {
    console.log(`[Alert Utils] Creating new alert for item ${itemId}`)
    await prisma.alert.create({
      data: {
        item_id: itemId,
        alert_type: type,
        alert_message: message,
        severity: severity,
        timestamp: new Date()
      }
    })
  }
}
