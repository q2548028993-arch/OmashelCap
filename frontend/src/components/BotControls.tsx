import { useState } from 'react'
import axios from 'axios'
import { useBotStore } from '../store/botStore'

export function BotControls() {
  const { running, connected, cbTripped, cbReason, consecutiveLosses } = useBotStore()
  const [loading, setLoading] = useState(false)

  async function toggle() {
    setLoading(true)
    try {
      if (running) {
        await axios.post('/api/bot/stop')
      } else {
        await axios.post('/api/bot/start')
      }
    } catch (e: any) {
      console.error(e?.response?.data?.detail || e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className={`w-2 h-2 rounded-full ${connected ? 'bg-emerald-400' : 'bg-red-500'} animate-pulse`} />
        <span className="text-xs text-gray-400">{connected ? 'Connected' : 'Disconnected'}</span>
        {cbTripped && (
          <span className="text-xs text-red-400 bg-red-950 px-2 py-0.5 rounded border border-red-800">
            CIRCUIT BREAKER: {cbReason}
          </span>
        )}
      </div>

      <button
        onClick={toggle}
        disabled={loading || !connected || cbTripped}
        className={`px-5 py-2 rounded text-sm font-bold transition-all disabled:opacity-40 disabled:cursor-not-allowed
          ${running
            ? 'bg-red-800 hover:bg-red-700 text-white'
            : 'bg-emerald-700 hover:bg-emerald-600 text-white'
          }`}
      >
        {loading ? '...' : running ? 'STOP BOT' : 'START BOT'}
      </button>
    </div>
  )
}
