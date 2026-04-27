import { useEffect, useRef, useState } from 'react'
import { createChart, CandlestickSeries } from 'lightweight-charts'
import type { IChartApi, ISeriesApi } from 'lightweight-charts'

const SYMBOLS = ['R_75', 'R_50', 'R_100', 'R_25', 'R_10', 'CRASH1000', 'BOOM1000', 'CRASH500', 'BOOM500']
const TIMEFRAMES = [
  { value: 60, label: '1M' },
  { value: 300, label: '5M' },
  { value: 900, label: '15M' },
  { value: 3600, label: '1H' },
]

interface Bar {
  time: number
  open: number
  high: number
  low: number
  close: number
}

type Status = 'connecting' | 'live' | 'error'

function chartWsUrl(symbol: string, granularity: number) {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${window.location.host}/ws/chart?symbol=${symbol}&granularity=${granularity}`
}

export function PriceChart() {
  const [symbol, setSymbol] = useState('R_75')
  const [granularity, setGranularity] = useState(60)
  const [status, setStatus] = useState<Status>('connecting')
  const [lastPrice, setLastPrice] = useState<number | null>(null)
  const [priceChange, setPriceChange] = useState<number>(0)

  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const seriesRef = useRef<ISeriesApi<'Candlestick', any> | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const openPriceRef = useRef<number | null>(null)

  useEffect(() => {
    if (!containerRef.current) return

    // Tear down previous chart if symbol/granularity changed
    if (chartRef.current) {
      chartRef.current.remove()
      chartRef.current = null
      seriesRef.current = null
    }

    setStatus('connecting')
    setLastPrice(null)
    openPriceRef.current = null

    const chart = createChart(containerRef.current, {
      layout: {
        background: { color: 'transparent' },
        textColor: '#64748b',
        fontFamily: 'JetBrains Mono, monospace',
        fontSize: 11,
      },
      grid: {
        vertLines: { color: '#1e293b' },
        horzLines: { color: '#1e293b' },
      },
      crosshair: {
        vertLine: { color: '#475569', labelBackgroundColor: '#1e293b' },
        horzLine: { color: '#475569', labelBackgroundColor: '#1e293b' },
      },
      rightPriceScale: {
        borderColor: '#1e293b',
        scaleMargins: { top: 0.08, bottom: 0.08 },
      },
      timeScale: {
        borderColor: '#1e293b',
        timeVisible: true,
        secondsVisible: false,
      },
      width: containerRef.current.clientWidth,
      height: 340,
    })
    chartRef.current = chart

    const series = chart.addSeries(CandlestickSeries, {
      upColor: '#10b981',
      downColor: '#ef4444',
      borderUpColor: '#10b981',
      borderDownColor: '#ef4444',
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
    })
    seriesRef.current = series

    const ro = new ResizeObserver(() => {
      if (containerRef.current && chartRef.current) {
        chartRef.current.applyOptions({ width: containerRef.current.clientWidth })
      }
    })
    ro.observe(containerRef.current)

    let reconnectTimer: ReturnType<typeof setTimeout>

    function connect() {
      const ws = new WebSocket(chartWsUrl(symbol, granularity))
      wsRef.current = ws

      ws.onmessage = (e) => {
        const msg = JSON.parse(e.data) as {
          type: string
          bars?: Bar[]
          bar?: Bar
          message?: string
        }

        if (msg.type === 'history' && msg.bars && seriesRef.current) {
          const sorted = [...msg.bars].sort((a, b) => a.time - b.time)
          seriesRef.current.setData(sorted as any)
          if (sorted.length > 0) {
            const last = sorted[sorted.length - 1]
            setLastPrice(last.close)
            openPriceRef.current = sorted[0].open
            setPriceChange(
              openPriceRef.current
                ? ((last.close - openPriceRef.current) / openPriceRef.current) * 100
                : 0
            )
          }
          chartRef.current?.timeScale().fitContent()
          setStatus('live')
        } else if (msg.type === 'update' && msg.bar && seriesRef.current) {
          seriesRef.current.update(msg.bar as any)
          setLastPrice(msg.bar.close)
          if (openPriceRef.current) {
            setPriceChange(
              ((msg.bar.close - openPriceRef.current) / openPriceRef.current) * 100
            )
          }
        } else if (msg.type === 'error') {
          setStatus('error')
        }
      }

      ws.onopen = () => setStatus('connecting')
      ws.onclose = () => {
        setStatus('connecting')
        reconnectTimer = setTimeout(connect, 3_000)
      }
      ws.onerror = () => ws.close()
    }

    connect()

    return () => {
      clearTimeout(reconnectTimer)
      wsRef.current?.close()
      ro.disconnect()
      if (chartRef.current) {
        chartRef.current.remove()
        chartRef.current = null
        seriesRef.current = null
      }
    }
  }, [symbol, granularity])

  const isUp = priceChange >= 0

  return (
    <div className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
        {/* Left: symbol picker + price */}
        <div className="flex items-center gap-3">
          <select
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            className="bg-slate-800 text-slate-200 text-xs font-mono font-semibold border border-slate-700 rounded-md px-2 py-1 focus:outline-none focus:border-emerald-500 cursor-pointer"
          >
            {SYMBOLS.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>

          {lastPrice !== null && (
            <div className="flex items-center gap-2">
              <span className="text-base font-mono font-bold text-slate-100">
                {lastPrice.toFixed(lastPrice > 1000 ? 2 : 4)}
              </span>
              <span
                className={`text-xs font-mono font-semibold px-1.5 py-0.5 rounded ${
                  isUp
                    ? 'text-emerald-400 bg-emerald-950/60'
                    : 'text-rose-400 bg-rose-950/60'
                }`}
              >
                {isUp ? '+' : ''}{priceChange.toFixed(3)}%
              </span>
            </div>
          )}
        </div>

        {/* Right: timeframe + status */}
        <div className="flex items-center gap-2">
          <div className="flex items-center rounded-lg border border-slate-700 overflow-hidden">
            {TIMEFRAMES.map((tf) => (
              <button
                key={tf.value}
                onClick={() => setGranularity(tf.value)}
                className={`px-2.5 py-1 text-xs font-medium transition-colors ${
                  granularity === tf.value
                    ? 'bg-slate-700 text-slate-100'
                    : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800'
                }`}
              >
                {tf.label}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-1.5 ml-1">
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                status === 'live'
                  ? 'bg-emerald-400 pulse-dot'
                  : status === 'error'
                  ? 'bg-rose-500'
                  : 'bg-amber-400 pulse-dot'
              }`}
            />
            <span
              className={`text-[11px] font-medium ${
                status === 'live'
                  ? 'text-slate-500'
                  : status === 'error'
                  ? 'text-rose-400'
                  : 'text-amber-400'
              }`}
            >
              {status === 'live' ? 'Live' : status === 'error' ? 'Error' : 'Connecting…'}
            </span>
          </div>
        </div>
      </div>

      {/* Chart canvas */}
      <div ref={containerRef} className="w-full" />

      {/* Footer: volume/info bar */}
      <div className="px-4 py-2 border-t border-slate-800 flex items-center gap-4">
        <span className="text-[11px] text-slate-600">Synthetic Indices · Deriv</span>
        <span className="text-[11px] text-slate-700">
          {TIMEFRAMES.find((t) => t.value === granularity)?.label} candles · last 120 bars
        </span>
      </div>
    </div>
  )
}
