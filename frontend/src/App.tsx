import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useWebSocket } from './hooks/useWebSocket'
import { useBotStore } from './store/botStore'
import { StatCard } from './components/StatCard'
import { SignalPanel } from './components/SignalPanel'
import { BotControls } from './components/BotControls'
import { TradeHistory } from './components/TradeHistory'
import './index.css'

const qc = new QueryClient()

function Dashboard() {
  useWebSocket()

  const { balance, currency, sessionPnl, wins, losses, winRate } = useBotStore()
  const total = wins + losses

  return (
    <div className="min-h-screen bg-gray-950 p-6">
      <div className="max-w-5xl mx-auto space-y-4">

        {/* Header */}
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">OmashelCap</h1>
          <p className="text-gray-500 text-xs">Deriv Synthetic Indices — Automated Trading</p>
        </div>

        {/* Bot controls */}
        <BotControls />

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatCard label="Balance" value={`$${balance.toFixed(2)}`} sub={currency} />
          <StatCard
            label="Session P&L"
            value={`${sessionPnl >= 0 ? '+' : ''}$${sessionPnl.toFixed(2)}`}
            color={sessionPnl > 0 ? 'green' : sessionPnl < 0 ? 'red' : 'default'}
          />
          <StatCard
            label="Win Rate"
            value={`${(winRate * 100).toFixed(1)}%`}
            sub={`${wins}W / ${losses}L`}
            color={winRate >= 0.556 ? 'green' : winRate > 0 ? 'yellow' : 'default'}
          />
          <StatCard label="Trades" value={total} sub={`${wins} wins · ${losses} losses`} />
        </div>

        {/* Signal */}
        <SignalPanel />

        {/* Trade history */}
        <TradeHistory />

      </div>
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
