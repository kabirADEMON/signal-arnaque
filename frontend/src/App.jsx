import { useEffect } from 'react';
import { Link, NavLink, Route, Routes, useLocation } from 'react-router-dom';
import Accueil from './pages/Accueil.jsx';
import Signaler from './pages/Signaler.jsx';
import Suivi from './pages/Suivi.jsx';
import Statistiques from './pages/Statistiques.jsx';
import Connexion from './pages/agent/Connexion.jsx';
import Dossiers from './pages/agent/Dossiers.jsx';
import Dossier from './pages/agent/Dossier.jsx';

function Header() {
  const { pathname } = useLocation();
  const agent = pathname.startsWith('/agent');
  return (
    <header className="header">
      <div className="container header__row">
        <Link to="/" className="logo">
          <svg viewBox="0 0 32 32" aria-hidden="true">
            <rect width="32" height="32" rx="7" fill="currentColor" />
            <path d="M16 6 26 24H6Z" fill="#f2b33d" />
            <rect x="15" y="12" width="2" height="7" rx="1" fill="#1d3a5f" />
            <circle cx="16" cy="21.5" r="1.2" fill="#1d3a5f" />
          </svg>
          Signal Arnaque
          {agent && <span className="logo__badge">Espace agents</span>}
        </Link>
        <nav aria-label="Navigation principale" className="nav">
          <NavLink to="/signaler">Signaler</NavLink>
          <NavLink to="/suivi">Suivre</NavLink>
          <NavLink to="/statistiques">Statistiques</NavLink>
        </nav>
      </div>
    </header>
  );
}

export default function App() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);

  return (
    <>
      <a href="#contenu" className="skip">Aller au contenu</a>
      <Header />
      <main id="contenu" className="container main">
        <Routes>
          <Route path="/" element={<Accueil />} />
          <Route path="/signaler" element={<Signaler />} />
          <Route path="/suivi" element={<Suivi />} />
          <Route path="/statistiques" element={<Statistiques />} />
          <Route path="/agent/connexion" element={<Connexion />} />
          <Route path="/agent" element={<Dossiers />} />
          <Route path="/agent/dossiers/:id" element={<Dossier />} />
          <Route path="*" element={<p className="empty">Cette page n'existe pas. <Link to="/">Retour à l'accueil</Link></p>} />
        </Routes>
      </main>
      <footer className="footer">
        <div className="container footer__row">
          <p>
            En cas d'urgence ou de perte d'argent, contactez aussi votre opérateur et la police.
            Ne communiquez jamais un code reçu par SMS.
          </p>
          <p>
            <Link to="/agent">Espace agents</Link> · Projet de démonstration par{' '}
            <a href="https://portfolio-six-opal-16.vercel.app" rel="noreferrer">Kabir ADEMON</a>
          </p>
        </div>
      </footer>
    </>
  );
}
