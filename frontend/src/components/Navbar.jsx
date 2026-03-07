import { useState, useEffect, useRef } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  Music2, Shuffle, ListMusic, Wand2, Radio, LayoutGrid,
  LogOut, ChevronRight, SkipForward
} from 'lucide-react'
import NowPlaying from './NowPlaying'
import NowPlayingModal from './NowPlayingModal'
import styles from './Navbar.module.css'

const NAV_LINKS = [
  { to: '/dashboard', icon: LayoutGrid, label: 'Dashboard' },
  { to: '/stats', icon: Radio, label: 'Stats Hub' },
  { to: '/fusion-center', icon: Wand2, label: 'Fusion Center' },
  { to: '/random-hub', icon: Shuffle, label: 'Random Hub' },
  { to: '/time-machine', icon: Music2, label: 'Time Machine' },
  { to: '/queue-setter', icon: ListMusic, label: 'Queue Setter' },
]

export default function Navbar({ user }) {
  const location = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)
  const [showPlayer, setShowPlayer] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setMenuOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  useEffect(() => setMenuOpen(false), [location.pathname])

  const handleLogout = async () => {
    try {
      await fetch('/auth/logout', { method: 'POST', credentials: 'include' })
    } catch (e) {
      console.error('Logout error:', e)
    }
    window.location.href = '/'
  }

  return (
    <>
      <nav className={styles.navbarDesktop}>
        <Link to="/dashboard" className={styles.logo}>
          <div className={styles.logoMark}>MS</div>
          <span>MultiSpot</span>
        </Link>
        <div className={styles.links}>
          {NAV_LINKS.slice(1).map(({ to, icon: Icon, label }) => (
            <Link key={to} to={to} className={`${styles.link} ${location.pathname === to ? styles.linkActive : ''}`}>
              <Icon size={15} />
              {label}
            </Link>
          ))}
        </div>
        <div className={styles.right} ref={ref}>
          <div className={styles.nowPlayingDesktop}>
            <button 
              onClick={() => setShowPlayer(true)} 
              style={{ background: 'transparent', border: 'none', padding: 0, margin: 0, textAlign: 'left', cursor: 'pointer' }}
            >
              <NowPlaying />
            </button>
          </div>
          <button className={styles.avatar} onClick={() => setMenuOpen(v => !v)}>
            {user.image ? <img src={user.image} alt={user.display_name} /> : <span>{(user.display_name || 'U')[0].toUpperCase()}</span>}
          </button>
          {menuOpen && (
            <div className={styles.dropdown}>
              <div className={styles.dropdownHeader}>
                <span className={styles.dropdownName}>{user.display_name}</span>
                <span className={styles.dropdownEmail}>{user.email}</span>
              </div>
              <div className={styles.dropdownDivider} />
              <button 
                onMouseDown={(e) => { e.preventDefault(); handleLogout(); }}
                className={styles.dropdownItem}
                style={{ background: 'transparent', border: 'none', width: '100%', textAlign: 'left', cursor: 'pointer', fontFamily: 'inherit', pointerEvents: 'auto', zIndex: 999 }}
              >
                <LogOut size={15} />
                Logout
              </button>
            </div>
          )}
        </div>
      </nav>

      <nav className={styles.navbarMobileTop}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', padding: '0 16px', height: '56px' }}>
          <Link to="/dashboard" className={styles.logo}>
            <div className={styles.logoMark}>MS</div>
          </Link>
          <div style={{ flex: 1, padding: '0 12px' }}>
            <button 
              onClick={() => setShowPlayer(true)} 
              style={{ background: 'transparent', border: 'none', padding: 0, margin: 0, width: '100%', textAlign: 'left', cursor: 'pointer' }}
            >
              <NowPlaying />
            </button>
          </div>
          <div className={styles.right} ref={ref}>
            <button className={styles.avatar} onClick={() => setMenuOpen(v => !v)}>
              {user.image ? <img src={user.image} alt={user.display_name} /> : <span>{(user.display_name || 'U')[0].toUpperCase()}</span>}
            </button>
            {menuOpen && (
              <div className={styles.dropdown}>
                <div className={styles.dropdownHeader}>
                  <span className={styles.dropdownName}>{user.display_name}</span>
                </div>
                <button 
                  onMouseDown={(e) => { e.preventDefault(); handleLogout(); }}
                  className={styles.dropdownItem}
                  style={{ background: 'transparent', border: 'none', width: '100%', textAlign: 'left', cursor: 'pointer', fontFamily: 'inherit', pointerEvents: 'auto', zIndex: 999 }}
                >
                  <LogOut size={15} />Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </nav>

      <nav className={styles.navbarMobileBottom}>
        <div className={styles.mobileLinks}>
          {NAV_LINKS.slice(0, 5).map(({ to, icon: Icon, label }) => (
            <Link key={to} to={to} className={`${styles.mobileLink} ${location.pathname === to ? styles.mobileLinkActive : ''}`}>
              <Icon size={20} style={{ marginBottom: 4 }} />
              <span style={{ fontSize: 9 }}>{label.split(' ')[0]}</span>
            </Link>
          ))}
        </div>
      </nav>

      <div className={styles.navSpacerDesktop} />
      <div className={styles.navSpacerMobileTop} />
      
      {showPlayer && <NowPlayingModal onClose={() => setShowPlayer(false)} />}
    </>
  )
}
