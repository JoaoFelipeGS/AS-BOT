interface LogPanelProps {
  logs: string[]
}

export default function LogPanel({ logs }: LogPanelProps) {
  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xl font-semibold">Logs ao vivo</h2>
        <span className="rounded-full bg-slate-800 px-3 py-1 text-sm text-slate-300">Tempo real</span>
      </div>
      <div className="max-h-72 space-y-2 overflow-y-auto rounded-3xl bg-slate-950 p-4 text-sm text-slate-300">
        {logs.length === 0 ? (
          <p className="text-slate-500 italic">Nenhuma mensagem recebida ainda...</p>
        ) : (
          logs.map((item, index) => (
            <div key={index} className="rounded-2xl bg-slate-900 p-3 border border-slate-800/50 animate-in fade-in slide-in-from-left-2 duration-300">
              {item}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
