import { ArrowDownToLine, ArrowUp, Command, LoaderCircle, Moon, Plus, Sun, WandSparkles } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { apiRequest, ApiError } from './lib/api'
import { useTheme } from './hooks/useTheme'
import type { ThemePreference } from './hooks/useTheme'

type GenerationRun = {
  id: number
  prompt: string
  status: 'queued' | 'running' | 'completed' | 'failed'
  project_name: string | null
  result: {
    file_count?: number
    validation?: { success?: boolean; attempts?: number; report?: Record<string, unknown> }
    tests?: { status?: string; reason?: string }
  } | null
  error_message: string | null
  created_at: string
  updated_at: string
}

function App() {
  const [runs, setRuns] = useState<GenerationRun[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [prompt, setPrompt] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [showApiKey, setShowApiKey] = useState(false)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [newBuild, setNewBuild] = useState(false)
  const { preference, setPreference } = useTheme()

  const refreshRuns = useCallback(async () => {
    try {
      const currentRuns = await apiRequest<GenerationRun[]>('/generation-runs')
      setRuns(currentRuns)
      setSelectedId((current) => current ?? currentRuns[0]?.id ?? null)
      setError('')
    } catch (reason) {
      setError(messageFor(reason))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void refreshRuns()
  }, [refreshRuns])

  const hasActiveRuns = runs.some((run) => run.status === 'queued' || run.status === 'running')

  useEffect(() => {
    if (!hasActiveRuns) return
    const timer = window.setInterval(() => void refreshRuns(), 2500)
    return () => window.clearInterval(timer)
  }, [hasActiveRuns, refreshRuns])

  const selectedRun = useMemo(
    () => newBuild ? null : runs.find((run) => run.id === selectedId) ?? null,
    [newBuild, runs, selectedId],
  )

  async function startGeneration() {
    const trimmedPrompt = prompt.trim()
    if (trimmedPrompt.length < 10 || submitting) return

    setSubmitting(true)
    setError('')
    try {
      const trimmedApiKey = apiKey.trim()
      const run = await apiRequest<GenerationRun>('/generation-runs', {
        method: 'POST',
        body: JSON.stringify({ prompt: trimmedPrompt }),
        headers: trimmedApiKey ? { 'X-OpenAI-API-Key': trimmedApiKey } : undefined,
      })
      setPrompt('')
      setApiKey('')
      setRuns((current) => [run, ...current.filter((item) => item.id !== run.id)])
      setSelectedId(run.id)
      setNewBuild(false)
      void refreshRuns()
    } catch (reason) {
      setError(messageFor(reason))
    } finally {
      setApiKey('')
      setSubmitting(false)
    }
  }

  function startNew() {
    setPrompt('')
    setApiKey('')
    setShowApiKey(false)
    setSelectedId(null)
    setNewBuild(true)
    setError('')
  }

  function toggleTheme() {
    const next: ThemePreference = preference === 'dark' ? 'light' : 'dark'
    setPreference(next)
  }

  return (
    <div className="simple-app">
      <aside className="history-sidebar">
        <div className="simple-brand">
          <span className="simple-brand-icon"><Command size={17} /></span>
          <span>Personal CTO</span>
        </div>
        <button className="new-build-button" onClick={startNew}>
          <Plus size={16} /> New app
        </button>
        <div className="history-title">History <span>{runs.length}</span></div>
        <div className="history-list">
          {loading && runs.length === 0 ? (
            <div className="history-placeholder">Loading history…</div>
          ) : runs.length === 0 ? (
            <div className="history-placeholder">Your app builds will appear here.</div>
          ) : runs.map((run) => (
            <button
              key={run.id}
              className={`history-item ${selectedId === run.id ? 'history-item-active' : ''}`}
              onClick={() => {
                setSelectedId(run.id)
                setNewBuild(false)
                setPrompt('')
                setApiKey('')
                setShowApiKey(false)
              }}
            >
              <span className={`history-status history-status-${run.status}`} />
              <span className="history-item-copy">
                <span>{run.prompt}</span>
                <small>{formatDate(run.created_at)} · {statusLabel(run.status)}</small>
              </span>
            </button>
          ))}
        </div>
        <div className="history-sidebar-footer">
          <span>Local workspace</span>
          <button className="theme-toggle" onClick={toggleTheme} aria-label={`Switch to ${preference === 'dark' ? 'light' : 'dark'} theme`}>
            {preference === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
          </button>
        </div>
      </aside>

      <main className="chat-main">
        <header className="chat-header">
          <span>App builder</span>
          <span className="backend-indicator">Local API</span>
        </header>

        <section className="chat-content">
          {selectedRun ? (
            <RunDetails run={selectedRun} />
          ) : (
            <div className="welcome">
              <div className="welcome-symbol"><WandSparkles size={23} /></div>
              <p className="welcome-kicker">YOUR IDEA, BUILT</p>
              <h1>What do you want to create?</h1>
              <p className="welcome-description">Describe the app you have in mind. Your generated project and past builds will be kept in this workspace.</p>
              <PromptForm
                prompt={prompt}
                setPrompt={setPrompt}
                apiKey={apiKey}
                setApiKey={setApiKey}
                showApiKey={showApiKey}
                setShowApiKey={setShowApiKey}
                onSubmit={() => void startGeneration()}
                submitting={submitting}
                error={error}
              />
              <p className="privacy-hint">Be specific about the features, users, and technology you want.</p>
            </div>
          )}
        </section>
        <footer className="chat-footer">Generated code is saved locally on the backend. Review it before running in production.</footer>
      </main>
    </div>
  )
}

function PromptForm({
  prompt,
  setPrompt,
  apiKey,
  setApiKey,
  showApiKey,
  setShowApiKey,
  onSubmit,
  submitting,
  error,
}: {
  prompt: string
  setPrompt: (value: string) => void
  apiKey: string
  setApiKey: (value: string) => void
  showApiKey: boolean
  setShowApiKey: (value: boolean) => void
  onSubmit: () => void
  submitting: boolean
  error: string
}) {
  return (
    <div className="prompt-wrap">
      <label className="sr-only" htmlFor="app-prompt">Describe the app you want to build</label>
      <textarea
        id="app-prompt"
        value={prompt}
        onChange={(event) => setPrompt(event.target.value.slice(0, 8000))}
        onKeyDown={(event) => {
          if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault()
            onSubmit()
          }
        }}
        placeholder="I want to build an app that…"
        rows={4}
        maxLength={8000}
      />
      <details className="api-key-section">
        <summary>OpenAI API key <span>Optional</span></summary>
        <label htmlFor="openai-api-key">Use your key for this generation only</label>
        <div className="api-key-input-wrap">
          <input
            id="openai-api-key"
            type={showApiKey ? 'text' : 'password'}
            value={apiKey}
            onChange={(event) => setApiKey(event.target.value)}
            placeholder="Leave blank to use the backend key"
            maxLength={512}
            autoComplete="off"
            spellCheck={false}
          />
          <button
            type="button"
            className="api-key-visibility"
            aria-label={showApiKey ? 'Hide OpenAI API key' : 'Show OpenAI API key'}
            onClick={() => setShowApiKey(!showApiKey)}
          >
            {showApiKey ? 'Hide' : 'Show'}
          </button>
        </div>
        <p className="api-key-note">Sent only with this request. It is not saved in browser storage or build history.</p>
      </details>
      {error && <p className="inline-error" role="alert">{error}</p>}
      <div className="prompt-controls">
        <span>Describe your app · {prompt.length}/8000</span>
        <button
          className="submit-prompt"
          onClick={onSubmit}
          disabled={submitting || prompt.trim().length < 10}
        >
          {submitting ? <LoaderCircle size={15} className="spin" /> : <ArrowUp size={16} />}
          <span>{submitting ? 'Starting…' : 'Start creating'}</span>
        </button>
      </div>
    </div>
  )
}

function RunDetails({ run }: { run: GenerationRun }) {
  const isActive = run.status === 'queued' || run.status === 'running'

  return (
    <div className="run-details">
      <div className="run-message">
        <span className="user-avatar">You</span>
        <div><small>Your app idea</small><p>{run.prompt}</p></div>
      </div>

      {isActive ? (
        <div className="run-progress">
          <span className="progress-icon"><LoaderCircle size={18} className="spin" /></span>
          <div><strong>{run.status === 'queued' ? 'Waiting to start' : 'Creating your app'}</strong><p>The AI is generating project files and checking the project structure. This may take a few minutes.</p></div>
        </div>
      ) : run.status === 'failed' ? (
        <div className="run-failure" role="alert">
          <strong>Couldn’t complete this build</strong>
          <p>{run.error_message || 'The generation failed. You can try again with a revised description.'}</p>
        </div>
      ) : (
        <div className="run-complete">
          <div className="complete-heading">
            <span className="complete-check">✓</span>
            <div><strong>Your project is ready</strong><p>{run.project_name} · {run.result?.file_count ?? 0} files</p></div>
          </div>
          <div className="quality-summary">
            <div><span>Validation</span><strong className={run.result?.validation?.success ? 'quality-pass' : 'quality-review'}>{run.result?.validation?.success ? 'Passed' : 'Needs review'}</strong></div>
            <div><span>Tests</span><strong className="quality-review">Not run</strong></div>
          </div>
          <p className="test-note">Generated tests are included in the project but aren’t run automatically.</p>
          <a className="download-project" href={`/api/generation-runs/${run.id}/download`}>
            <ArrowDownToLine size={17} /> Download project ZIP
          </a>
        </div>
      )}
    </div>
  )
}

function formatDate(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.valueOf())) return 'Recently'
  return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }).format(date)
}

function statusLabel(status: GenerationRun['status']) {
  if (status === 'queued') return 'queued'
  if (status === 'running') return 'building'
  if (status === 'completed') return 'ready'
  return 'failed'
}

function messageFor(reason: unknown) {
  if (reason instanceof ApiError && reason.status === 404) return 'The generation API was not found. Restart the backend to load the new endpoint.'
  if (reason instanceof Error) return reason.message
  return 'Something went wrong. Please try again.'
}

export default App
