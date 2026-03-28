'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { 
  FileSpreadsheet, 
  History, 
  AlertTriangle, 
  FileText, 
  Download, 
  Eye, 
  Loader2,
  CheckCircle2,
  Table as TableIcon
} from 'lucide-react'
import { cn } from '@/lib/utils'

const API_BASE = "http://localhost:8001"

type ReportType = 'FULL' | 'MOVEMENT' | 'EXPIRY' | 'SUMMARY'

interface ReportResult {
  filename: string
  url: string
  content: string
}

export default function ReportsPage() {
  const [loading, setLoading] = useState<ReportType | null>(null)
  const [report, setReport] = useState<ReportResult | null>(null)
  const [days, setDays] = useState('30')
  const [success, setSuccess] = useState<ReportType | null>(null)

  const generateReport = async (type: ReportType) => {
    setLoading(type)
    setReport(null)
    setSuccess(null)
    
    let endpoint = ''
    switch (type) {
      case 'FULL': endpoint = '/reports/full-inventory'; break
      case 'MOVEMENT': endpoint = `/reports/stock-movement?days=${days}`; break
      case 'EXPIRY': endpoint = '/reports/expiry'; break
      case 'SUMMARY': endpoint = '/reports/summary'; break
    }

    try {
      const resp = await fetch(`${API_BASE}${endpoint}`)
      const data = await resp.json()
      if (data.status === 'success') {
        setReport(data)
        setSuccess(type)
        // Auto-clear success state after 3s
        setTimeout(() => setSuccess(null), 3000)
      } else {
        alert("Failed to generate report: " + data.detail)
      }
    } catch (err) {
      console.error(err)
      alert("Error connecting to backend server.")
    } finally {
      setLoading(null)
    }
  }

  const renderPreview = () => {
    if (!report) return null

    const isCsv = report.filename.endsWith('.csv')
    
    return (
      <Card className="mt-8 border-zinc-800 bg-zinc-900/60 backdrop-blur-md overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-500">
        <CardHeader className="flex flex-row items-center justify-between border-b border-zinc-800/50 bg-zinc-800/20 px-6 py-4">
          <div>
            <CardTitle className="text-lg font-bold flex items-center gap-2 text-zinc-100">
              <Eye className="h-4 w-4 text-blue-400" />
              Report Preview: {report.filename}
            </CardTitle>
            <CardDescription className="text-xs text-zinc-500 uppercase tracking-widest mt-1">
              {isCsv ? "Spreadsheet Data Visualization" : "Textual Analysis Summary"}
            </CardDescription>
          </div>
          <Button 
            className="gap-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-100 border-zinc-700" 
            variant="outline"
            size="sm"
            onClick={() => {
              const link = document.createElement('a')
              link.href = `${API_BASE}${report.url}`
              link.download = report.filename
              link.click()
            }}
          >
            <Download className="h-4 w-4" />
            Download Original File
          </Button>
        </CardHeader>
        <CardContent className="p-0">
          <div className="max-h-[600px] overflow-auto scrollbar-thin scrollbar-thumb-zinc-800">
            {isCsv ? (
              <table className="w-full text-left text-sm font-sans">
                <thead className="sticky top-0 bg-zinc-900 z-10">
                  <tr className="border-b border-zinc-800 shadow-sm text-zinc-400 font-bold uppercase text-[10px] tracking-wider">
                    {report.content.split('\n')[0].split(',').map((header, idx) => (
                      <th key={idx} className="px-5 py-4 whitespace-nowrap bg-zinc-900/90">{header.replace(/_/g, ' ')}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800/40">
                  {report.content.split('\n').slice(1).filter(line => line.trim()).map((line, rowIdx) => (
                    <tr key={rowIdx} className="hover:bg-blue-500/5 transition-colors duration-200">
                      {line.split(',').map((cell, cellIdx) => (
                        <td key={cellIdx} className="px-5 py-4 whitespace-nowrap text-zinc-300 text-xs font-mono">
                          {cell}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <pre className="p-8 text-xs font-mono text-zinc-300 leading-relaxed whitespace-pre bg-zinc-950/20">
                {report.content}
              </pre>
            )}
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="flex-1 space-y-10 p-8 pt-6 min-h-screen bg-zinc-950/10 dark">
      <div className="relative">
        {/* Abstract Background Elements */}
        <div className="absolute -top-10 -left-10 w-40 h-40 bg-blue-500/10 rounded-full blur-[80px] pointer-events-none" />
        <div className="absolute top-20 right-20 w-60 h-60 bg-purple-500/5 rounded-full blur-[100px] pointer-events-none" />
        
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <h1 className="text-4xl font-black tracking-tight bg-gradient-to-r from-blue-400 to-indigo-500 bg-clip-text text-transparent italic">
              ANALYTIC REPORTS
            </h1>
            <p className="text-zinc-500 max-w-lg leading-relaxed font-medium">
              Audit your inventory status, track stock velocity, and maintain record compliance with automated reporting tools.
            </p>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-zinc-900/50 rounded-full border border-zinc-800/80 backdrop-blur-sm self-start md:self-center">
            <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest pt-[1px]">Real-time Database Connection Active</span>
          </div>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {/* Full Inventory Card */}
        <Card className="group relative border-zinc-800 bg-zinc-900/40 hover:bg-zinc-900/60 transition-all duration-300 overflow-hidden hover:scale-[1.02] hover:border-zinc-700">
          <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
            <FileSpreadsheet className="h-16 w-16 text-white" />
          </div>
          <CardHeader className="pb-2">
            <div className="h-10 w-10 rounded-xl bg-blue-500/10 flex items-center justify-center mb-2">
              <FileSpreadsheet className="h-5 w-5 text-blue-400" />
            </div>
            <CardTitle className="text-lg">Full Inventory</CardTitle>
            <CardDescription className="text-xs">Complete export of active stock.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-[10px] font-mono text-zinc-600 bg-black/20 p-2 rounded uppercase tracking-tighter">
              Columns: item_id, product, category, qty, supplier, price...
            </div>
            <Button 
              className={cn(
                "w-full transition-all gap-2 h-10 font-bold tracking-wide",
                success === 'FULL' ? "bg-emerald-600 hover:bg-emerald-600" : "bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500"
              )}
              onClick={() => generateReport('FULL')}
              disabled={loading === 'FULL'}
            >
              {loading === 'FULL' ? <Loader2 className="h-4 w-4 animate-spin" /> : 
               success === 'FULL' ? <CheckCircle2 className="h-4 w-4" /> : <Download className="h-4 w-4" />}
              {success === 'FULL' ? 'Generated' : 'Generate CSV'}
            </Button>
          </CardContent>
        </Card>

        {/* Stock Movement Card */}
        <Card className="group relative border-zinc-800 bg-zinc-900/40 hover:bg-zinc-900/60 transition-all duration-300 overflow-hidden hover:scale-[1.02] hover:border-zinc-700">
          <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
            <History className="h-16 w-16 text-white" />
          </div>
          <CardHeader className="pb-2">
            <div className="h-10 w-10 rounded-xl bg-purple-500/10 flex items-center justify-center mb-2">
              <History className="h-5 w-5 text-purple-400" />
            </div>
            <CardTitle className="text-lg">Velocity Report</CardTitle>
            <CardDescription className="text-xs">Audit inbound & outbound logs.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest pl-1">Days to Lookback</label>
              <Input 
                type="number" 
                value={days} 
                onChange={(e) => setDays(e.target.value)}
                className="bg-black/20 border-zinc-800 h-8 text-xs font-mono text-blue-400 focus-visible:ring-1 focus-visible:ring-blue-500/50"
              />
            </div>
            <Button 
              className={cn(
                "w-full transition-all gap-2 h-10 font-bold tracking-wide",
                success === 'MOVEMENT' ? "bg-emerald-600 hover:bg-emerald-600" : "bg-gradient-to-r from-purple-600 to-fuchsia-600 hover:from-purple-500 hover:to-fuchsia-500"
              )}
              onClick={() => generateReport('MOVEMENT')}
              disabled={loading === 'MOVEMENT'}
            >
              {loading === 'MOVEMENT' ? <Loader2 className="h-4 w-4 animate-spin" /> : 
               success === 'MOVEMENT' ? <CheckCircle2 className="h-4 w-4" /> : <Download className="h-4 w-4" />}
              {success === 'MOVEMENT' ? 'Generated' : 'Generate CSV'}
            </Button>
          </CardContent>
        </Card>

        {/* Expiry Report Card */}
        <Card className="group relative border-zinc-800 bg-zinc-900/40 hover:bg-zinc-900/60 transition-all duration-300 overflow-hidden hover:scale-[1.02] hover:border-zinc-700">
          <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
            <AlertTriangle className="h-16 w-16 text-white" />
          </div>
          <CardHeader className="pb-2">
            <div className="h-10 w-10 rounded-xl bg-amber-500/10 flex items-center justify-center mb-2">
              <AlertTriangle className="h-5 w-5 text-amber-500" />
            </div>
            <CardTitle className="text-lg">Expiry Audit</CardTitle>
            <CardDescription className="text-xs">Critical risk assessment for items.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-[10px] font-mono text-zinc-600 bg-black/20 p-2 rounded uppercase tracking-tighter">
              Filters: expired [past-due] & expiring [within-30d] items.
            </div>
            <Button 
              className={cn(
                "w-full transition-all gap-2 h-10 font-bold tracking-wide",
                success === 'EXPIRY' ? "bg-emerald-600 hover:bg-emerald-600" : "bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500"
              )}
              onClick={() => generateReport('EXPIRY')}
              disabled={loading === 'EXPIRY'}
            >
              {loading === 'EXPIRY' ? <Loader2 className="h-4 w-4 animate-spin" /> : 
               success === 'EXPIRY' ? <CheckCircle2 className="h-4 w-4" /> : <Download className="h-4 w-4" />}
              {success === 'EXPIRY' ? 'Generated' : 'Generate CSV'}
            </Button>
          </CardContent>
        </Card>

        {/* Text Summary Card */}
        <Card className="group relative border-zinc-800 bg-zinc-900/40 hover:bg-zinc-900/60 transition-all duration-300 overflow-hidden hover:scale-[1.02] hover:border-zinc-700">
          <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
            <FileText className="h-16 w-16 text-white" />
          </div>
          <CardHeader className="pb-2">
            <div className="h-10 w-10 rounded-xl bg-emerald-500/10 flex items-center justify-center mb-2">
              <FileText className="h-5 w-5 text-emerald-500" />
            </div>
            <CardTitle className="text-lg">Executive Summary</CardTitle>
            <CardDescription className="text-xs">Human-readable system overview.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-[10px] font-mono text-zinc-600 bg-black/20 p-2 rounded uppercase tracking-tighter">
              Includes: stats, category breakdown, top-5 valuation.
            </div>
            <Button 
              className={cn(
                "w-full transition-all gap-2 h-10 font-bold tracking-wide",
                success === 'SUMMARY' ? "bg-emerald-600 hover:bg-emerald-600" : "bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500"
              )}
              onClick={() => generateReport('SUMMARY')}
              disabled={loading === 'SUMMARY'}
            >
              {loading === 'SUMMARY' ? <Loader2 className="h-4 w-4 animate-spin" /> : 
               success === 'SUMMARY' ? <CheckCircle2 className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              {success === 'SUMMARY' ? 'Generated' : 'Generate TEXT'}
            </Button>
          </CardContent>
        </Card>
      </div>

      <div className="relative">
        {renderPreview()}
        {!report && !loading && (
          <div className="mt-12 flex flex-col items-center justify-center p-20 border-2 border-dashed border-zinc-800/40 rounded-3xl bg-zinc-900/10 group cursor-default">
             <div className="h-20 w-20 rounded-full bg-zinc-800/30 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-500">
               <TableIcon className="h-8 w-8 text-zinc-600 group-hover:text-blue-500/50" />
             </div>
             <h3 className="text-lg font-bold text-zinc-400 group-hover:text-zinc-200 transition-colors">Select a Report to Preview</h3>
             <p className="text-sm text-zinc-600 text-center max-w-xs mt-2">Generate any database export above to view real-time data visualization here.</p>
          </div>
        )}
        {loading && (
           <div className="mt-12 flex flex-col items-center justify-center p-20 border-2 border-dashed border-blue-500/20 rounded-3xl bg-blue-500/5">
             <Loader2 className="h-12 w-12 text-blue-500 animate-spin mb-6" />
             <h3 className="text-lg font-bold text-blue-400">Processing Real-time Database...</h3>
             <p className="text-sm text-blue-500/60 text-center max-w-xs mt-2 italic font-mono uppercase tracking-tighter">Compiling records into document format</p>
          </div>
        )}
      </div>
      
      {/* Visual Glare effect */}
      <div className="fixed bottom-0 left-1/2 -translate-x-1/2 w-[80%] h-[1px] bg-gradient-to-r from-transparent via-blue-500/20 to-transparent pointer-events-none" />
    </div>
  )
}
