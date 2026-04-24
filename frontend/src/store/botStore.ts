import { create } from 'zustand'

interface Signal {
  symbol: string
  direction: 'CALL' | 'PUT' | 'NONE'
  score: number
  reason: string
  trend: string
  zone: string
  rsi: number
}

interface BotStore {
  running: boolean
  balance: number
  currency: string
  sessionPnl: number
  wins: number
  losses: number
  winRate: number
  cbTripped: boolean
  cbReason: string
  consecutiveLosses: number
  lastSignal: Signal | null
  connected: boolean

  setStatus: (data: Partial<BotStore>) => void
  setSignal: (signal: Signal) => void
  setConnected: (v: boolean) => void
}

export const useBotStore = create<BotStore>((set) => ({
  running: false,
  balance: 0,
  currency: 'USD',
  sessionPnl: 0,
  wins: 0,
  losses: 0,
  winRate: 0,
  cbTripped: false,
  cbReason: '',
  consecutiveLosses: 0,
  lastSignal: null,
  connected: false,

  setStatus: (data) => set((s) => ({ ...s, ...data })),
  setSignal: (signal) => set({ lastSignal: signal }),
  setConnected: (v) => set({ connected: v }),
}))
