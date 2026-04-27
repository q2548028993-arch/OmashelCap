import { useEffect, useState } from 'react'
import axios from 'axios'

const SYMBOLS = ['R_75', 'R_50', 'R_100', 'R_25', 'R_10', 'CRASH1000', 'CRASH500', 'BOOM1000', 'BOOM500']
const GRANULARITIES = [
  { value: 60, label: '1 min' },
  { value: 300, label: '5 min' },
  { value: 900, label: '15 min' },
  { value: 3600, label: '1 hour' },
]

interface Settings {
  symbol: string
  granularity: number
  risk_per_trade: number
  min_stake: number
  max_stake: number
  trade_duration: number
  trade_duration_unit: string
  max_consecutive_losses: number
  daily_drawdown_limit: number
}

function Field({
  label, hint, children,
}: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-[10px] text-slate-500 uppercase tracking-widest mb-1.5">
        {label}
        {hint && <span className="ml-1 text-slate-700 normal-case tracking-normal">{hint}</span>}
      </label>
      {children}
    </div>
  )
}

const inputCls = 'w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 font-mono focus:outline-none focus:border-slate-500'

export function StrategyConfig() {
  const [cfg, setCfg] = useState<Settings | null>(null)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    axios.get<Settings>('/api/settings/').then(r => setCfg(r.data)).catch(() => {})
  }, [])

  async function save() {
    if (!cfg) return
    setSaving(true); setError(''); setSaved(false)
    try {
      await axios.patch('/api/settings/', {
        symbol: cfg.symbol,
        granularity: cfg.granularity,
        risk_per_trade: cfg.risk_per_trade,
        min_stake: cfg.min_stake,
        max_stake: cfg.max_stake,
        trade_duration: cfg.trade_duration,
        max_consecutive_losses: cfg.max_consecutive_losses,
      })
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message)
    } finally {
      setSaving(false)
    }
  }

  function set<K extends keyof Settings>(key: K, value: Settings[K]) {
    setCfg(prev => prev ? { ...prev, [key]: value } : prev)
  }

  if (!cfg) {
    return (
      <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5">
        <div className="flex items-center gap-2 text-slate-600">
          <span className="w-3 h-3 border-2 border-slate-700 border-t-slate-500 rounded-full animate-spin" />
          <span className="text-sm">Loading settings...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 backdrop-blur-sm">
      <div className="flex items-center justify-between mb-5">
        <p className="text-slate-400 text-[10px] uppercase tracking-widest font-medium">Strategy Configuration</p>
        <p className="text-[10px] text-slate-600">Changes apply on next bot start</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-5">
        <Field label="Symbol">
          <select value={cfg.symbol} onChange={e => set('symbol', e.target.value)} className={inputCls}>
            {SYMBOLS.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </Field>

        <Field label="Timeframe">
          <select value={cfg.granularity} onChange={e => set('granularity', Number(e.target.value))} className={inputCls}>
            {GRANULARITIES.map(g => <option key={g.value} value={g.value}>{g.label}</option>)}
          </select>
        </Field>

        <Field label="Risk per trade" hint="(% of balance)">
          <div className="relative">
            <input
              type="number"
              value={Math.round(cfg.risk_per_trade * 100 * 10) / 10}
              min={0.5} max={5} step={0.1}
              onChange={e => set('risk_per_trade', Number(e.target.value) / 100)}
              className={inputCls + ' pr-6'}
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 text-xs">%</span>
          </div>
        </Field>

        <Field label="Min stake" hint="($)">
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 text-xs">$</span>
            <input
              type="number"
              value={cfg.min_stake}
              min={0.35} step={0.05}
              onChange={e => set('min_stake', Number(e.target.value))}
              className={inputCls + ' pl-6'}
            />
          </div>
        </Field>

        <Field label="Max stake" hint="(hard ceiling)">
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 text-xs">$</span>
            <input
              type="number"
              value={cfg.max_stake}
              min={1} step={1}
              onChange={e => set('max_stake', Number(e.target.value))}
              className={inputCls + ' pl-6'}
            />
          </div>
        </Field>

        <Field label="Trade duration" hint="(minutes)">
          <input
            type="number"
            value={cfg.trade_duration}
            min={1} max={60}
            onChange={e => set('trade_duration', Number(e.target.value))}
            className={inputCls}
          />
        </Field>

        <Field label="Circuit breaker" hint="(consecutive losses)">
          <input
            type="number"
            value={cfg.max_consecutive_losses}
            min={2} max={20}
            onChange={e => set('max_consecutive_losses', Number(e.target.value))}
            className={inputCls}
          />
        </Field>

        <Field label="Daily drawdown limit">
          <div className="relative">
            <input
              type="number"
              value={Math.round(cfg.daily_drawdown_limit * 100 * 10) / 10}
              disabled
              className={inputCls + ' opacity-40 cursor-not-allowed'}
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 text-xs">%</span>
          </div>
        </Field>
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={save}
          disabled={saving}
          className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-sm font-semibold rounded-lg transition-colors flex items-center gap-2"
        >
          {saving ? (
            <>
              <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Saving...
            </>
          ) : 'Save Settings'}
        </button>

        {saved && <span className="text-emerald-400 text-sm">Saved — restart bot to apply</span>}
        {error && <span className="text-rose-400 text-sm">{error}</span>}
      </div>
    </div>
  )
}
