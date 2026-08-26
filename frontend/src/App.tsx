import { useEffect, useState } from 'react'
import axios from 'axios'
import DashboardCard from './components/DashboardCard'
import Sidebar from './components/Sidebar'
import LogPanel from './components/LogPanel'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 0,
})

const getAuthHeaders = () => {
  const token = localStorage.getItem('as_marketplace_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

api.interceptors.request.use((config) => {
  config.headers = {
    ...(config.headers ?? {}),
    ...getAuthHeaders(),
  } as any
  return config
})

type DashboardStats = {
  total_extraidos: number
  total_publicados: number
  total_erros: number
  total_bloqueios: number
  fila_pendente: number
  taxa_sucesso: number
}

type ImovelItem = {
  id: number
  url: string
  titulo: string
  preco: number
  descricao?: string
  endereco?: string
  quartos: number
  banheiros: number
  garagem: number
  area: number
  tipo_negocio: string // NOVO: Venda ou Aluguel
  tipo_imovel: string // NOVO: Casa ou Apartamento
  imagens_json: string[]
}

type ItemFila = {
  id: number
  status: string
  tentativas: number
  publicado_em?: string
  url_facebook?: string
  mensagem_erro?: string
  agendado_para?: string
  imovel: ImovelItem
}

function getImageUrl(path: string) {
  if (!path) return ''
  if (path.startsWith('http')) return path
  return `${API_BASE_URL}${path.startsWith('/') ? '' : '/'}${path}`
}

function ViewDashboard({ stats }: { stats: DashboardStats | null }) {
  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {stats ? [
          { label: 'Extraídos', value: stats.total_extraidos },
          { label: 'Publicados', value: stats.total_publicados },
          { label: 'Erros', value: stats.total_erros },
          { label: 'Fila pendente', value: stats.fila_pendente },
          { label: 'Taxa de sucesso', value: `${stats.taxa_sucesso}%` },
        ].map(item => <DashboardCard key={item.label} label={item.label} value={item.value} />) : <p>Carregando...</p>}
      </section>
      <div className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="text-xl font-semibold mb-4">Resumo do Sistema</h2>
        <p className="text-slate-400">Sua automação está ativa. Use o menu lateral para navegar entre extração, revisão e fila.</p>
      </div>
    </div>
  )
}

function ViewExtract({
  urls,
  setUrls,
  isExtracting,
  handleExtract,
  logs,
  totalUrls,
}: {
  urls: string
  setUrls: (v: string) => void
  isExtracting: boolean
  handleExtract: () => void
  logs: string[]
  totalUrls: number
}) {
  const liveLogs = [...logs].slice(0, 30).reverse()
  return (
    <section className="relative rounded-3xl border border-slate-800 bg-slate-900 p-6 space-y-4 animate-in slide-in-from-bottom-4 duration-500 overflow-hidden">
      <div className="mb-4">
        <h2 className="text-xl font-semibold">Nova Extração</h2>
        <p className="text-slate-400">Cole as URLs dos imóveis abaixo para iniciar a captura.</p>
      </div>
      <textarea
        value={urls}
        onChange={(e) => setUrls(e.target.value)}
        rows={8}
        disabled={isExtracting}
        className="w-full rounded-3xl border border-slate-800 bg-slate-950 p-4 text-slate-100 outline-none focus:border-sky-500 transition-all disabled:opacity-50"
        placeholder="Cole as URLs aqui (uma por linha)..."
      />
      <button
        onClick={handleExtract}
        disabled={isExtracting}
        className={`w-full rounded-3xl py-4 font-bold text-slate-950 transition-all ${isExtracting ? 'bg-slate-600 cursor-not-allowed' : 'bg-sky-500 hover:bg-sky-400 shadow-lg shadow-sky-500/20'}`}
      >
        {isExtracting ? '⏳ Processando URLs...' : '🚀 Iniciar Extração'}
      </button>
      {isExtracting && (
        <div className="absolute inset-0 z-20 flex flex-col rounded-3xl bg-slate-950 border border-sky-500/30 animate-in fade-in duration-300">
          <div className="flex-1 flex flex-col items-center justify-center gap-4 p-6 text-center">
            <div className="h-12 w-12 rounded-full border-4 border-sky-500/20 border-t-sky-500 animate-spin" />
            <div className="text-slate-100 font-bold">Extraindo imóveis...</div>
          </div>
          <div className="max-h-48 overflow-y-auto bg-slate-900 border-t border-slate-800 px-4 py-3 font-mono text-xs text-sky-400 space-y-1">
            {liveLogs.map((log, idx) => <p key={idx} className="truncate">{log}</p>)}
          </div>
        </div>
      )}
    </section>
  )
}

function ViewReview({
  imoveis,
  setImoveis,
  handleDeleteImovel,
  handleSave,
  handleAddToQueue,
  setGalleryImovel,
}: {
  imoveis: ImovelItem[]
  setImoveis: React.Dispatch<React.SetStateAction<ImovelItem[]>>
  handleDeleteImovel: (id: number) => void
  handleSave: (imovel: ImovelItem) => void
  handleAddToQueue: (id: number) => void
  setGalleryImovel: (imovel: ImovelItem | null) => void
}) {
  return (
    <div className="space-y-4 animate-in fade-in duration-500">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Revisão de Imóveis</h2>
        <span className="rounded-full bg-slate-800 px-3 py-1 text-sm text-slate-300">{imoveis.length} itens</span>
      </div>
      {imoveis.length === 0 ? <p className="text-slate-400">Nenhum imóvel para revisar.</p> :
        imoveis.map((imovel) => (
          <div key={imovel.id} className="rounded-3xl border border-slate-800 bg-slate-950 p-5 hover:border-slate-700 transition-colors group">
            <div className="grid gap-6 lg:grid-cols-[1fr_300px]">
              <div className="space-y-4 relative">
                <button onClick={() => handleDeleteImovel(imovel.id)} className="absolute -top-2 -right-2 rounded-full bg-rose-500 p-2 text-white opacity-0 group-hover:opacity-100 transition-opacity shadow-lg">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                </button>
                
                <input className="w-full rounded-xl border border-slate-800 bg-slate-900 px-4 py-2 text-slate-100 outline-none" value={imovel.titulo} onChange={(e) => setImoveis(curr => curr.map(i => i.id === imovel.id ? {...i, titulo: e.target.value} : i))} />
                
                <div className="grid grid-cols-2 gap-4">
                  <input type="number" className="rounded-xl border border-slate-800 bg-slate-900 px-4 py-2 text-slate-100 outline-none" value={imovel.preco} onChange={(e) => setImoveis(curr => curr.map(i => i.id === imovel.id ? {...i, preco: Number(e.target.value)} : i))} />
                  
                  {/* NOVO: SELEÇÃO TIPO NEGOCIO */}
                  <select 
                    className="rounded-xl border border-slate-800 bg-slate-900 px-4 py-2 text-slate-100 outline-none"
                    value={imovel.tipo_negocio}
                    onChange={(e) => setImoveis(curr => curr.map(i => i.id === imovel.id ? {...i, tipo_negocio: e.target.value} : i))}
                  >
                    <option value="Venda">Venda</option>
                    <option value="Aluguel">Aluguel</option>
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  {/* NOVO: SELEÇÃO TIPO IMOVEL */}
                  <select 
                    className="rounded-xl border border-slate-800 bg-slate-900 px-4 py-2 text-slate-100 outline-none"
                    value={imovel.tipo_imovel}
                    onChange={(e) => setImoveis(curr => curr.map(i => i.id === imovel.id ? {...i, tipo_imovel: e.target.value} : i))}
                  >
                    <option value="Casa">Casa</option>
                    <option value="Apartamento">Apartamento</option>
                  </select>

                  <div className="flex gap-2">
                    <input type="number" className="w-1/2 rounded-xl border border-slate-800 bg-slate-900 px-4 py-2 text-slate-100 outline-none" value={imovel.quartos} onChange={(e) => setImoveis(curr => curr.map(i => i.id === imovel.id ? {...i, quartos: Number(e.target.value)} : i))} title="Quartos" />
                    <input type="number" className="w-1/2 rounded-xl border border-slate-800 bg-slate-900 px-4 py-2 text-slate-100 outline-none" value={imovel.banheiros} onChange={(e) => setImoveis(curr => curr.map(i => i.id === imovel.id ? {...i, banheiros: Number(e.target.value)} : i))} title="Banheiros" />
                  </div>
                </div>

                <textarea className="w-full rounded-xl border border-slate-800 bg-slate-900 px-4 py-2 text-slate-100 outline-none" rows={3} value={imovel.descricao || ''} onChange={(e) => setImoveis(curr => curr.map(i => i.id === imovel.id ? {...i, descricao: e.target.value} : i))} />
              </div>
              <div className="flex flex-col gap-3">
                <div className="rounded-2xl bg-slate-900 p-3 text-xs text-slate-400">
                  <p className="font-bold text-slate-200 mb-1">DETALHES</p>
                  <p>🛏 {imovel.quartos} | 🚿 {imovel.banheiros} | 📏 {imovel.area}m²</p>
                </div>
                <div onClick={() => setGalleryImovel(imovel)} className="cursor-pointer group/img relative">
                  {imovel.imagens_json?.[0] ? (
                    <img src={getImageUrl(imovel.imagens_json[0])} className="h-32 w-full rounded-2xl object-cover transition-opacity group-hover/img:opacity-80" />
                  ) : (
                    <div className="h-32 w-full rounded-2xl bg-slate-800 flex items-center justify-center text-slate-500 text-xs">Sem foto</div>
                  )}
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <button onClick={() => handleSave(imovel)} className="rounded-xl bg-emerald-600 py-2 text-xs font-bold text-white hover:bg-emerald-500 transition">Salvar</button>
                  <button onClick={() => handleAddToQueue(imovel.id)} className="rounded-xl bg-sky-600 py-2 text-xs font-bold text-white hover:bg-sky-500 transition">Enfileirar</button>
                </div>
              </div>
            </div>
          </div>
        ))
      }
    </div>
  )
}

function ViewQueue({
  queue,
  handleConfirm,
  handlePublish,
  handleRetry,
  handleDeleteQueue,
  publishingIds,
}: {
  queue: ItemFila[]
  handleConfirm: (id: number) => void
  handlePublish: (id: number) => void
  handleRetry: (id: number) => void
  handleDeleteQueue: (id: number) => void
  publishingIds: Set<number>
}) {
  return (
    <div className="space-y-4 animate-in fade-in duration-500">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Fila de Publicação</h2>
        <span className="rounded-full bg-slate-800 px-3 py-1 text-sm text-slate-300">{queue.length} itens</span>
      </div>
      {queue.length === 0 ? <p className="text-slate-400">Fila vazia.</p> :
        queue.map((item) => {
          const isPublishing = publishingIds.has(item.id)
          return (
            <div key={item.id} className="rounded-3xl border border-slate-800 bg-slate-950 p-4 flex items-center justify-between gap-4">
              <div className="flex flex-col gap-1">
                <p className="font-semibold">{item.imovel.titulo}</p>
                <p className="text-xs text-slate-500">R$ {item.imovel.preco.toLocaleString()}</p>
              </div>
              <div className="flex items-center gap-3">
                <span className={`rounded-full px-3 py-1 text-xs flex items-center gap-2 ${
                  isPublishing
                    ? 'bg-sky-500/20 text-sky-400 font-bold'
                    : item.status === 'aguardando_confirmacao'
                      ? 'bg-amber-500 text-black font-bold'
                      : 'bg-slate-800 text-slate-300'
                }`}>
                  {isPublishing && <span className="h-2 w-2 rounded-full bg-sky-400 animate-pulse" />}
                  {isPublishing ? 'publicando...' : item.status}
                </span>
                {isPublishing ? (
                  <div className="h-8 w-8 flex items-center justify-center">
                    <div className="h-4 w-4 rounded-full border-2 border-sky-500/30 border-t-sky-500 animate-spin" />
                  </div>
                ) : item.status === 'aguardando_confirmacao' ? (
                  <button onClick={() => handleConfirm(item.id)} className="rounded-full bg-emerald-500 p-2 text-white hover:bg-emerald-400 transition" title="Confirmar Publicação">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                  </button>
                ) : (
                  <div className="flex gap-2">
                    <button onClick={() => handlePublish(item.id)} className="p-2 rounded-full bg-sky-600 text-white hover:bg-sky-500 transition"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg></button>
                    <button onClick={() => handleRetry(item.id)} className="p-2 rounded-full bg-amber-600 text-white hover:bg-amber-500 transition"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M23 4v13.5a3.5 3.5 0 0 1-3.5 .5H3a3.5 3.5 0 0 1-2-2V6a2 2 0 0 1 2-2h5a2 2 0 0 1 2 2v1"/></svg></button>
                    <button onClick={() => handleDeleteQueue(item.id)} className="p-2 rounded-full bg-rose-600 text-white hover:bg-rose-500 transition"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg></button>
                  </div>
                )}
              </div>
            </div>
          )
        })
      }
    </div>
  )
}

function GalleryModal({
  galleryImovel,
  setGalleryImovel,
}: {
  galleryImovel: ImovelItem | null
  setGalleryImovel: (imovel: ImovelItem | null) => void
}) {
  if (!galleryImovel) return null
  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/90 p-4 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative max-w-5xl w-full max-h-[90vh] overflow-y-auto rounded-3xl bg-slate-900 p-6 border border-slate-800">
        <button
          onClick={() => setGalleryImovel(null)}
          className="absolute top-4 right-4 p-2 rounded-full bg-slate-800 text-white hover:bg-slate-700 transition"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
        </button>
        <h3 className="text-xl font-bold mb-6 pr-10">{galleryImovel.titulo}</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {galleryImovel.imagens_json && galleryImovel.imagens_json.length > 0 ? (
            galleryImovel.imagens_json.map((src, index) => (
              <div key={index} className="aspect-square rounded-xl overflow-hidden border border-slate-800 bg-slate-950">
                <img src={getImageUrl(src)} className="w-full h-full object-cover hover:scale-105 transition-transform duration-300" alt={`Foto ${index + 1}`} />
              </div>
            ))
          ) : (
            <p className="col-span-full text-center text-slate-500 py-10">Nenhuma imagem disponível.</p>
          )}
        </div>
      </div>
    </div>
  )
}

function LoginScreen({ onLogin }: { onLogin: (username: string, password: string) => Promise<void> }) {
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('admin123')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit() {
    setLoading(true)
    setError('')
    try {
      await onLogin(username, password)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Credenciais inválidas')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-6">
      <div className="w-full max-w-md rounded-3xl border border-slate-800 bg-slate-900 p-8 shadow-2xl shadow-sky-500/10">
        <p className="text-xs uppercase tracking-[0.3em] text-sky-500 font-bold">AS Marketplace SaaS</p>
        <h1 className="mt-4 text-3xl font-bold">Acesso ao painel</h1>
        <div className="mt-6 space-y-4">
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 outline-none focus:border-sky-500"
            placeholder="Usuário"
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 outline-none focus:border-sky-500"
            placeholder="Senha"
          />
          {error && <p className="text-sm text-rose-400">{error}</p>}
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="w-full rounded-2xl bg-sky-500 px-4 py-3 font-bold text-slate-950 transition hover:bg-sky-400 disabled:opacity-60"
          >
            {loading ? 'Entrando...' : 'Entrar'}
          </button>
        </div>
      </div>
    </div>
  )
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [activeTab, setActiveTab] = useState<'dashboard' | 'extract' | 'review' | 'queue'>('dashboard')
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [queue, setQueue] = useState<ItemFila[]>([])
  const [imoveis, setImoveis] = useState<ImovelItem[]>([])
  const [urls, setUrls] = useState('')
  const [statusMessage, setStatusMessage] = useState('')
  const [wsStatus, setWsStatus] = useState('Conectando...')
  const [logs, setLogs] = useState<string[]>([])
  const [selected, setSelected] = useState<string[]>([])
  const [isExtracting, setIsExtracting] = useState(false)
  const [extractTotalUrls, setExtractTotalUrls] = useState(0)
  const [publishingIds, setPublishingIds] = useState<Set<number>>(new Set())
  const [galleryImovel, setGalleryImovel] = useState<ImovelItem | null>(null)

  async function handleLogin(username: string, password: string) {
    const response = await api.post('/login', null, {
      params: { username, password },
    })
    const token = response.data.token
    localStorage.setItem('as_marketplace_token', token)
    setIsAuthenticated(true)
    await refreshData()
  }

  useEffect(() => {
    const token = localStorage.getItem('as_marketplace_token')
    if (token) {
      setIsAuthenticated(true)
      refreshData()
    }
  }, [])

  useEffect(() => {
    const connectWS = () => {
      const ws = new WebSocket(`${API_BASE_URL}/api/logs`)
      ws.onopen = () => { setWsStatus('🟢 Logs ao Vivo') }
      ws.onmessage = (event) => {
        setStatusMessage(event.data)
        setLogs((prev) => [event.data, ...prev].slice(0, 50))
      }
      ws.onerror = () => { setWsStatus('🔴 Erro de Conexão') }
      ws.onclose = () => {
        setWsStatus('⚪ Desconectado')
        setTimeout(connectWS, 5000)
      }
    }
    connectWS()
  }, [])

  async function refreshData() {
    try {
      const [statsRes, queueRes, imoveisRes] = await Promise.all([
        api.get('/dashboard'),
        api.get('/fila'),
        api.get('/imoveis'),
      ])
      setStats(statsRes.data)
      setQueue(queueRes.data)
      setImoveis(imoveisRes.data)
    } catch (error) {
      console.error('Erro ao carregar dados', error)
    }
  }

  async function handleExtract() {
    if (!urls.trim()) return setStatusMessage('Insira ao menos uma URL.')
    const rawUrls = urls.split(/\r?\n|,|;/).map(i => i.trim()).filter(Boolean)
    if (rawUrls.length === 0) return setStatusMessage('Insira ao menos uma URL.')
    try {
      setExtractTotalUrls(rawUrls.length)
      setIsExtracting(true)
      setStatusMessage('🚀 Extraindo... acompanhe nos logs!')
      const response = await api.post('/extract', { urls: rawUrls })
      setImoveis(response.data)
      setUrls('')
      await refreshData()
    } catch (error: any) {
      setStatusMessage(error?.response?.data?.detail || 'Falha na extração')
    } finally {
      setIsExtracting(false)
      setExtractTotalUrls(0)
    }
  }

  async function handleDeleteImovel(id: number) {
    if (!window.confirm('Excluir este imóvel permanentemente?')) return
    try {
      await api.delete(`/imoveis/${id}`)
      setStatusMessage('Imóvel removido com sucesso.')
      refreshData()
    } catch (e) { setStatusMessage('Erro ao excluir.') }
  }

  async function handleSave(imovel: ImovelItem) {
    try {
      await api.patch(`/imoveis/${imovel.id}`, imovel)
      setStatusMessage('Dados atualizados com sucesso.')
      refreshData()
    } catch (e) { setStatusMessage('Erro ao salvar.') }
  }

  async function handleAddToQueue(id: number) {
    try {
      await api.post(`/imoveis/${id}/queue`)
      setStatusMessage('Imóvel adicionado à fila com sucesso!')
      await refreshData()
    } catch (e) {
      setStatusMessage('Erro ao adicionar à fila.')
    }
  }

  async function handleRetry(id: number) {
    try {
      await api.post(`/fila/retry/${id}`)
      setStatusMessage('Reprocessando item da fila.')
      refreshData()
    } catch (e) { setStatusMessage('Falha ao reprocessar.') }
  }

  async function handleDeleteQueue(id: number) {
    try {
      await api.delete(`/fila/${id}`)
      setStatusMessage('Item removido da fila.')
      refreshData()
    } catch (e) { setStatusMessage('Falha ao remover item.') }
  }

  async function handlePublish(id: number) {
    if (publishingIds.has(id)) return
    setPublishingIds(prev => new Set(prev).add(id))
    try {
      setStatusMessage('Publicação iniciada.')
      await api.post('/fila/publish', { fila_id: id })
      await refreshData()
    } catch (e) {
      setStatusMessage('Erro ao publicar.')
    } finally {
      setPublishingIds(prev => {
        const next = new Set(prev)
        next.delete(id)
        return next
      })
    }
  }

  async function handleConfirm(id: number) {
    try {
      await api.post(`/fila/confirm/${id}`)
      setStatusMessage('Publicação confirmada! Browser encerrado.')
      refreshData()
    } catch (e) { setStatusMessage('Erro ao confirmar publicação.') }
  }

  if (!isAuthenticated) {
    return <LoginScreen onLogin={handleLogin} />
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans">
      <div className="max-w-[1600px] mx-auto px-4 py-6">
        <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs uppercase tracking-widest text-sky-500 font-bold mb-1">SaaS Control Panel</p>
            <h1 className="text-4xl font-bold tracking-tight">Facebook <span className="text-sky-500">Marketplace</span></h1>
            <p className="text-slate-400">Extração inteligente e automação de publicações.</p>
          </div>
          <div className="flex flex-col gap-2 items-end">
            <div className="rounded-full bg-slate-900 border border-slate-800 px-3 py-1 text-[10px] font-bold uppercase text-slate-400">
              {wsStatus}
            </div>
            <div className="rounded-2xl border border-slate-800 bg-slate-900 p-4 min-w-[250px]">
              <p className="text-xs uppercase text-slate-500 font-semibold">Status do Sistema</p>
              <p className="mt-1 text-slate-100 font-medium">{statusMessage || 'Sistema Pronto'}</p>
            </div>
          </div>
        </header>
        <div className="grid gap-6 xl:grid-cols-[240px_1fr]">
          <aside className="space-y-4">
            <nav className="flex flex-col gap-2">
              <button onClick={() => setActiveTab('dashboard')} className={`flex items-center gap-3 px-4 py-3 rounded-2xl transition-all ${activeTab === 'dashboard' ? 'bg-sky-500 text-slate-950 font-bold' : 'bg-slate-900 text-slate-400 hover:bg-slate-800'}`}>
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="9" x="14" y="3" rx="1"/><rect width="7" height="9" x="3" y="14" rx="1"/></svg> Dashboard
              </button>
              <button onClick={() => setActiveTab('extract')} className={`flex items-center gap-3 px-4 py-3 rounded-2xl transition-all ${activeTab === 'extract' ? 'bg-sky-500 text-slate-950 font-bold' : 'bg-slate-900 text-slate-400 hover:bg-slate-800'}`}>
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"/><path d="M15 12l-3-3-3 3 3 3"/></svg> Extrair
              </button>
              <button onClick={() => setActiveTab('review')} className={`flex items-center gap-3 px-4 py-3 rounded-2xl transition-all ${activeTab === 'review' ? 'bg-sky-500 text-slate-950 font-bold' : 'bg-slate-900 text-slate-400 hover:bg-slate-800'}`}>
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M16 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg> Revisão
              </button>
              <button onClick={() => setActiveTab('queue')} className={`flex items-center gap-3 px-4 py-3 rounded-2xl transition-all ${activeTab === 'queue' ? 'bg-sky-500 text-slate-950 font-bold' : 'bg-slate-900 text-slate-400 hover:bg-slate-800'}`}>
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2v20M17 5H7M17 19H7"/></svg> Fila
              </button>
            </nav>
            <div className="pt-4 border-t border-slate-800">
              <Sidebar selected={selected} setSelected={setSelected} />
            </div>
          </aside>
          <main className="space-y-6">
            {activeTab === 'dashboard' && <ViewDashboard stats={stats} />}
            {activeTab === 'extract' && (
              <ViewExtract
                urls={urls}
                setUrls={setUrls}
                isExtracting={isExtracting}
                handleExtract={handleExtract}
                logs={logs}
                totalUrls={extractTotalUrls}
              />
            )}
            {activeTab === 'review' && (
              <ViewReview
                imoveis={imoveis}
                setImoveis={setImoveis}
                handleDeleteImovel={handleDeleteImovel}
                handleSave={handleSave}
                handleAddToQueue={handleAddToQueue}
                setGalleryImovel={setGalleryImovel}
              />
            )}
            {activeTab === 'queue' && (
              <ViewQueue
                queue={queue}
                handleConfirm={handleConfirm}
                handlePublish={handlePublish}
                handleRetry={handleRetry}
                handleDeleteQueue={handleDeleteQueue}
                publishingIds={publishingIds}
              />
            )}
            <div className="pt-6">
              <LogPanel logs={logs} />
            </div>
          </main>
        </div>
      </div>
      <GalleryModal galleryImovel={galleryImovel} setGalleryImovel={setGalleryImovel} />
    </div>
  )
}

export default App
