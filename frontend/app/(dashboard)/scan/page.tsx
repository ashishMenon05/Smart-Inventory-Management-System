'use client'

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Scan, Focus, AlertTriangle, ShieldCheck, Zap, Wifi } from 'lucide-react'
import { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button'

export default function ScanPage() {
  const [isScanning, setIsScanning] = useState(true)
  const [isConnected, setIsConnected] = useState(false)
  const [detectedItems, setDetectedItems] = useState<any[]>([])
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Real-time WebSocket connection to Python AI backend
  useEffect(() => {
    const connect = () => {
      if (wsRef.current?.readyState === WebSocket.OPEN || wsRef.current?.readyState === WebSocket.CONNECTING) {
        return; // Already connecting or connected
      }

      try {
        console.log('Attempting to connect to AI Vision Backend...');
        const ws = new WebSocket('ws://127.0.0.1:8001/ws/scan');
        wsRef.current = ws;
        
        ws.onopen = () => {
          console.log('Successfully connected to AI Vision Backend at 127.0.0.1:8001');
          setIsConnected(true);
          if (reconnectTimerRef.current) {
            clearTimeout(reconnectTimerRef.current);
            reconnectTimerRef.current = null;
          }
        };

        ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            if (message.type === 'SCAN_UPDATE') {
              setDetectedItems(message.data);
            } else if (message.type === 'CONNECTED') {
              console.log('Backend confirmation:', message.server);
            }
          } catch (jsonErr) {
            console.error('Failed to parse WebSocket message:', jsonErr);
          }
        };

        ws.onclose = (event) => {
          console.log('WebSocket connection closed:', event.code, event.reason);
          setIsConnected(false);
          wsRef.current = null;
          
          // Try to reconnect in 3 seconds
          if (isScanning && !reconnectTimerRef.current) {
            reconnectTimerRef.current = setTimeout(() => {
              reconnectTimerRef.current = null;
              if (isScanning) connect();
            }, 3000);
          }
        };

        ws.onerror = (err) => {
          // Only log error if we are not actively closing the connection ourselves
          if (ws.readyState !== WebSocket.CLOSING && ws.readyState !== WebSocket.CLOSED) {
             console.error('WebSocket encountered an error');
          }
        };
      } catch (e) {
        console.error('Failed to initialize WebSocket:', e);
      }
    };

    if (isScanning) {
      connect();
    }

    return () => {
      if (wsRef.current) {
        console.log('Cleaning up WebSocket connection...');
        wsRef.current.onclose = null; 
        wsRef.current.onerror = null;
        wsRef.current.close();
        wsRef.current = null;
      }
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
    };
  }, [isScanning]);

  const mainItem = detectedItems.length > 0 ? detectedItems[0] : null;

  return (
    <div className="flex-1 space-y-8 p-8 pt-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AI Edge Scanner</h1>
          <p className="text-zinc-500 dark:text-zinc-400 font-sans">
            Real-time YOLOv8 multi-QR detection via connected Python backend.
          </p>
        </div>
        <div className="flex items-center gap-3">
           <Badge variant={isConnected ? "success" : "error"} className="gap-1.5 px-2.5 py-1">
              <Wifi className={`h-3.5 w-3.5 ${isConnected ? "animate-pulse" : ""}`} />
              {isConnected ? "Backend Live" : "Backend Offline"}
           </Badge>
           <Button variant={isScanning ? "primary" : "outline"} onClick={() => { setIsScanning(!isScanning); if(isScanning) setDetectedItems([]); }}>
             {isScanning ? "Stop Scanner" : "Start Scanner"}
           </Button>
        </div>
      </div>

      <div className="grid gap-8 lg:grid-cols-5">
        {/* Camera Feed */}
        <Card className="lg:col-span-3 relative overflow-hidden border-zinc-800 bg-black aspect-video flex items-center justify-center group">
            {isScanning && isConnected ? (
                /* Real MJPEG Stream from Python Backend */
                <img 
                    src="http://127.0.0.1:8001/video_feed" 
                    alt="AI Vision Feed" 
                    className="w-full h-full object-cover"
                />
            ) : (
                <div className="flex flex-col items-center gap-4 text-zinc-700">
                    <Focus className="h-16 w-16" />
                    <p className="text-sm font-medium uppercase tracking-widest">
                        {!isScanning ? "Scanner Disabled" : "Waiting for backend..."}
                    </p>
                </div>
            )}
            
            {/* HUD Overlay */}
            {isScanning && isConnected && (
              <div className="absolute inset-0 pointer-events-none p-6">
                 <div className="flex justify-between items-start">
                    <div className="bg-black/40 backdrop-blur-md border border-white/10 rounded-lg p-2 flex flex-col gap-1 text-[10px] font-mono text-white/50">
                        <div className="flex justify-between gap-4"><span>RESOL:</span><span>640x480</span></div>
                        <div className="flex justify-between gap-4"><span>ENGINE:</span><span className="text-emerald-400">YOLOv8n</span></div>
                    </div>
                 </div>
              </div>
            )}
        </Card>

        {/* Global Detections Sidebar */}
        <div className="lg:col-span-2 space-y-6">
           <Card className="border-zinc-800 bg-zinc-900/50 backdrop-blur-xl h-full flex flex-col">
              <CardHeader className="flex-none">
                 <CardTitle className="text-lg flex items-center gap-2">
                    <Zap className="h-4 w-4 text-yellow-500" />
                    Active Detections ({detectedItems.length})
                 </CardTitle>
                 <CardDescription>Live mapped telemetry from current frame.</CardDescription>
              </CardHeader>
              <CardContent className="flex-1 overflow-auto">
                 {detectedItems.length > 0 ? (
                    <div className="space-y-4">
                       {detectedItems.map((item, idx) => (
                          <div key={idx} className="p-4 rounded-xl border border-zinc-800 bg-zinc-950/80 hover:bg-zinc-950 transition-colors group">
                             <div className="flex items-start justify-between mb-3">
                                <div>
                                   <h3 className="font-bold text-white group-hover:text-emerald-400 transition-colors uppercase tracking-tight">{item.product_name}</h3>
                                   <p className="text-[10px] uppercase font-mono text-zinc-600">{item.item_id}</p>
                                </div>
                                <Badge className={item.alerts.length > 0 ? "bg-red-500/20 text-red-500 border-red-500/30" : "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"}>
                                   {item.alerts.length > 0 ? "Alert Active" : "Healthy"}
                                </Badge>
                             </div>
                             
                             {item.alerts.length > 0 && (
                                <div className="space-y-1.5">
                                   {item.alerts.map((al: any, aIdx: number) => (
                                      <div key={aIdx} className="flex items-center gap-2 text-xs text-red-400 bg-red-400/5 p-2 rounded-md border border-red-400/10">
                                         <AlertTriangle className="h-3 w-3" />
                                         {al.alert_type.replace('_', ' ')}: {al.alert_message}
                                      </div>
                                   ))}
                                </div>
                             )}
                          </div>
                       ))}
                    </div>
                 ) : (
                    <div className="flex flex-col items-center justify-center h-full py-12 text-center opacity-40">
                       <Scan className="h-12 w-12 mb-4 animate-pulse" />
                       <p className="text-zinc-500 text-sm font-sans max-w-[200px]">Waiting for camera input markers...</p>
                    </div>
                 )}
              </CardContent>
           </Card>
        </div>
      </div>
    </div>
  )
}
