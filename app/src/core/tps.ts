/**
 * Verdis TPS Tracker & Real-time WebSocket Server
 * 
 * Tracks transactions per second, block timing, and pushes
 * live updates to connected WebSocket clients.
 */

import { Server as HttpServer } from 'http';
import { WebSocketServer, WebSocket } from 'ws';

export interface NetworkStats {
  tps: number;
  blockTime: number;
  avgBlockTime: number;
  totalTxs: number;
  txsLastMinute: number;
  peakTPS: number;
  uptime: number;
  lastBlockTime: number;
}

export class TPSTracker {
  private blockTimestamps: number[] = [];
  private txTimestamps: number[] = [];
  private peakTPS: number = 0;
  private startTime: number;
  private wsServer: WebSocketServer | null = null;
  private clients: Set<WebSocket> = new Set();
  private currentStats: NetworkStats;

  constructor() {
    this.startTime = Date.now();
    this.currentStats = {
      tps: 0,
      blockTime: 5000,
      avgBlockTime: 5000,
      totalTxs: 0,
      txsLastMinute: 0,
      peakTPS: 0,
      uptime: 0,
      lastBlockTime: Date.now(),
    };
  }

  /**
   * Record a new block and its transactions
   */
  recordBlock(txCount: number): void {
    const now = Date.now();
    this.blockTimestamps.push(now);
    
    // Record each transaction timestamp
    for (let i = 0; i < txCount; i++) {
      this.txTimestamps.push(now);
    }
    
    // Calculate block time
    if (this.blockTimestamps.length >= 2) {
      const last = this.blockTimestamps[this.blockTimestamps.length - 1];
      const prev = this.blockTimestamps[this.blockTimestamps.length - 2];
      this.currentStats.blockTime = last - prev;
    }
    
    // Calculate average block time (last 20 blocks)
    if (this.blockTimestamps.length >= 2) {
      const recent = this.blockTimestamps.slice(-20);
      let totalTime = 0;
      for (let i = 1; i < recent.length; i++) {
        totalTime += recent[i] - recent[i - 1];
      }
      this.currentStats.avgBlockTime = totalTime / (recent.length - 1);
    }
    
    this.currentStats.totalTxs += txCount;
    this.currentStats.lastBlockTime = now;
    
    // Calculate TPS (transactions in last 10 seconds / 10)
    this.updateTPS();
    
    // Broadcast update to WebSocket clients
    this.broadcast({
      type: 'block',
      tps: this.currentStats.tps,
      blockTime: this.currentStats.blockTime,
      avgBlockTime: this.currentStats.avgBlockTime,
      totalTxs: this.currentStats.totalTxs,
      txCount,
      timestamp: now,
    });
  }

  recordTransaction(): void {
    const now = Date.now();
    this.txTimestamps.push(now);
    this.updateTPS();
  }

  private updateTPS(): void {
    const now = Date.now();
    const windowMs = 10000; // 10 second window
    const cutoff = now - windowMs;
    
    // Filter to last 10 seconds
    this.txTimestamps = this.txTimestamps.filter(t => t > cutoff);
    
    // TPS = transactions in window / window seconds
    this.currentStats.tps = this.txTimestamps.length / (windowMs / 1000);
    
    // Track peak
    if (this.currentStats.tps > this.peakTPS) {
      this.peakTPS = this.currentStats.tps;
      this.currentStats.peakTPS = this.peakTPS;
    }
    
    // Tx in last minute
    const minuteCutoff = now - 60000;
    this.currentStats.txsLastMinute = this.txTimestamps.filter(t => t > minuteCutoff).length;
    
    // Uptime
    this.currentStats.uptime = Math.floor((now - this.startTime) / 1000);
  }

  getStats(): NetworkStats {
    this.updateTPS();
    return { ...this.currentStats };
  }

  /**
   * Attach WebSocket server to an HTTP server
   */
  attachWebSocket(server: HttpServer): void {
    this.wsServer = new WebSocketServer({ server, path: '/ws' });
    
    this.wsServer.on('connection', (ws: WebSocket, req: any) => {
      this.clients.add(ws);
      console.log(`🔌 WebSocket client connected (total: ${this.clients.size})`);
      
      // Send initial stats
      ws.send(JSON.stringify({
        type: 'connected',
        stats: this.getStats(),
        timestamp: Date.now(),
      }));
      
      ws.on('message', (data: any) => {
        try {
          const msg = JSON.parse(data.toString());
          if (msg.type === 'subscribe') {
            // Already subscribed by default
          }
          if (msg.type === 'ping') {
            ws.send(JSON.stringify({ type: 'pong', timestamp: Date.now() }));
          }
        } catch (e) {
          // Ignore malformed messages
        }
      });
      
      ws.on('close', () => {
        this.clients.delete(ws);
        console.log(`🔌 WebSocket client disconnected (total: ${this.clients.size})`);
      });
      
      ws.on('error', () => {
        this.clients.delete(ws);
      });
    });
    
    // Broadcast stats every 5 seconds
    setInterval(() => {
      this.broadcast({
        type: 'stats',
        stats: this.getStats(),
        timestamp: Date.now(),
      });
    }, 5000);
  }

  private broadcast(data: any): void {
    const msg = JSON.stringify(data);
    this.clients.forEach(ws => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(msg);
      }
    });
  }

  getClientCount(): number {
    return this.clients.size;
  }
}
