import { useEffect, useState } from 'react'
import { Bot, Loader2, Play, Trash2, ExternalLink, Sunrise, Radar, CalendarHeart } from 'lucide-react'
import { ToastContext } from '../toast'
import { api } from '../api'
import featureStyles from './FeaturePage.module.css'
import styles from './NewFeatures.module.css'

const ICONS = { daily_mix: Sunrise, weekly_radar: Radar, monthly_rewind: CalendarHeart }
const ACCENTS = { daily_mix: '#00b4d8', weekly_radar: '#ff8a3d', monthly_rewind: '#9b8cff' }

function when(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString(undefined, { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}

export default function AutopilotPage() {
  const [data, setData] = useState(null)
  const [busy, setBusy] = useState({})

  useEffect(() => {
    let alive = true
    api('/api/autopilot')
      .then(d => alive && setData(d))
      .catch(e => alive && ToastContext.push(e.message, 'error'))
    return () => { alive = false }
  }, [])

  const replace = (item) => setData(d => ({ ...d, automations: d.automations.map(a => (a.id === item.id ? item : a)) }))
  const mark = (key, value) => setBusy(b => ({ ...b, [key]: value }))

  const create = async (kind) => {
    mark(kind, true)
    try {
      const item = await api('/api/autopilot', { method: 'POST', body: { kind } })
      setData(d => ({ ...d, automations: [...d.automations, item] }))
      ToastContext.push(`${item.label} is on. First playlist is ready.`, 'success')
    } catch (e) {
      ToastContext.push(e.message, 'error')
    } finally {
      mark(kind, false)
    }
  }

  const runNow = async (item) => {
    mark(item.id, true)
    try {
      const updated = await api(`/api/autopilot/${item.id}/run`, { method: 'POST' })
      replace(updated)
      ToastContext.push(updated.last_status || 'Done', 'success')
    } catch (e) {
      ToastContext.push(e.message, 'error')
    } finally {
      mark(item.id, false)
    }
  }

  const toggle = async (item) => {
    try {
      replace(await api(`/api/autopilot/${item.id}`, { method: 'PATCH', body: { enabled: !item.enabled } }))
    } catch (e) {
      ToastContext.push(e.message, 'error')
    }
  }

  const remove = async (item) => {
    try {
      await api(`/api/autopilot/${item.id}`, { method: 'DELETE' })
      setData(d => ({ ...d, automations: d.automations.filter(a => a.id !== item.id) }))
      ToastContext.push('Autopilot removed. The playlist stays in your library.', 'info')
    } catch (e) {
      ToastContext.push(e.message, 'error')
    }
  }

  const active = data?.automations || []
  const available = (data?.kinds || []).filter(k => !active.some(a => a.kind === k.kind))

  return (
    <main className={`${featureStyles.page} page-enter`} style={{ maxWidth: 1000 }}>
      <header className={featureStyles.header}>
        <h1 className={featureStyles.title}>Autopilot</h1>
        <p className={featureStyles.subtitle}>Playlists that keep themselves fresh. MultiSpot refreshes them on schedule, even when the app is closed.</p>
      </header>

      {!data ? (
        <div className={styles.scanning}><Loader2 size={32} className="spin" /></div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
          {active.length > 0 && (
            <section className="stagger" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {active.map(item => {
                const Icon = ICONS[item.kind] || Bot
                return (
                  <div key={item.id} className={`${styles.pilot} ${item.enabled ? '' : styles.pilotOff}`} style={{ '--accent': ACCENTS[item.kind] }}>
                    <div className={styles.pilotIcon}><Icon size={24} /></div>
                    <div className={styles.pilotBody}>
                      <div className={styles.pilotHead}>
                        <h3>{item.settings?.name || item.label}</h3>
                        <button className={`${styles.switch} ${item.enabled ? styles.switchOn : ''}`} onClick={() => toggle(item)} aria-label="Toggle autopilot">
                          <span />
                        </button>
                      </div>
                      <p className={styles.pilotDesc}>{item.schedule}{item.enabled ? ` · next ${when(item.next_run)}` : ' · paused'}</p>
                      <p className={styles.pilotStatus}>Last run {when(item.last_run)}{item.last_status ? ` — ${item.last_status}` : ''}</p>
                      <div className={styles.pilotActions}>
                        <button className="btn btn-ghost" onClick={() => runNow(item)} disabled={busy[item.id]}>
                          {busy[item.id] ? <Loader2 size={16} className="spin" /> : <Play size={16} />} Run now
                        </button>
                        {item.playlist_url && (
                          <a className="btn btn-ghost" href={item.playlist_url} target="_blank" rel="noreferrer"><ExternalLink size={16} /> Open</a>
                        )}
                        <button className="btn btn-ghost" onClick={() => remove(item)}><Trash2 size={16} /></button>
                      </div>
                    </div>
                  </div>
                )
              })}
            </section>
          )}

          {available.length > 0 && (
            <section>
              <h3 className="label" style={{ marginBottom: 16 }}>Add an autopilot</h3>
              <div className={`${styles.pilotGrid} stagger`}>
                {available.map(k => {
                  const Icon = ICONS[k.kind] || Bot
                  return (
                    <button key={k.kind} className={styles.pilotCard} style={{ '--accent': ACCENTS[k.kind] }} onClick={() => create(k.kind)} disabled={busy[k.kind]}>
                      <div className={styles.pilotIcon}>{busy[k.kind] ? <Loader2 size={24} className="spin" /> : <Icon size={24} />}</div>
                      <strong>{k.label}</strong>
                      <span>{k.description}</span>
                      <small>{k.schedule}</small>
                    </button>
                  )
                })}
              </div>
            </section>
          )}
        </div>
      )}
    </main>
  )
}
