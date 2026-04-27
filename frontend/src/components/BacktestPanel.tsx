import { useEffect, useRef, useState } from 'react'
import axios from 'axios'
import { createChart, AreaSeries } from 'lightweight-charts'
import type { IChartApi, ISeriesApi } from 'lightweight-charts'

const SYMBOLS = ['R_75', 'R_50', 'R_100', 'R_25', 'R_10', 'CRASH1000', 'BOOM1000']
const GRANULARITIES = [
  { value: 60, label: '1 min' },
  { value: 300, label: '5 min' },
  { value: 900, label: '15 min' },
  { value: 3600, label: '1 hour' },
]

interface BacktestResult {
  symbol: string
  granularity: number
  candle_count: number
  elapsed_s: number
  starting_balance: number
  final_balance: number
  roi_pct: number
  total_trades: number
  wins: number
  losses: number
  win_rate_pct: number
  total_pnl: number
  avg_win: number
  avg_loss: number
  profit_factor: number
  expectancy_per_trade: number
  max_drawdown_pct: number
  best_trade: number
  worst_trade: number
  max_consec_wins: number
  max_consec_losses: number
  equity_curve: { time: number; value: number }[]
  message?: string
  error?: string
}

function MetricRow({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-slate-800/50 last:border-0">
      <span className="text-slate-500 text-xs">{label}</span>
      <span className={`text-xs font-mono font-semibold ${color ?? 'text-slate-200'}`}>{value}</span>
    </div>
  )
}

function EquityChart({ data }: { data: { time: number; value: number }[] }) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const seriesRef = useRef<ISeriesApi<'Area', any> | null>(null)

  useEffect(() => {
    if (!containerRef.current || data.length === 0) return

    if (chartRef.current) {
      chartRef.current.remove()
    }

    const chart = createChart(containerRef.current, {
      layout: {
        background: { color: 'transparent' },
        textColor: '#64748b',
      },
      grid: {
        vertLines: { color: '#1e293b' },
        horzLines: { color: '#1e293b' },
      },
      rightPriceScale: { borderColor: '#1e293b' },
      timeScale: { borderColor: '#1e293b', timeVisible: true },
      crosshair: { mode: 1 },
      width: containerRef.current.clientWidth,
      height: 220,
    })

    const series = chart.addSeries(AreaSeries, {
      lineColor: '#10b981',
      topColor: 'rgba(16, 185, 129, 0.2)',
      bottomColor: 'rgba(16, 185, 129, 0.01)',
      lineWidth: 2,
      priceFormat: { type: 'price', precision: 2, minMove: 0.01 },
    })

    // lightweight-charts requires sorted, unique timestamps
    const seen = new Set<number>()
    const points: { time: any; value: number }[] = []
    for (const d of data) {
      if (!seen.has(d.time)) {
        seen.add(d.time)
        points.push({ time: d.time as any, value: d.value })
      }
    }
    points.sort((a, b) => (a.time as number) - (b.time as number))

    series.setData(points)
    chart.timeScale().fitContent()

    chartRef.current = chart
    seriesRef.current = series

    const ro = new ResizeObserver(() => {
      chart.applyOptions({ width: containerRef.current!.clientWidth })
    })
    ro.observe(containerRef.current)
    return () => { ro.disconnect(); chart.remove() }
  }, [data])

  return <div ref={containerRef} className="w-full" />
}

export function BacktestPanel() {
  const [symbol, setSymbol] = useState('R_75')
  const [granularity, setGranularity] = useState(60)
  const [count, setCount] = useState(2000)
  const [durationBars, setDurationBars] = useState(5)
  const [balance, setBalance] = useState(1000)
  const [minScore, setMinScore] = useState(3)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<BacktestResult | null>(null)
  const [error, setError] = useState('')

  async function run() {
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const { data } = await axios.post<BacktestResult>('/api/backtest/run', {
        symbol,
        granularity,
        count,
        trade_duration_bars: durationBars,
        starting_balance: balance,
        min_score: minScore,
      })
      if (data.error) { setError(data.error); return }
      setResult(data)
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message)
    } finally {
      setLoading(false)
    }
  }

  const winRateColor = result
    ? result.win_rate_pct >= 55.6 ? 'text-emerald-400'
    : result.win_rate_pct >= 50 ? 'text-amber-400'
    : 'text-rose-400'
    : ''

  const pnlColor = result
    ? result.total_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'
    : ''

  return (
    <div className="space-y-5">
      {/* Config form */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 backdrop-blur-sm">
        <p className="text-slate-400 text-[10px] uppercase tracking-widest font-medium mb-4">
          Backtest Configuration
        </p>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-5">
          <div>
            <label className="block text-[10px] text-slate-500 uppercase tracking-widest mb-1.5">Symbol</label>
            <select
              value={symbol}
              onChange={e => setSymbol(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 font-mono focus:outline-none focus:border-slate-500"
            >
              {SYMBOLS.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-[10px] text-slate-500 uppercase tracking-widest mb-1.5">Timeframe</label>
            <select
              value={granularity}
              onChange={e => setGranularity(Number(e.target.value))}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 font-mono focus:outline-none focus:border-slate-500"
            >
              {GRANULARITIES.map(g => <option key={g.value} value={g.value}>{g.label}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-[10px] text-slate-500 uppercase tracking-widest mb-1.5">
              Candles <span className="text-slate-600">(history depth)</span>
            </label>
            <select
              value={count}
              onChange={e => setCount(Number(e.target.value))}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 font-mono focus:outline-none focus:border-slate-500"
            >
              <option value={500}>500</option>
              <option value={1000}>1,000</option>
              <option value={2000}>2,000</option>
              <option value={3000}>3,000</option>
              <option value={5000}>5,000 (max)</option>
            </select>
          </div>

          <div>
            <label className="block text-[10px] text-slate-500 uppercase tracking-widest mb-1.5">
              Trade duration <span className="text-slate-600">(candles)</span>
            </label>
            <input
              type="number"
              value={durationBars}
              min={1} max={60}
              onChange={e => setDurationBars(Number(e.target.value))}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 font-mono focus:outline-none focus:border-slate-500"
            />
          </div>

          <div>
            <label className="block text-[10px] text-slate-500 uppercase tracking-widest mb-1.5">Starting balance ($)</label>
            <input
              type="number"
              value={balance}
              min={10}
              onChange={e => setBalance(Number(e.target.value))}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 font-mono focus:outline-none focus:border-slate-500"
            />
          </div>

          <div>
            <label className="block text-[10px] text-slate-500 uppercase tracking-widest mb-1.5">
              Min score <span className="text-slate-600">(confluence)</span>
            </label>
            <select
              value={minScore}
              onChange={e => setMinScore(Number(e.target.value))}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 font-mono focus:outline-none focus:border-slate-500"
            >
              {[2, 3, 4, 5].map(s => <option key={s} value={s}>{s}/5</option>)}
            </select>
          </div>
        </div>

        <button
          onClick={run}
          disabled={loading}
          className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-semibold rounded-lg transition-colors flex items-center gap-2"
        >
          {loading ? (
            <>
              <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Running backtest...
            </>
          ) : 'Run Backtest'}
        </button>
      </div>

      {error && (
        <div className="bg-rose-950/40 border border-rose-800/50 rounded-xl px-5 py-3 text-rose-400 text-sm">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-4">
          {result.message && (
            <div className="bg-amber-950/40 border border-amber-800/50 rounded-xl px-5 py-3 text-amber-400 text-sm">
              {result.message}
            </div>
          )}

          {result.total_trades > 0 && (
            <>
              {/* Key metrics */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-4">
                  <p className="text-[10px] text-slate-500 uppercase tracking-widest mb-1">Win Rate</p>
                  <p className={`text-2xl font-bold font-mono ${winRateColor}`}>{result.win_rate_pct.toFixed(1)}%</p>
                  <p className="text-[11px] text-slate-600 font-mono mt-1">{result.wins}W / {result.losses}L</p>
                </div>
                <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-4">
                  <p className="text-[10px] text-slate-500 uppercase tracking-widest mb-1">Total P&L</p>
                  <p className={`text-2xl font-bold font-mono ${pnlColor}`}>
                    {result.total_pnl >= 0 ? '+' : ''}${result.total_pnl.toFixed(2)}
                  </p>
                  <p className={`text-[11px] font-mono mt-1 ${pnlColor}`}>{result.roi_pct >= 0 ? '+' : ''}{result.roi_pct}% ROI</p>
                </div>
                <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-4">
                  <p className="text-[10px] text-slate-500 uppercase tracking-widest mb-1">Profit Factor</p>
                  <p className={`text-2xl font-bold font-mono ${result.profit_factor >= 1.2 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {result.profit_factor === Infinity ? '∞' : result.profit_factor.toFixed(2)}
                  </p>
                  <p className="text-[11px] text-slate-600 mt-1">{result.total_trades} trades</p>
                </div>
                <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-4">
                  <p className="text-[10px] text-slate-500 uppercase tracking-widest mb-1">Max Drawdown</p>
                  <p className={`text-2xl font-bold font-mono ${result.max_drawdown_pct <= 5 ? 'text-emerald-400' : result.max_drawdown_pct <= 15 ? 'text-amber-400' : 'text-rose-400'}`}>
                    {result.max_drawdown_pct}%
                  </p>
                  <p className="text-[11px] text-slate-600 mt-1">peak-to-trough</p>
                </div>
              </div>

              {/* Equity curve */}
              <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 backdrop-blur-sm">
                <p className="text-slate-400 text-[10px] uppercase tracking-widest font-medium mb-4">Equity Curve</p>
                <EquityChart data={result.equity_curve} />
              </div>

              {/* Detailed stats */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5">
                  <p className="text-slate-400 text-[10px] uppercase tracking-widest font-medium mb-3">Performance</p>
                  <MetricRow label="Starting balance" value={`$${result.starting_balance.toFixed(2)}`} />
                  <MetricRow label="Final balance" value={`$${result.final_balance.toFixed(2)}`} color={pnlColor} />
                  <MetricRow label="Expectancy / trade" value={`$${result.expectancy_per_trade.toFixed(4)}`} color={result.expectancy_per_trade > 0 ? 'text-emerald-400' : 'text-rose-400'} />
                  <MetricRow label="Avg win" value={`$${result.avg_win.toFixed(2)}`} color="text-emerald-400" />
                  <MetricRow label="Avg loss" value={`$${result.avg_loss.toFixed(2)}`} color="text-rose-400" />
                  <MetricRow label="Best trade" value={`$${result.best_trade.toFixed(2)}`} color="text-emerald-400" />
                  <MetricRow label="Worst trade" value={`$${result.worst_trade.toFixed(2)}`} color="text-rose-400" />
                </div>
                <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5">
                  <p className="text-slate-400 text-[10px] uppercase tracking-widest font-medium mb-3">Run Info</p>
                  <MetricRow label="Symbol" value={result.symbol} />
                  <MetricRow label="Timeframe" value={`${result.granularity}s candles`} />
                  <MetricRow label="Candles tested" value={result.candle_count.toLocaleString()} />
                  <MetricRow label="Max consec. wins" value={String(result.max_consec_wins)} color="text-emerald-400" />
                  <MetricRow label="Max consec. losses" value={String(result.max_consec_losses)} color="text-rose-400" />
                  <MetricRow label="Completed in" value={`${result.elapsed_s}s`} />
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
