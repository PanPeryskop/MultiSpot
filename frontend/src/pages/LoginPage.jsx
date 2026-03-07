import { Disc3 } from 'lucide-react'
import styles from './LoginPage.module.css'

export default function LoginPage() {
  return (
    <main className={styles.page}>
      <div className={styles.brand}>
        <div className={styles.logoMark}>MS</div>
        <span className={styles.logoText}>MultiSpot</span>
      </div>
      <h1 className={styles.title}>Your Spotify.<br />Supercharged.</h1>
      <p className={styles.subtitle}>
        Random queues, playlist tools, magic recommendations — <br />
        all in one place. Log in to get started.
      </p>
      <a href="/auth/login" className={`btn btn-primary ${styles.loginBtn}`}>
        <Disc3 size={18} />
        Continue with Spotify
      </a>
      <p className={styles.finePrint}>
        Uses your Spotify account. Your credentials are never stored.
      </p>
    </main>
  )
}
