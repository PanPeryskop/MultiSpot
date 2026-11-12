import { useNavigate } from 'react-router-dom'
import { Radio, Music2, ListMusic, Shuffle, Wand2, Star, Clock, BarChart2, Layers, History } from 'lucide-react'
import styles from './DashboardPage.module.css'

const FEATURES = [
  {
    icon: Radio,
    title: 'Random Hub',
    description: 'Random tracks from 6000+ genres, or a whole station from one genre you pick. Into your queue or a new playlist.',
    to: '/random-hub',
    accent: '#1db954',
  },
  {
    icon: Music2,
    title: 'Track Radio',
    description: 'One track in, a full playlist out. Built from what listeners play right next to it.',
    to: '/track-to-playlist',
    accent: '#6c63ff',
  },
  {
    icon: ListMusic,
    title: 'Queue Setter',
    description: 'Select multiple playlists and interleave them into a seamless, alternating queue.',
    to: '/queue-setter',
    accent: '#f7931e',
  },
  {
    icon: Shuffle,
    title: 'Playlist Shuffler',
    description: 'True-shuffle any playlist. Recreates it in a random order so Spotify plays it properly.',
    to: '/playlist-shuffler',
    accent: '#ff4d6d',
  },
  {
    icon: Wand2,
    title: 'Magic Mix',
    description: 'A fresh playlist from your taste, skipping the songs you already have on repeat.',
    to: '/magic-recommender',
    accent: '#00b4d8',
  },
  {
    icon: Star,
    title: 'Stats Hub',
    description: 'Explore your top tracks, top artists, and musical DNA breakdown.',
    to: '/stats',
    accent: '#f9c74f',
  },
  {
    icon: Layers,
    title: 'Fusion Center',
    description: 'Mix tracks, artists, albums and playlists as seeds and get one playlist that bridges them.',
    to: '/fusion-center',
    accent: '#00f5d4',
  },
  {
    icon: Clock,
    title: 'Time Machine',
    description: 'Pick a decade and queue its hits straight into your player.',
    to: '/time-machine',
    accent: '#ffe346',
  },
  {
    icon: BarChart2,
    title: 'Track X-Ray',
    description: 'Release info, album context, popularity and the artists behind any single track.',
    to: '/track-stats',
    accent: '#b8ff3c',
  },
  {
    icon: History,
    title: 'Rewind',
    description: 'Save your recently played, monthly, yearly or all-time favourites as a playlist.',
    to: '/rewind',
    accent: '#9b8cff',
    note: 'New',
  },
]

export default function DashboardPage() {
  const navigate = useNavigate()
  return (
    <main className={styles.page}>
      <div className={styles.header + ' fade-in'}>
        <h1 className={styles.title}>What do you want to do?</h1>
        <p className={styles.subtitle}>Pick a tool and take control of your Spotify experience.</p>
      </div>
      <div className={styles.grid + ' stagger'}>
        {FEATURES.map(({ icon: Icon, title, description, to, accent, note }) => (
          <button
            key={title}
            className={styles.card}
            onClick={() => navigate(to)}
            style={{ '--accent': accent }}
          >
            <div className={styles.iconWrapper}>
              <Icon size={22} />
            </div>
            <div className={styles.cardBody}>
              <h2 className={styles.cardTitle}>{title}</h2>
              {note && <span className={styles.note}>{note}</span>}
              <p className={styles.cardDesc}>{description}</p>
            </div>
            <div className={styles.arrow}>→</div>
          </button>
        ))}
      </div>
    </main>
  )
}
