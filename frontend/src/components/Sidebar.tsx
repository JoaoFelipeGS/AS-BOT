type SidebarProps = {
  selected: string[]
  setSelected: (value: string[]) => void
}

export default function Sidebar({ selected, setSelected }: SidebarProps) {
  return (
    <div className="selection-panel rounded-3xl border border-slate-800 bg-slate-900 p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Seleção visual</h2>
        <span className="rounded-full bg-slate-800 px-3 py-1 text-sm text-slate-300">{selected.length}</span>
      </div>
      <p className="text-sm leading-6 text-slate-400">Escolha os imóveis que deseja extrair. Sua seleção permanece ativa durante a navegação.</p>
      <button
        onClick={() => setSelected([])}
        className="mt-5 w-full rounded-2xl bg-slate-800 px-4 py-3 text-sm font-semibold text-white hover:bg-slate-700 transition"
      >
        Limpar seleção
      </button>
    </div>
  )
}
