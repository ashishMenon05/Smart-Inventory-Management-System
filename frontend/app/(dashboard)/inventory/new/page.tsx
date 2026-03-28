'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  PlusCircle, 
  QrCode, 
  Printer, 
  Eye, 
  RefreshCw, 
  ArrowLeft,
  Loader2,
  CheckCircle2
} from 'lucide-react'
import Link from 'next/link'

export default function NewItemPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [previewLabel, setPreviewLabel] = useState<string | null>(null)
  const [successData, setSuccessData] = useState<{ item_id: string, label_url: string } | null>(null)

  const [formData, setFormData] = useState({
    product_name: '',
    category: '',
    supplier_name: '',
    batch_number: '',
    unit_of_measure: 'units',
    quantity: '0',
    min_stock_level: '10',
    shelf_location: '',
    entry_date: new Date().toISOString().split('T')[0],
    expiry_date: '',
    manufacture_date: '',
    unit_price: '0.00',
    notes: ''
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const resetForm = () => {
    setFormData({
      product_name: '',
      category: '',
      supplier_name: '',
      batch_number: '',
      unit_of_measure: 'units',
      quantity: '0',
      min_stock_level: '10',
      shelf_location: '',
      entry_date: new Date().toISOString().split('T')[0],
      expiry_date: '',
      manufacture_date: '',
      unit_price: '0.00',
      notes: ''
    })
    setPreviewLabel(null)
    setSuccessData(null)
  }

  const handleSubmit = async (action: 'qr' | 'print' | 'preview') => {
    setLoading(true)
    setPreviewLabel(null)
    setSuccessData(null)

    try {
      // Connect to FastAPI backend
      const response = await fetch('http://localhost:8001/items', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          quantity: parseInt(formData.quantity) || 0,
          min_stock_level: parseInt(formData.min_stock_level) || 0,
          unit_price: parseFloat(formData.unit_price) || 0.0,
          expiry_date: formData.expiry_date || null,
          manufacture_date: formData.manufacture_date || null,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to create item')
      }

      const data = await response.json()
      setSuccessData(data)

      if (action === 'qr') {
        setPreviewLabel(`http://localhost:8001${data.label_url}`)
      } else if (action === 'print') {
        // The backend already opens the viewer if print_label=True,
        // but we can also handle it on the frontend for convenience
        window.open(`http://localhost:8001${data.label_url}`, '_blank')
      } else if (action === 'preview') {
          // Just show the ID
      }

    } catch (err) {
      console.error(err)
      alert("Error connecting to backend server on port 8001. Make sure it's running.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex-1 space-y-8 p-8 pt-6 max-w-5xl mx-auto animate-fade-in">
      <div className="flex items-center gap-4">
        <Link href="/inventory">
          <Button variant="ghost" size="icon" className="h-8 w-8 text-zinc-400 hover:text-white">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Add New Item</h1>
          <p className="text-zinc-500">Register a new product in the SmartStock system.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Form */}
        <Card className="lg:col-span-2 border-zinc-800 bg-zinc-900/50 backdrop-blur-xl shadow-2xl">
          <CardHeader>
            <CardTitle className="text-xl">Product Information</CardTitle>
            <CardDescription>Enter details about the new inventory item.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-400">Product Name</label>
                <Input 
                  name="product_name" 
                  value={formData.product_name} 
                  onChange={handleChange}
                  placeholder="e.g. Paracetamol 500mg" 
                  className="bg-black/40 border-zinc-800 focus:border-emerald-500/50"
                  required
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-400">Category</label>
                <Input 
                  name="category" 
                  value={formData.category} 
                  onChange={handleChange}
                  placeholder="e.g. Medicines" 
                  className="bg-black/40 border-zinc-800"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-400">Supplier Name</label>
                <Input 
                  name="supplier_name" 
                  value={formData.supplier_name} 
                  onChange={handleChange}
                  placeholder="e.g. HealthFirst Pharma" 
                  className="bg-black/40 border-zinc-800"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-400">Batch Number</label>
                <Input 
                  name="batch_number" 
                  value={formData.batch_number} 
                  onChange={handleChange}
                  placeholder="e.g. B-2024-X1" 
                  className="bg-black/40 border-zinc-800"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-400">Quantity</label>
                <Input 
                  type="number" 
                  name="quantity" 
                  value={formData.quantity} 
                  onChange={handleChange}
                  className="bg-black/40 border-zinc-800"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-400">Min Stock</label>
                <Input 
                  type="number" 
                  name="min_stock_level" 
                  value={formData.min_stock_level} 
                  onChange={handleChange}
                  className="bg-black/40 border-zinc-800"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-400">UoM</label>
                <Input 
                   name="unit_of_measure" 
                   value={formData.unit_of_measure} 
                   onChange={handleChange}
                   placeholder="units, kg, Liters" 
                   className="bg-black/40 border-zinc-800"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-400">Unit Price</label>
                <Input 
                  type="number" 
                  step="0.01" 
                  name="unit_price" 
                  value={formData.unit_price} 
                  onChange={handleChange}
                  className="bg-black/40 border-zinc-800"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-zinc-400">Shelf Location</label>
              <Input 
                name="shelf_location" 
                value={formData.shelf_location} 
                onChange={handleChange}
                placeholder="e.g. Rack-1, Row-A, Slot-2" 
                className="bg-black/40 border-zinc-800"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-400">Entry Date</label>
                <Input 
                  type="date" 
                  name="entry_date" 
                  value={formData.entry_date} 
                  onChange={handleChange}
                  className="bg-black/40 border-zinc-800"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-400">Manufacture Date</label>
                <Input 
                  type="date" 
                  name="manufacture_date" 
                  value={formData.manufacture_date} 
                  onChange={handleChange}
                  className="bg-black/40 border-zinc-800"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-400">Expiry Date</label>
                <Input 
                  type="date" 
                  name="expiry_date" 
                  value={formData.expiry_date} 
                  onChange={handleChange}
                  className="bg-black/40 border-zinc-800"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-zinc-400">Notes</label>
              <textarea 
                name="notes"
                value={formData.notes}
                onChange={handleChange}
                className="w-full flex min-h-[80px] rounded-md border border-zinc-800 bg-black/40 px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-emerald-500/50" 
                placeholder="Additional details..."
              />
            </div>
          </CardContent>
        </Card>

        {/* Actions & Preview Sidebar */}
        <div className="space-y-6">
          <Card className="border-zinc-800 bg-zinc-900/50 backdrop-blur-xl shadow-2xl">
            <CardHeader>
              <CardTitle className="text-lg">Actions</CardTitle>
              <CardDescription>Save and process the item.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button 
                onClick={() => handleSubmit('qr')} 
                disabled={loading || !formData.product_name}
                className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-semibold flex items-center gap-2 h-11"
              >
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <QrCode className="h-4 w-4" />}
                Save and generate QR
              </Button>
              
              <Button 
                onClick={() => handleSubmit('print')}
                disabled={loading || !formData.product_name}
                variant="outline" 
                className="w-full border-zinc-700 bg-zinc-800/50 hover:bg-zinc-800 flex items-center gap-2 h-11"
              >
                <Printer className="h-4 w-4" />
                Save & print Label
              </Button>

              <Button 
                onClick={() => handleSubmit('preview')}
                disabled={loading || !formData.product_name}
                variant="outline" 
                className="w-full border-zinc-700 bg-zinc-800/50 hover:bg-zinc-800 flex items-center gap-2 h-11"
              >
                <Eye className="h-4 w-4" />
                Save and preview code
              </Button>

              <div className="pt-2">
                <Button 
                  onClick={resetForm}
                  variant="ghost" 
                  className="w-full text-zinc-500 hover:text-red-400 flex items-center gap-2 transition-colors"
                >
                  <RefreshCw className="h-4 w-4" />
                  Reset form
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Success / Preview Feedback */}
          {successData && (
             <Card className="border-emerald-500/50 bg-emerald-500/5 backdrop-blur-xl animate-fade-in">
               <CardContent className="pt-6 text-center space-y-4">
                  <div className="flex justify-center">
                    <CheckCircle2 className="h-12 w-12 text-emerald-500" />
                  </div>
                  <div>
                    <p className="text-white font-semibold">Item Created Successfully!</p>
                    <p className="text-xs font-mono text-zinc-400 mt-1">{successData.item_id}</p>
                  </div>
                  {previewLabel ? (
                    <div className="bg-white p-2 rounded-lg inline-block mx-auto border-4 border-zinc-800 overflow-hidden">
                       <img src={previewLabel} alt="QR Label Preview" className="max-w-[180px] h-auto" />
                    </div>
                  ) : null}
                  <Button 
                    variant="link" 
                    className="text-emerald-500 text-xs"
                    onClick={() => router.push('/inventory')}
                  >
                    View in Inventory
                  </Button>
               </CardContent>
             </Card>
          )}
        </div>
      </div>
    </div>
  )
}
