import { useState } from 'react'
import { ScanSearch, Loader2, Copy, Ban, Clock, Users, Disc3, CalendarRange, Flame } from 'lucide-react'
import { ToastContext } from '../toast'
import { api, compact, formatDuration, isSpotifyLink } from '../api'
import PlaylistPicker from '../components/PlaylistPicker'
import featureStyles from './FeaturePage.module.css'
import styles from './NewFeatures.module.css'

function Bars({ items, labelKey, accent }) {
  const top = Math.max(1, ...items.map(i => i.count))
  return (
    <div className={styles.bars}>
      {items.map((item, i) => (
        <div key={item[labelKey]} className={styles.barRow}>
          <span className={styles.barLabel}>{item[labelKey]}</span>
          <div className={styles.barTrack}>
            <div className={styles.barFill} style={{ width: `${(item.count / top) * 100}%`, background: accent, animationDelay: `${i * 0.05}s` }} />
          </div>
          <span className={styles.barValue}>{item.count}</span>
        </div>
      ))}
    </div>
  )
}

function TrackLine({ t, extra }) {
  return (
    <a href={t.url} target="_blank" rel="noreferrer" className={styles.trackLine}>
      {t.image ? <img src={t.image} alt="" loading="lazy" /> : <div className={styles.thumb} />}
      <div className={styles.trackMeta}>
        <span>{t.name}</span>
        <small>{t.artists.join(', ')}</small>
      </div>
      {extra && <span className={styles.trackExtra}>{extra}</span>}
    </a>
  )
}

export default function PlaylistXrayPage() {
  const [selected, setSelected] = useState(null)
  const [manual, setManual] = useState('')
  const [loading, setLoading] = useState(false)
  const [report, setReport] = useState(null)

  const scan = async (url) => {
    if (!isSpotifyLink(url, 'playlist')) {
      ToastContext.push('Pick a playlist or paste a playlist link', 'error')
      return
    }
    setLoading(true)
    setReport(null)
    try {
      setReport(await api(`/api/playlist-xray?playlist_url=${encodeURIComponent(url)}`))
    } catch (e) {
      ToastContext.push(e.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  const target = manual.trim() || selected?.url
  const p = report?.playlist
  const t = report?.totals

  return (
    <main className={`${featureStyles.page} page-enter`} style={{ maxWidth: 1000 }}>
      <header className={featureStyles.header}>
        <h1 className={featureStyles.title}>Playlist X-Ray</h1>
        <p className={featureStyles.subtitle}>Everything inside a playlist: who dominates it, which decades it lives in, duplicates and tracks you can no longer play. Read only, nothing gets changed.</p>
      </header>

      <div className={featureStyles.form}>
        <div className={featureStyles.field}>
          <label className="label">Playlist link</label>
          <input className="input" placeholder="https://open.spotify.com/playlist/..." value={manual} onChange={e => setManual(e.target.value)} />
        </div>
        <PlaylistPicker multi={false} selected={selected ? [selected] : []} onChange={v => { setSelected(v[0] || null); setManual('') }} />
        <button className="btn btn-primary" onClick={() => scan(target)} disabled={loading || !target} style={{ alignSelf: 'flex-start' }}>
          {loading ? <Loader2 size={18} className="spin" /> : <ScanSearch size={18} />}
          {loading ? 'Scanning…' : 'X-Ray Playlist'}
        </button>
      </div>

      {report && (
        <div className="slide-up" style={{ marginTop: 40, display: 'flex', flexDirection: 'column', gap: 24 }}>
          <a href={p.url} target="_blank" rel="noreferrer" className={styles.plHero}>
            {p.image ? <img src={p.image} alt="" /> : <div className={styles.thumb} />}
            <div>
              <div className="label">{p.collaborative ? 'Collaborative' : p.public ? 'Public' : 'Private'} playlist by {p.owner}</div>
              <h2>{p.name}</h2>
              {p.followers !== null && p.followers !== undefined && <small>{compact(p.followers)} followers</small>}
            </div>
          </a>

          <div className={styles.tiles}>
            <div className={styles.tile}><Disc3 size={18} /><strong>{t.tracks}</strong><span>tracks</span></div>
            <div className={styles.tile}><Clock size={18} /><strong>{formatDuration(t.duration_ms)}</strong><span>runtime</span></div>
            <div className={styles.tile}><Users size={18} /><strong>{t.artists}</strong><span>artists</span></div>
            <div className={styles.tile}><CalendarRange size={18} /><strong>{t.avg_year ?? '?'}</strong><span>avg year</span></div>
            {t.avg_popularity !== null && <div className={styles.tile}><Flame size={18} /><strong>{t.avg_popularity}</strong><span>avg popularity</span></div>}
            <div className={styles.tile}><strong>{t.explicit_pct}%</strong><span>explicit</span></div>
          </div>

          <div className={styles.columns}>
            <section className={styles.panel}>
              <h3>Who owns it</h3>
              <Bars items={report.top_artists.map(a => ({ ...a, label: `${a.name} · ${a.share}%` }))} labelKey="label" accent="var(--green)" />
            </section>
            <section className={styles.panel}>
              <h3>Decades</h3>
              <Bars items={report.decades} labelKey="decade" accent="var(--yellow)" />
              {report.added_by_year.length > 1 && (
                <>
                  <h3 style={{ marginTop: 20 }}>Added per year</h3>
                  <Bars items={report.added_by_year} labelKey="year" accent="var(--purple)" />
                </>
              )}
            </section>
          </div>

          <div className={styles.columns}>
            <section className={styles.panel}>
              <h3><Copy size={16} /> Duplicates ({report.duplicates.length})</h3>
              {report.duplicates.length === 0 ? <p className={styles.ok}>No duplicates. Clean.</p> : report.duplicates.map(d => <TrackLine key={d.id} t={d} extra={`×${d.count}${d.exact ? '' : ' versions'}`} />)}
            </section>
            <section className={styles.panel}>
              <h3><Ban size={16} /> Unavailable ({report.unavailable.length})</h3>
              {report.unavailable.length === 0 ? <p className={styles.ok}>Everything is playable in your country.</p> : report.unavailable.map(u => <TrackLine key={u.id} t={u} />)}
            </section>
          </div>

          <div className={styles.columns}>
            <section className={styles.panel}>
              <h3>Extremes</h3>
              {report.extremes.oldest && <TrackLine t={report.extremes.oldest} extra={`oldest · ${report.extremes.oldest.year}`} />}
              {report.extremes.newest && <TrackLine t={report.extremes.newest} extra={`newest · ${report.extremes.newest.year}`} />}
              {report.extremes.shortest && <TrackLine t={report.extremes.shortest} extra={formatDuration(report.extremes.shortest.duration_ms)} />}
              {report.extremes.longest && <TrackLine t={report.extremes.longest} extra={formatDuration(report.extremes.longest.duration_ms)} />}
            </section>
            {report.most_popular.length > 0 && (
              <section className={styles.panel}>
                <h3>Biggest hits</h3>
                {report.most_popular.map(m => <TrackLine key={m.id} t={m} extra={`★ ${m.popularity}`} />)}
                <h3 style={{ marginTop: 20 }}>Hidden gems</h3>
                {report.least_popular.map(m => <TrackLine key={m.id} t={m} extra={`★ ${m.popularity}`} />)}
              </section>
            )}
          </div>
        </div>
      )}
    </main>
  )
}
