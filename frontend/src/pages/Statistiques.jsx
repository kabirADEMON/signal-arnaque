import { useEffect, useState } from 'react';
import { api } from '../api.js';
import { CATEGORIES, STATUTS, fcfa } from '../labels.js';

const MOIS = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.'];
const moisCourt = (m) => `${MOIS[Number(m.slice(5)) - 1]} ${m.slice(2, 4)}`;

// Barres horizontales : total reçu (clair) et part confirmée (foncée) pour chaque type.
function ParCategorie({ data }) {
  const max = Math.max(1, ...data.map((d) => d.total));
  return (
    <ul className="hbars">
      {data.map((d) => (
        <li key={d.categorie}>
          <div className="hbars__label">
            <span>{CATEGORIES[d.categorie].label}</span>
            <span className="muted">{d.valides} confirmé{d.valides > 1 ? 's' : ''} / {d.total} reçu{d.total > 1 ? 's' : ''}</span>
          </div>
          <div className="hbars__track" role="img" aria-label={`${d.total} reçus dont ${d.valides} confirmés`}>
            <span className="hbars__total" style={{ width: `${(d.total / max) * 100}%` }} />
            <span className="hbars__ok" style={{ width: `${(d.valides / max) * 100}%` }} />
          </div>
          {d.montant_valide > 0 && <p className="small muted">Pertes confirmées : {fcfa(d.montant_valide)}</p>}
        </li>
      ))}
    </ul>
  );
}

function ParMois({ data }) {
  if (!data.length) return <p className="muted">Pas encore de données.</p>;
  const max = Math.max(1, ...data.map((d) => d.total));
  const w = 44;
  const h = 160;
  return (
    <svg className="vbars" viewBox={`0 0 ${data.length * w} ${h + 40}`} role="img"
         aria-label={data.map((d) => `${moisCourt(d.mois)} : ${d.total}`).join(', ')}>
      {data.map((d, i) => {
        const bh = Math.max(2, (d.total / max) * h);
        return (
          <g key={d.mois} transform={`translate(${i * w} 0)`}>
            <rect x="8" y={h - bh + 14} width={w - 16} height={bh} rx="3" />
            <text x={w / 2} y={h - bh + 8} textAnchor="middle" className="vbars__n">{d.total}</text>
            <text x={w / 2} y={h + 32} textAnchor="middle" className="vbars__m">{moisCourt(d.mois)}</text>
          </g>
        );
      })}
    </svg>
  );
}

export default function Statistiques() {
  const [stats, setStats] = useState(null);
  const [erreur, setErreur] = useState('');
  useEffect(() => {
    api('/api/statistiques').then(setStats).catch((e) => setErreur(e.message));
  }, []);

  if (erreur) return <p className="error" role="alert">{erreur}</p>;
  if (!stats) return <p className="muted">Chargement…</p>;

  return (
    <>
      <h1>Statistiques</h1>
      <p className="lead">
        Tous les signalements reçus, et ceux confirmés par un agent. Les montants ne comptent que les arnaques confirmées.
      </p>
      <section className="kpis" aria-label="Chiffres clés">
        <div><strong>{stats.total}</strong><span>signalements reçus</span></div>
        <div><strong>{stats.valides}</strong><span>arnaques confirmées</span></div>
        <div><strong>{fcfa(stats.montant_perdu_valide)}</strong><span>pertes confirmées</span></div>
      </section>
      <div className="grid2 grid2--top">
        <section className="card">
          <h2>Par type d'arnaque</h2>
          <p className="legend"><span className="sw sw--total" /> reçus <span className="sw sw--ok" /> confirmés</p>
          <ParCategorie data={stats.par_categorie} />
        </section>
        <section className="card">
          <h2>Par statut</h2>
          <ul className="statuts">
            {Object.entries(stats.par_statut).map(([k, n]) => (
              <li key={k}><span className={`badge badge--${k}`}>{STATUTS[k].label}</span><strong>{n}</strong></li>
            ))}
          </ul>
          <h2>Par mois</h2>
          <ParMois data={stats.par_mois} />
        </section>
      </div>
    </>
  );
}
