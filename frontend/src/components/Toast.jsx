import { useState, useEffect } from 'react'
import { CheckCircle2, AlertCircle, Info } from 'lucide-react'
import styles from './Toast.module.css'

export default function Toast({ message, type = 'info' }) {
  const [visible, setVisible] = useState(true)

  useEffect(() => {
    const t = setTimeout(() => setVisible(false), 3800)
    return () => clearTimeout(t)
  }, [])

  if (!visible) return null

  const icons = { success: CheckCircle2, error: AlertCircle, info: Info }
  const Icon = icons[type] || Info

  return (
    <div className={`${styles.toast} ${styles[type]}`}>
      <Icon size={16} />
      <span>{message}</span>
    </div>
  )
}
