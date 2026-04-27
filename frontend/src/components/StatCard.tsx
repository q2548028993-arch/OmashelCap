interface StatCardProps {
  label: string
  value: string | number
  sub?: string
  color?: 'green' | 'red' | 'yellow' | 'default'
  mono?: boolean
}

const colorMap = {
  green: 'text-emerald-400',
  red: 'text-rose-400',
  yellow: 'text-amber-400',
  default: 'text-slate-100',
}

const glowMap = {
  green: 'border-emerald-900/60',
  red: 'border-rose-900/60',
  yellow: 'border-amber-900/60',
  default: 'border-slate-800',
}

export function StatCard({ label, value, sub, color = 'default', mono = true }: StatCardProps) {
  return (
    <div className={`bg-slate-900/70 border ${glowMap[color]} rounded-xl p-4 backdrop-blur-sm`}>
      <p className="text-slate-500 text-[10px] uppercase tracking-widest font-medium mb-2">{label}</p>
      <p className={`text-2xl font-bold ${colorMap[color]} ${mono ? 'font-mono' : ''} leading-none`}>
        {value}
      </p>
      {sub && <p className="text-slate-600 text-[11px] mt-1.5 font-mono">{sub}</p>}
    </div>
  )
}
