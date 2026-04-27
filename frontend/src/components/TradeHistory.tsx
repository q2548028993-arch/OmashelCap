import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

interface Trade {
  contract_id: number
  symbol: string
  direction: string
  stake: number
  score: number
  profit: number
  is_win: boolean
  trend: string
  zone: string
  rsi: number
  opened_at: string
  closed_at: string
}

async function fetchTrades() {
  const { data } = await axios.get<{ trades: Trade[] }>('/api/trades/?limit=25')
  return data.trades
}

function DirectionBadge({ direction }: { direction: string }) {
  const isCall = direction === 'CALL'
  return (
    <span className={`inline-flex items-center gap-1 text-[11px] font-semibold font-mono px-2 py-0.5 rounded-md ${
      isCall
        ? 'text-emerald-400 bg-emerald-950/60 border border-emerald-900/50'
        : 'text-rose-400 bg-rose-950/60 border border-rose-900/50'
    }`}>
      {isCall ? '↑' : '↓'} {direction}
    </span>
  )
}

function ScoreDots({ score }: { score: number }) {
  return (
    <div className="flex gap-0.5 justify-end">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className={`w-1.5 h-1.5 rounded-full ${i <= score ? 'bg-slate-400' : 'bg-slate-800'}`} />
      ))}
    </div>
  )
}

export function TradeHistory() {
  const { data: trades = [], isLoading } = useQuery({
    queryKey: ['trades'],
    queryFn: fetchTrades,
    refetchInterval: 5_000,
  })

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-xl backdrop-blur-sm">
      <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <p className="text-slate-400 text-[10px] uppercase tracking-widest font-medium">Trade History</p>
          {trades.length > 0 && (
            <span className="text-[10px] font-mono text-slate-600 bg-slate-800 px-1.5 py-0.5 rounded">
              {trades.length}
            </span>
          )}
        </div>
        {trades.length > 0 && (
          <a
            href="/api/trades/export"
            download
            className="text-[11px] text-slate-500 hover:text-slate-300 transition-colors flex items-center gap-1"
          >
            ↓ Export CSV
          </a>
        )}
      </div>

      <div className="p-5">
        {isLoading && (
          <div className="flex items-center gap-2 text-slate-600 py-2">
            <span className="w-3 h-3 border-2 border-slate-700 border-t-slate-500 rounded-full animate-spin" />
            <span className="text-sm">Loading trades...</span>
          </div>
        )}

        {!isLoading && trades.length === 0 && (
          <p className="text-slate-600 text-sm py-2">No trades yet — start the bot to begin.</p>
        )}

        {trades.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-slate-600 text-[10px] uppercase tracking-widest">
                  <th className="text-left pb-3 pr-4 font-medium">Direction</th>
                  <th className="text-left pb-3 pr-4 font-medium">Symbol</th>
                  <th className="text-right pb-3 pr-4 font-medium">Stake</th>
                  <th className="text-right pb-3 pr-4 font-medium">P&L</th>
                  <th className="text-left pb-3 pr-4 font-medium">Trend</th>
                  <th className="text-left pb-3 pr-4 font-medium">Zone</th>
                  <th className="text-right pb-3 pr-4 font-medium">Score</th>
                  <th className="text-right pb-3 font-medium">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {trades.map((t) => (
                  <tr
                    key={t.contract_id}
                    className="hover:bg-slate-800/30 transition-colors"
                  >
                    <td className="py-2.5 pr-4">
                      <DirectionBadge direction={t.direction} />
                    </td>
                    <td className="py-2.5 pr-4 font-mono text-slate-300 font-medium">{t.symbol}</td>
                    <td className="py-2.5 pr-4 text-right font-mono text-slate-400">${t.stake.toFixed(2)}</td>
                    <td className={`py-2.5 pr-4 text-right font-mono font-semibold ${t.is_win ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {t.profit >= 0 ? '+' : ''}${t.profit.toFixed(2)}
                    </td>
                    <td className="py-2.5 pr-4 text-slate-500 font-mono text-[11px]">{t.trend}</td>
                    <td className="py-2.5 pr-4 text-slate-500 font-mono text-[11px]">{t.zone}</td>
                    <td className="py-2.5 pr-4 text-right">
                      <ScoreDots score={t.score} />
                    </td>
                    <td className="py-2.5 text-right font-mono text-slate-600">
                      {new Date(t.closed_at + 'Z').toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
