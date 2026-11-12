import { ExternalLink } from 'lucide-react'
import styles from './ResultCard.module.css'

export default function ResultCard({ title, children, tracks = [], url, total, accent = 'var(--green)' }) {
  const rest = (total ?? tracks.length) - tracks.length
  return (
    <section className={`${styles.card} slide-up`} style={{ '--accent': accent }}>
      <h2 className={styles.title}>{title}</h2>
      {children && <div className={styles.body}>{children}</div>}
      {tracks.length > 0 && (
        <ol className={styles.list}>
          {tracks.map((t, i) => (
            <li key={`${t.id}-${i}`} className={styles.row} style={{ animationDelay: `${0.04 * i}s` }}>
              <span className={styles.index}>{String(i + 1).padStart(2, '0')}</span>
              {t.image ? <img src={t.image} alt="" className={styles.cover} loading="lazy" /> : <div className={styles.cover} />}
              <div className={styles.meta}>
                <div className={styles.name}>{t.name}</div>
                <div className={styles.artists}>{(t.artists || []).join(', ')}</div>
              </div>
            </li>
          ))}
        </ol>
      )}
      {rest > 0 && <p className={styles.more}>+ {rest} more tracks</p>}
      {url && (
        <a href={url} target="_blank" rel="noreferrer" className="btn btn-primary">
          <ExternalLink size={18} /> Open in Spotify
        </a>
      )}
    </section>
  )
}
