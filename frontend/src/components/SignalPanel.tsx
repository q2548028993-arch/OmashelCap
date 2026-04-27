import { useBotStore } from '../store/botStore'

const SCORE_FILLS = [
  '',
  'bg-slate-600',
  'bg-rose-800',
  'bg-amber-700',
  'bg-emerald-700',
  'bg-emerald-500',
]

function ScoreBar({ score }: { score: number }) {
  return (
    <div className="flex items-center gap-1.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <div
          key={i}
          className={`h-1.5 flex-1 rounded-full transition-all duration-300 ${
            i <= score ? SCORE_FILLS[score] : 'bg-slate-800'
          }`}
        />
      ))}
      <span className="text-xs font-mono text-slate-400 ml-1 w-6 text-right">{score}/5</span>
    </div>
  )
}

function Badge({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-slate-800/60 border border-slate-700/40 rounded-lg px-3 py-1.5 text-center">
      <p className="text-[10px] text-slate-500 uppercase tracking-widest">{label}</p>
      <p className="text-xs font-semibold text-slate-200 font-mono mt-0.5">{value}</p>
    </div>
  )
}

export function SignalPanel() {
  const { lastSignal } = useBotStore()

  if (!lastSignal || lastSignal.direction === 'NONE') {
    return (
      <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 backdrop-blur-sm">
        <p className="text-slate-500 text-[10px] uppercase tracking-widest font-medium mb-4">
          Latest Signal
        </p>
        <div className="flex items-center gap-2 text-slate-600">
          <span className="w-1.5 h-1.5 rounded-full bg-slate-700 pulse-dot" />
          <p className="text-sm">Scanning market — waiting for confluence...</p>
        </div>
      </div>
    )
  }

  const isCall = lastSignal.direction === 'CALL'

  return (
    <div className={`border rounded-xl p-5 backdrop-blur-sm ${
      isCall
        ? 'bg-emerald-950/30 border-emerald-900/50'
        : 'bg-rose-950/30 border-rose-900/50'
    }`}>
      <p className="text-slate-400 text-[10px] uppercase tracking-widest font-medium mb-4">
        Latest Signal
      </p>

      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className={`text-4xl font-bold font-mono ${isCall ? 'text-emerald-400' : 'text-rose-400'}`}>
            {isCall ? '↑' : '↓'} {lastSignal.direction}
          </span>
          <span className={`text-sm font-medium px-2.5 py-1 rounded-lg border font-mono ${
            isCall
              ? 'text-emerald-400 bg-emerald-950/60 border-emerald-800/60'
              : 'text-rose-400 bg-rose-950/60 border-rose-800/60'
          }`}>
            {lastSignal.symbol}
          </span>
        </div>
      </div>

      <div className="mb-4">
        <p className="text-[10px] text-slate-500 uppercase tracking-widest mb-2">Confluence Score</p>
        <ScoreBar score={lastSignal.score} />
      </div>

      <div className="grid grid-cols-3 gap-2 mb-4">
        <Badge label="Trend" value={lastSignal.trend} />
        <Badge label="Zone" value={lastSignal.zone} />
        <Badge label="RSI" value={lastSignal.rsi.toFixed(1)} />
      </div>

      <p className="text-xs text-slate-500 italic border-t border-slate-800/60 pt-3">{lastSignal.reason}</p>
    </div>
  )
}
