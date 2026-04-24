import { useBotStore } from '../store/botStore'

const SCORE_COLORS = ['bg-gray-700', 'bg-red-900', 'bg-orange-800', 'bg-yellow-700', 'bg-emerald-700', 'bg-emerald-500']

export function SignalPanel() {
  const { lastSignal } = useBotStore()

  if (!lastSignal || lastSignal.direction === 'NONE') {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
        <p className="text-gray-500 text-xs uppercase tracking-widest mb-3">Latest Signal</p>
        <p className="text-gray-600 text-sm">Waiting for signal...</p>
      </div>
    )
  }

  const isCall = lastSignal.direction === 'CALL'

  return (
    <div className={`border rounded-lg p-4 ${isCall ? 'bg-emerald-950 border-emerald-800' : 'bg-red-950 border-red-800'}`}>
      <p className="text-gray-400 text-xs uppercase tracking-widest mb-3">Latest Signal</p>

      <div className="flex items-center gap-3 mb-3">
        <span className={`text-3xl font-bold ${isCall ? 'text-emerald-400' : 'text-red-400'}`}>
          {lastSignal.direction}
        </span>
        <span className="text-gray-400 text-sm">{lastSignal.symbol}</span>
      </div>

      {/* Score bar */}
      <div className="flex gap-1 mb-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className={`h-2 flex-1 rounded ${i <= lastSignal.score ? SCORE_COLORS[lastSignal.score] : 'bg-gray-800'}`}
          />
        ))}
        <span className="text-xs text-gray-400 ml-2">{lastSignal.score}/5</span>
      </div>

      <div className="grid grid-cols-3 gap-2 text-xs text-gray-400 mb-3">
        <span>Trend: <span className="text-gray-200">{lastSignal.trend}</span></span>
        <span>Zone: <span className="text-gray-200">{lastSignal.zone}</span></span>
        <span>RSI: <span className="text-gray-200">{lastSignal.rsi}</span></span>
      </div>

      <p className="text-xs text-gray-500 italic">{lastSignal.reason}</p>
    </div>
  )
}
