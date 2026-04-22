import { useEffect, useMemo, useState } from 'react'

const navItems = [
  { key: 'dashboard', label: 'ダッシュボード', path: '/admin' },
  { key: 'users', label: 'ユーザー管理', path: '/admin/users' },
  { key: 'quizzes', label: 'クイズ管理', path: '/admin/quizzes' },
  { key: 'settings_email', label: 'メール設定', path: '/admin/settings/email' },
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

const defaultEmailSettings = {
  sender_name: '',
  sender_email: '',
  smtp_host: '',
  smtp_port: 587,
  smtp_username: '',
  smtp_password: '',
  use_tls: true,
  use_ssl: false,
}

const adminHeaders = (isAdmin) =>
  isAdmin
    ? {
        'Content-Type': 'application/json',
        'X-Admin-Mode': 'true',
      }
    : { 'Content-Type': 'application/json' }

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
    <div className="min-h-screen bg-slate-950 text-slate-100 dark:bg-slate-950">
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

function SkeletonInput() {
  return <div className="h-10 animate-pulse rounded-xl border border-slate-800 bg-slate-900" />
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

function SettingsPage({ isAdmin }) {
  const [form, setForm] = useState(defaultEmailSettings)
  const [hasPassword, setHasPassword] = useState(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    const fetchSettings = async () => {
      setLoading(true)
      setError('')
      try {
        const response = await fetch('/api/admin/email-settings', {
          headers: adminHeaders(isAdmin),
        })
        if (!response.ok) {
          const errorBody = await response.json().catch(() => null)
          throw new Error(errorBody?.error?.message ?? 'メール設定の取得に失敗しました。')
        }
        const json = await response.json()
        const settings = json.email_settings ?? {}
        setForm((prev) => ({
          ...prev,
          sender_name: settings.sender_name ?? '',
          sender_email: settings.sender_email ?? '',
          smtp_host: settings.smtp_host ?? '',
          smtp_port: settings.smtp_port ?? 587,
          smtp_username: settings.smtp_username ?? '',
          use_tls: Boolean(settings.use_tls),
          use_ssl: Boolean(settings.use_ssl),
          smtp_password: '',
        }))
        setHasPassword(Boolean(settings.has_smtp_password))
      } catch (err) {
        setError(err instanceof Error ? err.message : '不明なエラーが発生しました。')
      } finally {
        setLoading(false)
      }
    }

    if (isAdmin) fetchSettings()
  }, [isAdmin])

  const validate = () => {
    if (!form.sender_name.trim()) return '送信元名は必須です。'
    if (!form.sender_email.includes('@')) return '送信元メールアドレスの形式が不正です。'
    if (!form.smtp_host.trim()) return 'SMTPホストは必須です。'
    if (!Number.isInteger(Number(form.smtp_port)) || Number(form.smtp_port) < 1 || Number(form.smtp_port) > 65535) {
      return 'SMTPポートは1〜65535の整数で入力してください。'
    }
    if (!form.smtp_username.trim()) return 'SMTPユーザー名は必須です。'
    if (form.use_tls && form.use_ssl) return 'TLSとSSLを同時に有効化できません。'
    return ''
  }

  const onSave = async () => {
    setSuccess('')
    const validationError = validate()
    if (validationError) {
      setError(validationError)
      return
    }

    setSaving(true)
    setError('')
    try {
      const payload = {
        sender_name: form.sender_name.trim(),
        sender_email: form.sender_email.trim(),
        smtp_host: form.smtp_host.trim(),
        smtp_port: Number(form.smtp_port),
        smtp_username: form.smtp_username.trim(),
        smtp_password: form.smtp_password,
        use_tls: form.use_tls,
        use_ssl: form.use_ssl,
      }

      const response = await fetch('/api/admin/email-settings', {
        method: 'PUT',
        headers: adminHeaders(isAdmin),
        body: JSON.stringify(payload),
      })
      if (!response.ok) {
        const errorBody = await response.json().catch(() => null)
        throw new Error(errorBody?.error?.message ?? 'メール設定の保存に失敗しました。')
      }

      const json = await response.json()
      const passwordUpdated = Boolean(json.meta?.password_updated)
      if (passwordUpdated) {
        setForm((prev) => ({ ...prev, smtp_password: '' }))
      }
      setHasPassword(Boolean(json.email_settings?.has_smtp_password))
      setSuccess('メール設定を保存しました。')
    } catch (err) {
      setError(err instanceof Error ? err.message : '不明なエラーが発生しました。')
    } finally {
      setSaving(false)
    }
  }

  const onFieldChange = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  if (loading) {
    return (
      <section className="space-y-4 rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
        <SkeletonInput />
        <SkeletonInput />
        <SkeletonInput />
        <SkeletonInput />
        <SkeletonInput />
      </section>
    )
  }

  return (
    <section className="space-y-5 pb-24">
      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
        <h2 className="text-lg font-semibold">メール設定</h2>
        <p className="mt-2 text-sm text-slate-400">OTP送信・通知メール送信の基盤となる SMTP 設定を管理します。</p>
      </div>

      {success && (
        <div className="rounded-xl border border-emerald-400/40 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">{success}</div>
      )}
      {error && <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">{error}</div>}

      <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
        <h3 className="text-base font-semibold">基本設定</h3>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <label className="space-y-2 text-sm">
            <span className="text-slate-300">送信元名</span>
            <input className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2" value={form.sender_name} onChange={(e) => onFieldChange('sender_name', e.target.value)} />
          </label>
          <label className="space-y-2 text-sm">
            <span className="text-slate-300">送信元メールアドレス</span>
            <input className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2" value={form.sender_email} onChange={(e) => onFieldChange('sender_email', e.target.value)} />
          </label>
        </div>
      </article>

      <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
        <h3 className="text-base font-semibold">SMTP接続設定</h3>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <label className="space-y-2 text-sm md:col-span-2">
            <span className="text-slate-300">SMTPホスト</span>
            <input className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2" value={form.smtp_host} onChange={(e) => onFieldChange('smtp_host', e.target.value)} />
          </label>
          <label className="space-y-2 text-sm">
            <span className="text-slate-300">SMTPポート</span>
            <input className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2" type="number" value={form.smtp_port} onChange={(e) => onFieldChange('smtp_port', e.target.value)} />
          </label>
          <label className="space-y-2 text-sm">
            <span className="text-slate-300">SMTPユーザー名</span>
            <input className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2" value={form.smtp_username} onChange={(e) => onFieldChange('smtp_username', e.target.value)} />
          </label>
        </div>
      </article>

      <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
        <h3 className="text-base font-semibold">セキュリティ関連</h3>
        <p className="mt-2 text-xs text-slate-400">
          保存済みパスワードは再表示されません。変更時のみ新しい値を入力してください。{hasPassword ? '（保存済み）' : '（未保存）'}
        </p>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <label className="space-y-2 text-sm md:col-span-2">
            <span className="text-slate-300">SMTPパスワード</span>
            <div className="flex gap-2">
              <input
                className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2"
                type={showPassword ? 'text' : 'password'}
                value={form.smtp_password}
                onChange={(e) => onFieldChange('smtp_password', e.target.value)}
                placeholder={hasPassword ? '******** (変更する場合のみ入力)' : '新しいパスワードを入力'}
              />
              <button
                className="rounded-xl border border-slate-700 px-3 py-2 text-sm hover:bg-slate-800"
                type="button"
                onClick={() => setShowPassword((prev) => !prev)}
              >
                {showPassword ? '隠す' : '表示'}
              </button>
            </div>
          </label>

          <label className="flex items-center gap-2 rounded-xl border border-slate-800 px-3 py-2 text-sm">
            <input type="checkbox" checked={form.use_tls} onChange={(e) => onFieldChange('use_tls', e.target.checked)} />
            STARTTLSを使用する
          </label>
          <label className="flex items-center gap-2 rounded-xl border border-slate-800 px-3 py-2 text-sm">
            <input type="checkbox" checked={form.use_ssl} onChange={(e) => onFieldChange('use_ssl', e.target.checked)} />
            SSL/TLSを使用する
          </label>
        </div>
      </article>

      <div className="fixed bottom-4 right-4 left-4 md:left-auto md:w-[420px]">
        <div className="rounded-2xl border border-cyan-500/40 bg-slate-900/95 p-3 shadow-2xl backdrop-blur">
          <button
            className="w-full rounded-xl bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:opacity-60"
            type="button"
            disabled={saving}
            onClick={onSave}
          >
            {saving ? '保存中...' : 'メール設定を保存'}
          </button>
        </div>
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
    if (path === '/admin/settings' || path === '/admin/settings/email') return <SettingsPage isAdmin={isAdmin} />
    return (
      <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 text-sm text-slate-300">
        ページが見つかりません。<button className="ml-2 underline" onClick={() => moveTo('/admin')}>/admin に戻る</button>
      </section>
    )
  }, [loading, moveTo, overview, path, quizzes, users, isAdmin])

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
