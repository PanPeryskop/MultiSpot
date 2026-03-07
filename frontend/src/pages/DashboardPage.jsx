import { useNavigate } from 'react-router-dom'
import { Radio, Music2, ListMusic, Shuffle, Wand2, Star, Clock, BarChart2, Layers } from 'lucide-react'
import styles from './DashboardPage.module.css'

const FEATURES = [
  {
    icon: Radio,
    title: 'Random Hub',
    description: 'Discover new music by adding randomly selected tracks from across 6000+ genres to your queue or a custom playlist.',
    to: '/random-hub',
    accent: '#1db954',
  },
  {
    icon: Music2,
    title: 'Track to Playlist',
    description: 'Enter any Spotify track URL and get a full playlist of recommendations built around it.',
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
    title: 'Magic Recommender',
    description: 'Instantly generate a new playlist based on your top Spotify tracks with one click.',
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
    description: 'Paste links to any tracks or artists and we will build a custom playlist fusing their DNA.',
    to: '/fusion-center',
    accent: '#00f5d4',
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
