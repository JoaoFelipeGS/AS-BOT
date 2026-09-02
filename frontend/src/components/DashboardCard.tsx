type DashboardCardProps = {
  label: string
  value: string | number
}

export default function DashboardCard({ label, value }: DashboardCardProps) {
  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900 p-6 shadow-sm shadow-slate-950/20">
      <p className="text-sm uppercase tracking-[0.2em] text-slate-500">{label}</p>
      <p className="mt-3 text-4xl font-semibold text-white">{value}</p>
      <div className="mt-5 h-1 w-10 rounded-full bg-sky-300" />
    </div>
  )
}
