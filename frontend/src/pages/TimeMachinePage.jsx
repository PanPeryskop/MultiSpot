import { useState } from 'react'
import { Clock, Loader2 } from 'lucide-react'
import { ToastContext } from '../toast'
import { api } from '../api'
import ResultCard from '../components/ResultCard'
import styles from './FeaturePage.module.css'

const DECADES = [1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020]

export default function TimeMachinePage() {
  const [decade, setDecade] = useState(1990)
  const [count, setCount] = useState(10)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const submit = async () => {
    setLoading(true)
    setResult(null)
    try {
      const d = await api('/api/time-machine', { method: 'POST', body: { decade, count } })
      setResult({ ...d, decade })
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
        <p className={styles.subtitle}>Pick a decade and we will queue up popular tracks released in that era, max two per artist. Needs an active Spotify device.</p>
      </header>
      <div className={styles.form}>
        <div className={styles.field}>
          <label className="label">Decade</label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {DECADES.map(d => (
              <button
                key={d}
                type="button"
                className={`btn ${d === decade ? 'btn-primary' : 'btn-ghost'}`}
                style={{ transform: d === decade ? 'translate(-2px,-2px)' : 'none' }}
                onClick={() => setDecade(d)}
              >
                {String(d).slice(2)}s
              </button>
            ))}
          </div>
        </div>
        <div className={styles.field}>
          <label className="label">Tracks to Queue ({count})</label>
          <div className={styles.sliderContainer}>
            <input type="range" min="1" max="50" value={count} onChange={e => setCount(Number(e.target.value))} className={styles.slider} />
            <span className={styles.sliderValue}>{count}</span>
          </div>
        </div>
        <button className="btn btn-primary" onClick={submit} disabled={loading} style={{ alignSelf: 'flex-start' }}>
          {loading ? <Loader2 size={18} className="spin" /> : <Clock size={18} />}
          {loading ? 'Traveling…' : 'Start Time Machine'}
        </button>
      </div>
      {result && (
        <ResultCard title="Time Travel Complete" tracks={result.tracks} total={result.added} accent="var(--yellow)">
          Queued <strong>{result.added}</strong> tracks from the {result.decade}s{result.errors > 0 && `, ${result.errors} skipped`}.
        </ResultCard>
      )}
    </main>
  )
}
