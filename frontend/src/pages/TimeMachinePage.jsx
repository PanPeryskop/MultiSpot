import { useState } from 'react'
import { Clock, Loader2, Music2 } from 'lucide-react'
import { ToastContext } from '../App'
import styles from './FeaturePage.module.css'

export default function TimeMachinePage() {
  const [decade, setDecade] = useState(1990)
  const [count, setCount] = useState(10)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const submit = async () => {
    setLoading(true)
    setResult(null)
    try {
      const r = await fetch('/api/time-machine', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decade: parseInt(decade), count: parseInt(count) }),
      })
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || 'Something went wrong')
      setResult(d)
      ToastContext.push(`Added ${d.added} tracks from the ${decade}s!`, 'success')
    } catch (e) {
      ToastContext.push(e.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className={`${styles.page} page-enter`}>
      <header className={styles.header}>
        <h1 className={styles.title}>Time Machine</h1>
        <p className={styles.subtitle}>Travel back in time. Pick a decade, and we'll queue up random popular tracks from that era directly into your player.</p>
      </header>
      <div className={styles.form}>
        <div className={styles.field}>
          <label className="label">Decade</label>
          <select className="input" value={decade} onChange={e => setDecade(e.target.value)}>
            <option value={1950}>1950s</option>
            <option value={1960}>1960s</option>
            <option value={1970}>1970s</option>
            <option value={1980}>1980s</option>
            <option value={1990}>1990s</option>
            <option value={2000}>2000s</option>
            <option value={2010}>2010s</option>
            <option value={2020}>2020s</option>
          </select>
        </div>
        <div className={styles.field}>
          <label className="label">Track Count (1-100)</label>
          <input
            className="input"
            type="number"
            min="1"
            max="100"
            value={count}
            onChange={e => setCount(e.target.value)}
          />
        </div>
        <button className="btn btn-primary" onClick={submit} disabled={loading} style={{ alignSelf: 'flex-start' }}>
          {loading ? <Loader2 size={18} className="spin" /> : <Clock size={18} />}
          {loading ? 'Traveling…' : 'Start Time Machine'}
        </button>
      </div>
      {result && (
        <div className={`${styles.result} slide-up`}>
          <h2 className={styles.resultTitle}>Time Travel Complete</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: 24 }}>Successfully queued <strong style={{color:'var(--text)'}}>{result.added}</strong> tracks from the {decade}s.</p>
          <button className="btn btn-secondary" onClick={() => setResult(null)}>
            <Music2 size={18} /> Queue More
          </button>
        </div>
      )}
    </main>
  )
}
