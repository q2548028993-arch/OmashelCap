import { useEffect, useRef } from 'react'
import { useBotStore } from '../store/botStore'

function wsUrl() {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${window.location.host}/ws/live`
}

export function useWebSocket() {
  const ws = useRef<WebSocket | null>(null)
  const pingRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const { setStatus, setSignal, setConnected } = useBotStore()

  useEffect(() => {
    let reconnectTimer: ReturnType<typeof setTimeout>

    function connect() {
      ws.current = new WebSocket(wsUrl())

      ws.current.onopen = () => {
        setConnected(true)
        pingRef.current = setInterval(() => ws.current?.send('ping'), 25_000)
      }

      ws.current.onmessage = (e) => {
        let msg: { event: string; data: Record<string, unknown> }
        try { msg = JSON.parse(e.data) } catch { return }

        switch (msg.event) {
          case 'snapshot':
          case 'status_update':
            setStatus({
              running: msg.data.running as boolean,
              balance: msg.data.balance as number,
              sessionPnl: msg.data.session_pnl as number,
              wins: msg.data.wins as number,
              losses: msg.data.losses as number,
              winRate: msg.data.win_rate as number,
              cbTripped: msg.data.cb_tripped as boolean,
              cbReason: (msg.data.cb_reason as string) ?? '',
            })
            break
          case 'signal':
            setSignal(msg.data as unknown as Parameters<typeof setSignal>[0])
            break
          case 'trade_closed':
            setStatus({
              sessionPnl: msg.data.session_pnl as number,
              wins: msg.data.wins as number,
              losses: msg.data.losses as number,
              winRate: msg.data.win_rate as number,
              balance: msg.data.balance as number,
            })
            break
        }
      }

      ws.current.onclose = () => {
        setConnected(false)
        if (pingRef.current) clearInterval(pingRef.current)
        reconnectTimer = setTimeout(connect, 3_000)
      }

      ws.current.onerror = () => ws.current?.close()
    }

    connect()

    return () => {
      clearTimeout(reconnectTimer)
      if (pingRef.current) clearInterval(pingRef.current)
      ws.current?.close()
    }
  }, [])
}
