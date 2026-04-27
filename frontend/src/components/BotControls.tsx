import { useState } from 'react'
import axios from 'axios'
import { useBotStore } from '../store/botStore'

export function BotControls() {
  const { running, connected, cbTripped, cbReason, setStatus } = useBotStore()
  const [loading, setLoading] = useState(false)

  async function toggle() {
    setLoading(true)
    try {
      if (running) {
        await axios.post('/api/bot/stop')
        setStatus({ running: false })
      } else {
        await axios.post('/api/bot/start')
        setStatus({ running: true })
      }
    } catch (e: any) {
      console.error(e?.response?.data?.detail || e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-2">
      {cbTripped && (
        <div className="flex items-center gap-3 bg-rose-950/60 border border-rose-800/60 rounded-xl px-4 py-3">
          <span className="text-rose-400 text-lg">⚠</span>
          <div>
            <p className="text-rose-300 text-sm font-semibold">Circuit Breaker Active</p>
            <p className="text-rose-500 text-xs">{cbReason} — restart the bot to resume</p>
          </div>
        </div>
      )}

      <div className="bg-slate-900/70 border border-slate-800 rounded-xl px-4 py-3 flex items-center justify-between backdrop-blur-sm">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${connected ? 'bg-emerald-400 pulse-dot' : 'bg-rose-500'}`} />
            <span className="text-xs text-slate-400 font-medium">
              {connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          <div className="w-px h-4 bg-slate-800" />
          <span className={`text-xs font-semibold px-2 py-0.5 rounded-md ${
            running
              ? 'text-emerald-400 bg-emerald-950/60 border border-emerald-900/60'
              : 'text-slate-500 bg-slate-800/60 border border-slate-700/40'
          }`}>
            {running ? 'RUNNING' : 'IDLE'}
          </span>
        </div>

        <button
          onClick={toggle}
          disabled={loading || !connected || cbTripped}
          className={`px-6 py-2 rounded-lg text-sm font-semibold tracking-wide transition-all duration-150
            disabled:opacity-40 disabled:cursor-not-allowed select-none
            ${running
              ? 'bg-rose-600 hover:bg-rose-500 text-white glow-red'
              : 'bg-emerald-600 hover:bg-emerald-500 text-white glow-green'
            }`}
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              {running ? 'Stopping' : 'Starting'}
            </span>
          ) : running ? 'Stop Bot' : 'Start Bot'}
        </button>
      </div>
    </div>
  )
}
