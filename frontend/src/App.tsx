import { useEffect } from 'react'
import { Link, NavLink, Route, Routes, useLocation } from 'react-router-dom'
import { StageProvider } from './stage-context'
import Pitch from './pages/Pitch'
import Explore from './pages/Explore'
import Hotspot from './pages/Hotspot'
import Method from './pages/Method'

export default function App() {
  const { pathname } = useLocation()
  useEffect(() => {
    scrollTo(0, 0)
  }, [pathname])

  return (
    <StageProvider>
      <header className="nav">
        <Link to="/" className="wordmark">
          Dancing with the <span>SARs</span>
        </Link>
        <nav aria-label="Primary">
          <NavLink to="/" end>
            Pitch
          </NavLink>
          <NavLink to="/explore">Hotspots</NavLink>
          <NavLink to="/method">Method</NavLink>
        </nav>
      </header>
      <Routes>
        <Route path="/" element={<Pitch />} />
        <Route path="/explore" element={<Explore />} />
        <Route path="/hotspot/:id" element={<Hotspot />} />
        <Route path="/method" element={<Method />} />
        <Route path="*" element={<Pitch />} />
      </Routes>
      <footer className="foot">
        <span>NASA Space Apps Challenge 2026</span>
        <span>Data: NASA–ISRO NISAR · ASF DAAC · ESA Sentinel-1 · NASA GIBS · Open-Meteo</span>
      </footer>
    </StageProvider>
  )
}
