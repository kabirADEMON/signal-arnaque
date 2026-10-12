import { useState } from 'react';
import { api } from '../api.js';
import { CATEGORIES, STATUTS, dateFr, dateHeureFr } from '../labels.js';

export function Badge({ statut }) {
  return <span className={`badge badge--${statut}`}>{STATUTS[statut].label}</span>;
}

export default function Suivi() {
  const [reference, setReference] = useState('');
  const [code, setCode] = useState('');
  const [dossier, setDossier] = useState(null);
  const [erreur, setErreur] = useState('');
  const [charge, setCharge] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setErreur('');
    setCharge(true);
    try {
      setDossier(await api('/api/suivi', { method: 'POST', body: { reference, code } }));
    } catch (err) {
      setDossier(null);
      setErreur(err.message);
    } finally {
      setCharge(false);
    }
  }

  return (
    <>
      <h1>Suivre mon signalement</h1>
      <form className="card form form--inline" onSubmit={onSubmit}>
        <div className="field">
          <label htmlFor="ref">Référence</label>
          <input id="ref" value={reference} onChange={(e) => setReference(e.target.value)} placeholder="SA-XXXXXXXX" maxLength={16} autoComplete="off" />
        </div>
        <div className="field">
          <label htmlFor="code">Code de suivi</label>
          <input id="code" value={code} onChange={(e) => setCode(e.target.value)} maxLength={20} autoComplete="off" />
        </div>
        <button className="btn" disabled={charge}>{charge ? 'Recherche…' : 'Voir'}</button>
      </form>
      {erreur && <p className="error" role="alert">{erreur}</p>}

      {dossier && (
        <section className="card" aria-labelledby="dossier-title">
          <div className="row-between">
            <h2 id="dossier-title">{dossier.reference}</h2>
            <Badge statut={dossier.statut} />
          </div>
          <p className="muted">{CATEGORIES[dossier.categorie].label} · envoyé le {dateFr(dossier.cree_le)}</p>
          <p>{STATUTS[dossier.statut].aide}</p>
          <ol className="timeline">
            {dossier.historique.map((h, i) => (
              <li key={i}>
                <Badge statut={h.statut} />
                <time dateTime={h.date}>{dateHeureFr(h.date)}</time>
                {h.motif && <p>{h.motif}</p>}
              </li>
            ))}
          </ol>
        </section>
      )}
    </>
  );
}
