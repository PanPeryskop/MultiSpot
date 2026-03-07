import { useState } from 'react'
import { ListMusic, Loader2, X } from 'lucide-react'
import { ToastContext } from '../App'
import PlaylistPicker from '../components/PlaylistPicker'
import featureStyles from './FeaturePage.module.css'
import styles from './QueueSetterPage.module.css'

export default function QueueSetterPage() {
  const [selected, setSelected] = useState([])
  const [manualUrl, setManualUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const submit = async () => {
    setLoading(true)
    setResult(null)
    
    const urlsToQueue = selected.map(p => p.url)
    if (manualUrl.trim()) {
      const parsedUrls = manualUrl.split(/[\s,]+/).filter(u => u.includes('spotify.com/playlist/'))
      urlsToQueue.push(...parsedUrls)
    }

    if (urlsToQueue.length < 2) {
      ToastContext.push('Please select at least 2 playlists', 'error')
      setLoading(false)
      return
    }

    try {
      const r = await fetch('/api/queue-setter', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ playlist_urls: urlsToQueue }),
      })
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || 'Something went wrong')
      setResult(d)
      ToastContext.push(`Queued ${d.queued} tracks!`, 'success')
      setSelected([])
      setManualUrl('')
    } catch (e) {
      ToastContext.push(e.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  const remove = (url) => setSelected(prev => prev.filter(p => p.url !== url))

  return (
    <main className={`${featureStyles.page} page-enter`}>
      <header className={featureStyles.header}>
        <h1 className={featureStyles.title}>Queue Setter</h1>
        <p className={featureStyles.subtitle}>Select multiple playlists. We'll interleave them, alternating tracks from each playlist, and inject them into your queue.</p>
      </header>

      <div className={featureStyles.form}>
        <div className={featureStyles.field}>
          <label className="label">Manual Playlist URLs (Comma separated)</label>
          <input
            className="input"
            type="text"
            placeholder="https://open.spotify.com/playlist/..."
            value={manualUrl}
            onChange={e => setManualUrl(e.target.value)}
          />
        </div>
        
        <div style={{ textAlign: 'center', fontWeight: 'bold', fontSize: 13, margin: '8px 0', color: 'var(--text-secondary)' }}>AND / OR</div>

        <div className={featureStyles.field}>
          <label className="label">Select 2+ Playlists</label>
          <PlaylistPicker 
            multi={true} 
            selected={selected} 
            onChange={setSelected} 
          />
        </div>

        {selected.length > 0 && (
          <div className="slide-up">
            <label className="label" style={{ marginBottom: 12 }}>Currently Selected ({selected.length})</label>
            <div className={styles.selectedList}>
              {selected.map(pl => (
                <div key={pl.url} className={styles.selectedItem}>
                  <div className={styles.itemInfo}>
                    {pl.image ? <img src={pl.image} alt="" className={styles.itemImage} /> : <div className={styles.itemPlaceholder} />}
                    <span className={styles.itemName}>{pl.name}</span>
                  </div>
                  <button className={`btn-icon ${styles.removeBtn}`} onClick={() => remove(pl.url)}>
                    <X size={16} />
                  </button>
                </div>
              ))}
            </div>

            <button
              className="btn btn-primary"
              onClick={submit}
              disabled={loading}
            >
              {loading ? <Loader2 size={18} className="spin" /> : <ListMusic size={18} />}
              {loading ? 'Setting queue…' : 'Set Interleaved Queue'}
            </button>
          </div>
        )}
        {selected.length === 0 && (
          <button
            className="btn btn-primary"
            onClick={submit}
            disabled={loading || !manualUrl.trim()}
          >
            {loading ? <Loader2 size={18} className="spin" /> : <ListMusic size={18} />}
            {loading ? 'Setting queue…' : 'Set Interleaved Queue'}
          </button>
        )}
      </div>

      {result && (
        <div className={`${featureStyles.result} slide-up`}>
          <h2 className={featureStyles.resultTitle}>Queue Set</h2>
          <p style={{ color: 'var(--text-secondary)' }}>Successfully interleaved <strong style={{color:'var(--text)'}}>{result.queued}</strong> tracks into your up-next queue.</p>
        </div>
      )}
    </main>
  )
}
