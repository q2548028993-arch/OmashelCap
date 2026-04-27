import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useWebSocket } from './hooks/useWebSocket'
import { useBotStore } from './store/botStore'
import { StatCard } from './components/StatCard'
import { SignalPanel } from './components/SignalPanel'
import { BotControls } from './components/BotControls'
import { TradeHistory } from './components/TradeHistory'
import './index.css'

const qc = new QueryClient()

function Header() {
  const { connected, balance, currency, running } = useBotStore()

  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-md sticky top-0 z-10">
      <div className="max-w-6xl mx-auto px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-lg bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center">
            <span className="text-emerald-400 text-xs font-bold">O</span>
          </div>
          <div>
            <h1 className="text-sm font-semibold text-slate-100 leading-none">OmashelCap</h1>
            <p className="text-[10px] text-slate-600 mt-0.5">Synthetic Indices · Automated Trading</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {balance > 0 && (
            <div className="text-right">
              <p className="text-xs font-mono font-semibold text-slate-200">${balance.toLocaleString('en', { minimumFractionDigits: 2 })}</p>
              <p className="text-[10px] text-slate-600">{currency} · Demo</p>
            </div>
          )}
          <div className="flex items-center gap-2 text-[11px]">
            <span className={`w-1.5 h-1.5 rounded-full ${connected ? 'bg-emerald-400 pulse-dot' : 'bg-rose-500'}`} />
            <span className={`font-medium ${connected ? 'text-slate-400' : 'text-rose-500'}`}>
              {connected ? 'Live' : 'Offline'}
            </span>
          </div>
          {running && (
            <span className="text-[10px] font-semibold text-emerald-400 bg-emerald-950/60 border border-emerald-900/50 px-2 py-1 rounded-md">
              LIVE
            </span>
          )}
        </div>
      </div>
    </header>
  )
}

function Dashboard() {
  useWebSocket()

  const { balance, currency, sessionPnl, wins, losses, winRate } = useBotStore()
  const total = wins + losses

  return (
    <div className="min-h-screen bg-[#08080f]">
      <Header />

      <main className="max-w-6xl mx-auto px-6 py-6 space-y-5">
        {/* Bot controls */}
        <BotControls />

        {/* Stats row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatCard
            label="Balance"
            value={`$${balance.toLocaleString('en', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
            sub={currency}
          />
          <StatCard
            label="Session P&L"
            value={`${sessionPnl >= 0 ? '+' : ''}$${sessionPnl.toFixed(2)}`}
            color={sessionPnl > 0 ? 'green' : sessionPnl < 0 ? 'red' : 'default'}
            sub={sessionPnl === 0 ? 'no trades yet' : sessionPnl > 0 ? 'in profit' : 'in drawdown'}
          />
          <StatCard
            label="Win Rate"
            value={`${(winRate * 100).toFixed(1)}%`}
            sub={total > 0 ? `${wins}W · ${losses}L · ${total} total` : 'no trades yet'}
            color={winRate >= 0.556 ? 'green' : winRate > 0 && total > 0 ? 'red' : 'default'}
          />
          <StatCard
            label="Trades"
            value={total}
            sub={total > 0 ? `${wins} wins · ${losses} losses` : 'waiting to start'}
            mono={false}
          />
        </div>

        {/* Signal + History */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <div className="lg:col-span-1">
            <SignalPanel />
          </div>
          <div className="lg:col-span-2">
            <TradeHistory />
          </div>
        </div>
      </main>
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <Dashboard />
    </QueryClientProvider>
  )
}
