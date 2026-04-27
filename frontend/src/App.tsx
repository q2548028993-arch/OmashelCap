import { useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useWebSocket } from './hooks/useWebSocket'
import { useBotStore } from './store/botStore'
import { StatCard } from './components/StatCard'
import { SignalPanel } from './components/SignalPanel'
import { BotControls } from './components/BotControls'
import { TradeHistory } from './components/TradeHistory'
import { BacktestPanel } from './components/BacktestPanel'
import { StrategyConfig } from './components/StrategyConfig'
import { PriceChart } from './components/PriceChart'
import './index.css'

const qc = new QueryClient()

type Tab = 'dashboard' | 'backtest' | 'settings'

const TABS: { id: Tab; label: string }[] = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'backtest', label: 'Backtest' },
  { id: 'settings', label: 'Settings' },
]

function Header({ activeTab, onTab }: { activeTab: Tab; onTab: (t: Tab) => void }) {
  const { connected, balance, currency, running } = useBotStore()

  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-md sticky top-0 z-10">
      <div className="max-w-6xl mx-auto px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center">
              <span className="text-emerald-400 text-xs font-bold">O</span>
            </div>
            <div>
              <h1 className="text-sm font-semibold text-slate-100 leading-none">OmashelCap</h1>
              <p className="text-[10px] text-slate-600 mt-0.5">Synthetic Indices · Auto Trading</p>
            </div>
          </div>

          {/* Tabs */}
          <nav className="hidden md:flex items-center gap-1">
            {TABS.map(t => (
              <button
                key={t.id}
                onClick={() => onTab(t.id)}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  activeTab === t.id
                    ? 'bg-slate-800 text-slate-100'
                    : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                {t.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="flex items-center gap-4">
          {balance > 0 && (
            <div className="text-right">
              <p className="text-xs font-mono font-semibold text-slate-200">
                ${balance.toLocaleString('en', { minimumFractionDigits: 2 })}
              </p>
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

      {/* Mobile tabs */}
      <div className="md:hidden flex border-t border-slate-800">
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => onTab(t.id)}
            className={`flex-1 py-2 text-xs font-medium transition-colors ${
              activeTab === t.id
                ? 'text-emerald-400 border-b-2 border-emerald-500'
                : 'text-slate-500'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>
    </header>
  )
}

function Dashboard() {
  const { balance, currency, sessionPnl, wins, losses, winRate } = useBotStore()
  const total = wins + losses

  return (
    <div className="space-y-5">
      <BotControls />
      <PriceChart />
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
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-1"><SignalPanel /></div>
        <div className="lg:col-span-2"><TradeHistory /></div>
      </div>
    </div>
  )
}

function App() {
  useWebSocket()
  const [tab, setTab] = useState<Tab>('dashboard')

  return (
    <div className="min-h-screen bg-[#08080f]">
      <Header activeTab={tab} onTab={setTab} />
      <main className="max-w-6xl mx-auto px-6 py-6">
        {tab === 'dashboard' && <Dashboard />}
        {tab === 'backtest' && <BacktestPanel />}
        {tab === 'settings' && <StrategyConfig />}
      </main>
    </div>
  )
}

export default function Root() {
  return (
    <QueryClientProvider client={qc}>
      <App />
    </QueryClientProvider>
  )
}
