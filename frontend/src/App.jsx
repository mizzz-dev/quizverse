import { useEffect, useMemo, useState } from 'react'

const navItems = [
  { key: 'dashboard', label: 'ダッシュボード', path: '/admin' },
  { key: 'users', label: 'ユーザー管理', path: '/admin/users' },
  { key: 'quizzes', label: 'クイズ管理', path: '/admin/quizzes' },
  { key: 'settings', label: 'メール設定', path: '/admin/settings' },
]

const fallbackOverview = {
  summary: { users: 0, quizzes: 0, plays: 0, ranking_entries: 0 },
  services: {
    api: { status: 'warning', latency_ms: null },
    database: { status: 'warning', latency_ms: null },
    mail_delivery: { status: 'warning', latency_ms: null },
  },
}

const statusTone = {
  ok: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  warning: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  error: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
}

function usePath() {
  const [path, setPath] = useState(window.location.pathname)
  useEffect(() => {
    const onPopState = () => setPath(window.location.pathname)
    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [])

  const moveTo = (nextPath) => {
    window.history.pushState({}, '', nextPath)
    setPath(nextPath)
  }

  return { path, moveTo }
}

function useAdminData(isAdmin) {
  const [overview, setOverview] = useState(null)
  const [users, setUsers] = useState([])
  const [quizzes, setQuizzes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchData = async () => {
      if (!isAdmin) {
        setLoading(false)
        return
      }

      setLoading(true)
      setError('')
      try {
        const [overviewRes, usersRes, quizzesRes] = await Promise.all([
          fetch('/api/admin/overview'),
          fetch('/api/admin/users?per_page=8&page=1'),
          fetch('/api/admin/quizzes?per_page=8&page=1'),
        ])

        if (!overviewRes.ok || !usersRes.ok || !quizzesRes.ok) {
          throw new Error('管理APIの取得に失敗しました。')
        }

        const [overviewJson, usersJson, quizzesJson] = await Promise.all([
          overviewRes.json(),
          usersRes.json(),
          quizzesRes.json(),
        ])

        setOverview(overviewJson)
        setUsers(usersJson.items ?? [])
        setQuizzes(quizzesJson.items ?? [])
      } catch (err) {
        setOverview(fallbackOverview)
        setUsers([])
        setQuizzes([])
        setError(err instanceof Error ? err.message : '不明なエラーが発生しました。')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [isAdmin])

  return { overview, users, quizzes, loading, error }
}

function AdminLayout({ children, moveTo, path, onToggleAdmin, isAdmin }) {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto flex w-full max-w-7xl gap-6 p-4 md:p-6">
        <aside className="sticky top-4 hidden h-[calc(100vh-2rem)] w-72 shrink-0 rounded-3xl border border-slate-800 bg-slate-900/80 p-5 shadow-2xl shadow-slate-950/40 backdrop-blur md:flex md:flex-col">
          <p className="text-xs uppercase tracking-[0.2em] text-cyan-300">QuizVerse Admin</p>
          <h1 className="mt-2 text-xl font-semibold">管理ダッシュボード</h1>
          <nav className="mt-6 space-y-2">
            {navItems.map((item) => (
              <button
                key={item.key}
                className={`w-full rounded-xl border px-3 py-2 text-left text-sm transition ${
                  path === item.path
                    ? 'border-cyan-400/60 bg-cyan-500/15 text-cyan-200'
                    : 'border-slate-800 bg-slate-900 hover:border-slate-600 hover:bg-slate-800'
                }`}
                onClick={() => moveTo(item.path)}
              >
                {item.label}
              </button>
            ))}
          </nav>
          <div className="mt-auto rounded-2xl border border-slate-700 bg-gradient-to-br from-cyan-500/10 to-indigo-500/10 p-3 text-xs text-slate-300">
            権限制御は仮置きです。<br />
            ローカル検証用に admin フラグを切り替えられます。
          </div>
          <button
            className="mt-3 rounded-xl border border-slate-700 px-3 py-2 text-sm hover:bg-slate-800"
            onClick={onToggleAdmin}
          >
            {isAdmin ? '管理者モードを解除' : '管理者モードを有効化'}
          </button>
        </aside>

        <div className="flex-1">
          <header className="sticky top-4 z-20 mb-4 rounded-2xl border border-slate-800 bg-slate-900/85 px-4 py-3 shadow-xl shadow-slate-950/30 backdrop-blur">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p className="text-xs text-slate-400">Admin Area</p>
                <p className="text-sm text-slate-200">URL: {path}</p>
              </div>
              <div className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-300">
                権限: {isAdmin ? 'admin(仮)' : 'general'}
              </div>
            </div>
          </header>
          {children}
        </div>
      </div>
    </div>
  )
}

function SkeletonCard() {
  return <div className="h-28 animate-pulse rounded-2xl border border-slate-800 bg-slate-900" />
}

function DashboardPage({ overview, loading }) {
  const summaryCards = useMemo(
    () => [
      { label: 'ユーザー数', value: overview?.summary?.users ?? 0 },
      { label: 'クイズ数', value: overview?.summary?.quizzes ?? 0 },
      { label: 'プレイ数', value: overview?.summary?.plays ?? 0 },
      { label: 'ランキング件数', value: overview?.summary?.ranking_entries ?? 0 },
    ],
    [overview],
  )

  return (
    <section className="space-y-5">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {loading
          ? [...Array(4)].map((_, idx) => <SkeletonCard key={idx} />)
          : summaryCards.map((card) => (
              <article
                key={card.label}
                className="rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900 to-slate-900/70 p-4 shadow-lg shadow-slate-950/40 transition hover:-translate-y-0.5 hover:border-cyan-400/40"
              >
                <p className="text-sm text-slate-400">{card.label}</p>
                <p className="mt-4 text-3xl font-semibold text-cyan-200">{card.value}</p>
              </article>
            ))}
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
        <h2 className="text-lg font-semibold">サービス状況</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {Object.entries(overview?.services ?? {}).map(([name, service]) => (
            <div key={name} className="rounded-xl border border-slate-700 bg-slate-950/70 p-3">
              <div className="mb-2 flex items-center justify-between">
                <p className="text-sm text-slate-300">{name}</p>
                <span className={`rounded-full border px-2 py-0.5 text-xs ${statusTone[service.status] ?? statusTone.warning}`}>
                  {service.status}
                </span>
              </div>
              <p className="text-xs text-slate-400">Latency: {service.latency_ms ?? 'N/A'} ms</p>
              {service.note && <p className="mt-1 text-xs text-slate-500">{service.note}</p>}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function UsersPage({ users, loading }) {
  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
      <h2 className="text-lg font-semibold">ユーザー管理一覧（MVP）</h2>
      {loading ? (
        <div className="mt-4 space-y-2">{[...Array(6)].map((_, idx) => <SkeletonCard key={idx} />)}</div>
      ) : users.length === 0 ? (
        <p className="mt-4 rounded-xl border border-dashed border-slate-700 p-6 text-sm text-slate-400">ユーザーが存在しません。</p>
      ) : (
        <div className="mt-4 overflow-hidden rounded-xl border border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-900 text-slate-400">
              <tr>
                <th className="px-3 py-2">ID</th><th className="px-3 py-2">名前</th><th className="px-3 py-2">Email(マスク)</th><th className="px-3 py-2">状態</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id} className="border-t border-slate-800 hover:bg-slate-800/60">
                  <td className="px-3 py-2">{user.id}</td><td className="px-3 py-2">{user.display_name}</td><td className="px-3 py-2">{user.email_masked}</td><td className="px-3 py-2">{user.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

function QuizzesPage({ quizzes, loading }) {
  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
      <h2 className="text-lg font-semibold">クイズ管理一覧（MVP）</h2>
      {loading ? (
        <div className="mt-4 space-y-2">{[...Array(6)].map((_, idx) => <SkeletonCard key={idx} />)}</div>
      ) : quizzes.length === 0 ? (
        <p className="mt-4 rounded-xl border border-dashed border-slate-700 p-6 text-sm text-slate-400">クイズが存在しません。</p>
      ) : (
        <div className="mt-4 overflow-hidden rounded-xl border border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-900 text-slate-400">
              <tr>
                <th className="px-3 py-2">ID</th><th className="px-3 py-2">タイトル</th><th className="px-3 py-2">作成者</th><th className="px-3 py-2">プレイ数</th>
              </tr>
            </thead>
            <tbody>
              {quizzes.map((quiz) => (
                <tr key={quiz.id} className="border-t border-slate-800 hover:bg-slate-800/60">
                  <td className="px-3 py-2">{quiz.id}</td><td className="px-3 py-2">{quiz.title}</td><td className="px-3 py-2">{quiz.author.display_name}</td><td className="px-3 py-2">{quiz.play_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

function SettingsPage() {
  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
      <h2 className="text-lg font-semibold">メール設定（雛形）</h2>
      <p className="mt-3 text-sm text-slate-400">今回は導線のみ実装。保存機能は次Issueで対応予定です。</p>
      <div className="mt-4 rounded-xl border border-dashed border-slate-700 p-4 text-sm text-slate-300">
        SMTPホスト / 送信元アドレス / テンプレートの管理UIをここに追加予定です。
      </div>
    </section>
  )
}

export function App() {
  const { path, moveTo } = usePath()
  const [isAdmin, setIsAdmin] = useState(() => localStorage.getItem('quizverse_is_admin') === 'true')

  const onToggleAdmin = () => {
    const next = !isAdmin
    localStorage.setItem('quizverse_is_admin', String(next))
    setIsAdmin(next)
  }

  const { overview, users, quizzes, loading, error } = useAdminData(isAdmin)

  const page = useMemo(() => {
    if (path === '/admin') return <DashboardPage overview={overview} loading={loading} />
    if (path === '/admin/users') return <UsersPage users={users} loading={loading} />
    if (path === '/admin/quizzes') return <QuizzesPage quizzes={quizzes} loading={loading} />
    if (path === '/admin/settings') return <SettingsPage />
    return (
      <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 text-sm text-slate-300">
        ページが見つかりません。<button className="ml-2 underline" onClick={() => moveTo('/admin')}>/admin に戻る</button>
      </section>
    )
  }, [loading, moveTo, overview, path, quizzes, users])

  return (
    <AdminLayout moveTo={moveTo} path={path} onToggleAdmin={onToggleAdmin} isAdmin={isAdmin}>
      {!isAdmin ? (
        <section className="rounded-2xl border border-amber-500/40 bg-amber-500/10 p-5 text-amber-100">
          <h2 className="text-lg font-semibold">管理者権限が必要です（仮置き）</h2>
          <p className="mt-2 text-sm text-amber-200">
            本Issueでは RBAC は未実装です。サイドバー下部のボタンで admin 判定を切り替えて検証してください。
          </p>
        </section>
      ) : (
        <>
          {error && <p className="mb-4 rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">{error}</p>}
          {page}
        </>
      )}
    </AdminLayout>
  )
}
