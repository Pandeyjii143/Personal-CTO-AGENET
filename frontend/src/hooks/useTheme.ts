import { useEffect, useState } from 'react'

export type ThemePreference = 'light' | 'dark' | 'system'

const STORAGE_KEY = 'personal-cto-theme'
const THEME_EVENT = 'personal-cto-theme-change'

function readPreference(): ThemePreference {
  const saved = localStorage.getItem(STORAGE_KEY)
  return saved === 'light' || saved === 'dark' || saved === 'system'
    ? saved
    : 'system'
}

export function useTheme() {
  const [preference, setPreferenceState] = useState<ThemePreference>(readPreference)

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const applyTheme = () => {
      const theme =
        preference === 'system'
          ? mediaQuery.matches
            ? 'dark'
            : 'light'
          : preference

      document.documentElement.dataset.theme = theme
      document.documentElement.style.colorScheme = theme
    }

    applyTheme()
    mediaQuery.addEventListener('change', applyTheme)

    return () => mediaQuery.removeEventListener('change', applyTheme)
  }, [preference])

  useEffect(() => {
    const handleThemeChange = (event: Event) => {
      setPreferenceState((event as CustomEvent<ThemePreference>).detail)
    }
    const handleStorage = (event: StorageEvent) => {
      if (event.key === STORAGE_KEY) setPreferenceState(readPreference())
    }

    window.addEventListener(THEME_EVENT, handleThemeChange)
    window.addEventListener('storage', handleStorage)
    return () => {
      window.removeEventListener(THEME_EVENT, handleThemeChange)
      window.removeEventListener('storage', handleStorage)
    }
  }, [])

  function setPreference(nextPreference: ThemePreference) {
    localStorage.setItem(STORAGE_KEY, nextPreference)
    window.dispatchEvent(new CustomEvent(THEME_EVENT, { detail: nextPreference }))
  }

  return { preference, setPreference }
}
