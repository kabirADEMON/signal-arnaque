import { useEffect, useState } from 'react';
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom';
import { api, session } from '../../api.js';
import { CANAUX, CATEGORIES, STATUTS, TYPES_ELEMENT, dateFr, dateHeureFr, fcfa, lisible } from '../../labels.js';
import { Badge } from '../Suivi.jsx';

const ACTIONS = {
  en_examen: 'Mettre en examen',
  valide: "Valider l'arnaque",
  rejete: 'Rejeter',
};

export default function Dossier() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [d, setD] = useState(null);
  const [motif, setMotif] = useState('');
  const [erreur, setErreur] = useState('');
  const [envoi, setEnvoi] = useState(false);
  const connecte = session.get();

  useEffect(() => {
    if (!connecte) return;
    api(`/api/agent/signalements/${id}`, { auth: true })
      .then(setD)
      .catch((e) => (e.status === 401 ? navigate('/agent/connexion') : setErreur(e.message)));
  }, [id]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!connecte) return <Navigate to="/agent/connexion" replace />;
  if (erreur && !d) return <p className="error" role="alert">{erreur}</p>;
  if (!d) return <p className="muted">Chargement…</p>;

  async function changer(statut) {
    setErreur('');
    setEnvoi(true);
    try {
      setD(await api(`/api/agent/signalements/${id}/statut`, { method: 'POST', auth: true, body: { statut, motif: motif || null } }));
      setMotif('');
    } catch (e) {
      setErreur(e.message);
    } finally {
      setEnvoi(false);
    }
  }

  return (
    <>
      <p><Link to="/agent">← Tous les dossiers</Link></p>
      <div className="row-between">
        <h1>{d.reference}</h1>
        <Badge statut={d.statut} />
      </div>
      <p className="muted">
        {CATEGORIES[d.categorie].label} · {CANAUX[d.canal]} · reçu le {dateHeureFr(d.cree_le)}
      </p>

      <div className="grid2 grid2--top">
        <section className="card">
          <h2>Récit du déclarant</h2>
          <p className="prewrap">{d.description}</p>
          <dl className="facts">
            <dt>Montant perdu</dt><dd>{d.montant_perdu != null ? fcfa(d.montant_perdu) : 'Non indiqué'}</dd>
            <dt>Date des faits</dt><dd>{d.date_faits ? dateFr(d.date_faits) : 'Non indiquée'}</dd>
            <dt>Contact</dt><dd>{d.contact || 'Anonyme'}</dd>
          </dl>
          <h3>Éléments signalés</h3>
          {d.elements.length ? (
            <ul className="elements">
              {d.elements.map((e, i) => (
                <li key={i}>
                  <span className="muted small">{TYPES_ELEMENT[e.type].label}</span>
                  <Link to={`/agent?q=${encodeURIComponent(e.valeur_normalisee)}`} title="Voir les autres dossiers qui le citent">
                    {lisible(e.type, e.valeur_normalisee)}
                  </Link>
                  {e.valeur !== e.valeur_normalisee && e.valeur !== lisible(e.type, e.valeur_normalisee) && <span className="muted small"> (saisi : {e.valeur})</span>}
                </li>
              ))}
            </ul>
          ) : <p className="muted">Aucun.</p>}
        </section>

        <section className="card">
          <h2>Décision</h2>
          {d.transitions_possibles.length ? (
            <>
              <div className="field">
                <label htmlFor="motif">Motif communiqué au déclarant</label>
                <textarea id="motif" rows={3} maxLength={500} value={motif} onChange={(e) => setMotif(e.target.value)}
                          placeholder="Obligatoire pour valider ou rejeter" />
              </div>
              <div className="actions">
                {d.transitions_possibles.map((s) => (
                  <button key={s} className={`btn ${s === 'valide' ? 'btn--accent' : s === 'rejete' ? 'btn--danger' : 'btn--ghost'}`}
                          disabled={envoi} onClick={() => changer(s)}>
                    {ACTIONS[s]}
                  </button>
                ))}
              </div>
            </>
          ) : <p className="muted">Aucune action possible.</p>}
          {erreur && <p className="error" role="alert">{erreur}</p>}

          <h2>Historique</h2>
          <ol className="timeline">
            {d.historique.map((h, i) => (
              <li key={i}>
                <Badge statut={h.nouveau_statut} />
                <time dateTime={h.date}>{dateHeureFr(h.date)}</time>
                <span className="muted small"> · {h.agent || 'Déclarant'}</span>
                {h.motif && <p>{h.motif}</p>}
              </li>
            ))}
          </ol>
          <p className="small muted">{STATUTS[d.statut].aide}</p>
        </section>
      </div>
    </>
  );
}
