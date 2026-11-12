import { useState, useEffect, useRef } from 'react'
import { Link2, Loader2, Plus, X, Search, CheckCircle2 } from 'lucide-react'
import { ToastContext } from '../toast'
import { api } from '../api'
import ResultCard from '../components/ResultCard'
import featureStyles from './FeaturePage.module.css'
import styles from './FusionCenterPage.module.css'
import PlaylistPicker from '../components/PlaylistPicker'

export default function FusionCenterPage() {
  const [urls, setUrls] = useState([''])
  const [playlistName, setPlaylistName] = useState('My Fusion Playlist')
  const [trackCount, setTrackCount] = useState(25)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState(null)
  const [isSearching, setIsSearching] = useState(false)
  
  const [suggestions, setSuggestions] = useState(null)
  const [loadingSuggestions, setLoadingSuggestions] = useState(true)

  const [selectedSeeds, setSelectedSeeds] = useState([])

  const searchTimeout = useRef(null)

  useEffect(() => {
    api('/api/fusion-suggestions')
      .then(d => setSuggestions(d))
      .catch(() => setSuggestions(null))
      .finally(() => setLoadingSuggestions(false))
  }, [])

  const handleAddUrl = () => {
    setUrls([...urls, ''])
  }
  const handleRemoveUrl = (index) => {
    setUrls(urls.filter((_, i) => i !== index))
  }
  const handleUrlChange = (index, value) => {
    const newUrls = [...urls]
    newUrls[index] = value
    setUrls(newUrls)
  }

  const handleSearchChange = (e) => {
    const text = e.target.value
    setSearchQuery(text)
    if (searchTimeout.current) clearTimeout(searchTimeout.current)

    if (text.trim().length === 0) {
      setSearchResults(null)
      setIsSearching(false)
      return
    }

    setIsSearching(true)
    searchTimeout.current = setTimeout(() => {
      fetchSearchResults(text)
    }, 500)
  }

  const fetchSearchResults = async (query) => {
    try {
      setSearchResults(await api(`/api/search?q=${encodeURIComponent(query)}&limit=10`))
    } catch (err) {
      ToastContext.push(err.message, 'error')
    } finally {
      setIsSearching(false)
    }
  }

  const toggleSeed = (item) => {
    setSelectedSeeds(prev => {
      const exists = prev.find(p => p.url === item.url)
      if (exists) {
        return prev.filter(p => p.url !== item.url)
      } else {
        return [...prev, item]
      }
    })
  }

  const generate = async () => {
    const validUrls = urls.filter(u => u.trim() !== '')
    const selectedUrls = selectedSeeds.map(s => s.url)
    const allUrlsToSeed = [...validUrls, ...selectedUrls]
    
    if (allUrlsToSeed.length === 0) {
      ToastContext.push('Please enter at least one link or select items from search.', 'error')
      return
    }
    if (!playlistName.trim()) {
      ToastContext.push('Please enter a playlist name.', 'error')
      return
    }

    setLoading(true)
    setResult(null)
    try {
      const data = await api('/api/fusion-center', {
        method: 'POST',
        body: { seed_urls: allUrlsToSeed, playlist_name: playlistName, track_count: trackCount },
      })
      setResult(data)
      ToastContext.push('Playlist generated successfully!', 'success')
    } catch (e) {
      ToastContext.push(e.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  const renderPanel = (title, items) => {
    if (!items || items.length === 0) return null
    return (
      <div className={styles.panel}>
        <h4 className={styles.panelHeader}>{title}</h4>
        <div className={styles.panelList}>
          {items.map(item => {
            const isSelected = selectedSeeds.some(s => s.url === item.url)
            return (
              <div 
                key={item.id} 
                onClick={() => toggleSeed(item)}
                className={`${styles.panelItem} ${isSelected ? styles.panelItemSelected : ''}`}
                style={{ background: isSelected ? 'var(--green-dim)' : 'transparent' }}
              >
                {item.image ? (
                  <img src={item.image} alt="" className={styles.panelImage} />
                ) : (
                  <div className={styles.panelImagePlaceholder} />
                )}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 14, fontWeight: 700, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{item.name}</div>
                  {item.artists && <div style={{ fontSize: 12, color: 'var(--text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{item.artists.join(', ')}</div>}
                </div>
                {isSelected && <CheckCircle2 size={18} color="var(--green)" />}
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  return (
    <main className={`${featureStyles.page} page-enter`} style={{ maxWidth: 1000 }}>
      <header className={featureStyles.header}>
        <h1 className={featureStyles.title}>Fusion Center</h1>
        <p className={featureStyles.subtitle}>
          Collect tracks, artists, albums or playlists as seeds. We find what their listeners play around them and favour songs that connect several seeds at once.
        </p>
      </header>

      <div className={featureStyles.form}>
      
        <div className={featureStyles.field} style={{ marginBottom: 32 }}>
           <label className="label">Search Catalog</label>
           <div style={{ display: 'flex', alignItems: 'center', position: 'relative' }}>
             <Search size={20} color="var(--text-secondary)" style={{ position: 'absolute', left: 16 }} />
             <input
               type="text"
               className="input"
               style={{ paddingLeft: 48, width: '100%', fontSize: 16 }}
               placeholder="Search for an artist, track, or album..."
               value={searchQuery}
               onChange={handleSearchChange}
             />
             {isSearching && <Loader2 size={18} className="spin" style={{ position: 'absolute', right: 16, color: 'var(--green)' }} />}
           </div>
           
           {searchResults && (
             <div className="slide-up" style={{ marginTop: 24 }}>
               <div className={styles.resultsGrid}>
                 {renderPanel('Artists', searchResults.artists)}
                 {renderPanel('Tracks', searchResults.tracks)}
                 {renderPanel('Albums', searchResults.albums)}
               </div>
             </div>
           )}

         {loadingSuggestions ? (
            <div className={styles.loadingBanner}>
              <Loader2 size={18} className="spin" color="var(--green)" /> 
              <span style={{ color: 'var(--text-secondary)' }}>Loading tactical suggestions...</span>
            </div>
         ) : suggestions ? (
            <div className="slide-up" style={{ marginTop: 24 }}>
              <h3 style={{ fontSize: 18, fontWeight: 800, marginBottom: 12 }}>Suggestions For You</h3>
              <div className={styles.resultsGrid}>
                {renderPanel('Top Artists', suggestions.top_artists)}
                {renderPanel('Top Tracks', suggestions.top_tracks)}
                {renderPanel('Recently Played', suggestions.recent_tracks)}
              </div>
            </div>
         ) : null}
         
         <div style={{ marginTop: 32 }}>
           <h3 style={{ fontSize: 18, fontWeight: 800, marginBottom: 12 }}>Your Playlists</h3>
           <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 12 }}>Pick a playlist and we use its main artists plus a couple of its tracks as seeds.</p>
           <PlaylistPicker 
             multi={true} 
             selected={selectedSeeds.filter(s => s.url?.includes('/playlist/'))} 
             onChange={v => {
                 const nonPlaylists = selectedSeeds.filter(s => !s.url?.includes('/playlist/'))
                 setSelectedSeeds([...nonPlaylists, ...v])
             }} 
           />
         </div>
      </div>

        {selectedSeeds.length > 0 && (
          <div className={`${featureStyles.field} ${styles.selectedSeedsContainer}`}>
            <label className="label" style={{ color: 'var(--green)' }}>Selected Seeds ({selectedSeeds.length})</label>
            <div className={styles.selectedSeedsGrid}>
              {selectedSeeds.map(item => (
                <div key={item.url} className={styles.seedItem}>
                   {item.image ? (
                    <img src={item.image} alt="" className={styles.seedItemImage} />
                  ) : (
                    <div className={styles.seedItemPlaceholder} />
                  )}
                  <span style={{ fontSize: 13, fontWeight: 600 }}>{item.name}</span>
                  <button className="btn" style={{ background: 'transparent', border: 'none', color: 'var(--text)', cursor: 'pointer', padding: 0, display: 'flex', minWidth: 'auto', minHeight: 'auto' }} onClick={() => toggleSeed(item)}>
                    <X size={14} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}


        <div className={featureStyles.field}>
          <label className="label">Or Paste Manual Links</label>
          <div className={styles.manualLinksContainer}>
            {urls.map((url, i) => (
              <div key={i} style={{ display: 'flex', gap: 12 }}>
                <input
                  type="text"
                  className="input"
                  style={{ flex: 1 }}
                  placeholder="https://open.spotify.com/..."
                  value={url}
                  onChange={(e) => handleUrlChange(i, e.target.value)}
                />
                {urls.length > 1 && (
                  <button className="btn" style={{ padding: '8px 12px' }} onClick={() => handleRemoveUrl(i)}>
                    <X size={16} />
                  </button>
                )}
              </div>
            ))}
          </div>
          <button className="btn" style={{ marginTop: 12, alignSelf: 'flex-start', fontSize: 13 }} onClick={handleAddUrl}>
            <Plus size={16} /> Add Another Link
          </button>
        </div>

        <div className={featureStyles.field}>
          <label className="label">New Playlist Name</label>
          <input
            type="text"
            className="input"
            value={playlistName}
            onChange={e => setPlaylistName(e.target.value)}
            placeholder="E.g. Brain Melt Fusion"
          />
        </div>

        <div className={featureStyles.field}>
          <label className="label">Length ({trackCount} Tracks)</label>
          <div className={featureStyles.sliderContainer}>
            <input
              type="range"
              min="5" max="100" step="5"
              value={trackCount}
              onChange={e => setTrackCount(Number(e.target.value))}
              className={featureStyles.slider}
            />
            <span className={featureStyles.sliderValue}>{trackCount}</span>
          </div>
        </div>

        <button className="btn btn-primary" onClick={generate} disabled={loading} style={{ marginTop: 16 }}>
          {loading ? <Loader2 size={18} className="spin" /> : <Link2 size={18} />}
          FUSE PLAYLIST
        </button>
      </div>

      {result && (
        <ResultCard title="Fusion Complete" tracks={result.tracks} total={result.track_count} url={result.playlist_url} accent="#00f5d4">
          Brewed <strong>{result.track_count}</strong> tracks from your seeds.
        </ResultCard>
      )}
    </main>
  )
}
