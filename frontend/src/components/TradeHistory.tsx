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
  const { data } = await axios.get<{ trades: Trade[] }>('/api/trades/?limit=20')
  return data.trades
}

export function TradeHistory() {
  const { data: trades = [], isLoading } = useQuery({
    queryKey: ['trades'],
    queryFn: fetchTrades,
    refetchInterval: 5_000,
  })

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
      <p className="text-gray-500 text-xs uppercase tracking-widest mb-4">
        Recent Trades
        {trades.length > 0 && (
          <span className="ml-2 text-gray-600">({trades.length})</span>
        )}
      </p>

      {isLoading && <p className="text-gray-600 text-sm">Loading...</p>}

      {!isLoading && trades.length === 0 && (
        <p className="text-gray-600 text-sm">No trades yet — start the bot to begin.</p>
      )}

      {trades.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-gray-500 border-b border-gray-800">
                <th className="text-left pb-2 pr-4">Direction</th>
                <th className="text-left pb-2 pr-4">Symbol</th>
                <th className="text-right pb-2 pr-4">Stake</th>
                <th className="text-right pb-2 pr-4">Profit</th>
                <th className="text-left pb-2 pr-4">Trend</th>
                <th className="text-left pb-2 pr-4">Zone</th>
                <th className="text-right pb-2 pr-4">Score</th>
                <th className="text-right pb-2">Time</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((t) => (
                <tr
                  key={t.contract_id}
                  className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors"
                >
                  <td className={`py-2 pr-4 font-bold ${t.direction === 'CALL' ? 'text-emerald-400' : 'text-red-400'}`}>
                    {t.direction}
                  </td>
                  <td className="py-2 pr-4 text-gray-300">{t.symbol}</td>
                  <td className="py-2 pr-4 text-right text-gray-400">${t.stake.toFixed(2)}</td>
                  <td className={`py-2 pr-4 text-right font-bold ${t.is_win ? 'text-emerald-400' : 'text-red-400'}`}>
                    {t.profit >= 0 ? '+' : ''}${t.profit.toFixed(2)}
                  </td>
                  <td className="py-2 pr-4 text-gray-500">{t.trend}</td>
                  <td className="py-2 pr-4 text-gray-500">{t.zone}</td>
                  <td className="py-2 pr-4 text-right text-gray-400">{t.score}/5</td>
                  <td className="py-2 text-right text-gray-600">
                    {new Date(t.closed_at + 'Z').toLocaleTimeString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
