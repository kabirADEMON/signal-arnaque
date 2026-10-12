import { useEffect, useState } from 'react';
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom';
import { api, session } from '../../api.js';
import { CANAUX, CATEGORIES, STATUTS, dateHeureFr, fcfa } from '../../labels.js';
import { Badge } from '../Suivi.jsx';

export default function Dossiers() {
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const [page, setPage] = useState(null);
  const [erreur, setErreur] = useState('');
  const [q, setQ] = useState(params.get('q') || '');
  const connecte = session.get();

  const statut = params.get('statut') || '';
  const categorie = params.get('categorie') || '';
  const numero = Number(params.get('page') || 1);

  useEffect(() => {
    if (!connecte) return;
    const query = new URLSearchParams({ page: numero, par_page: 20 });
    if (statut) query.set('statut', statut);
    if (categorie) query.set('categorie', categorie);
    if (params.get('q')) query.set('q', params.get('q'));
    api(`/api/agent/signalements?${query}`, { auth: true })
      .then(setPage)
      .catch((e) => (e.status === 401 ? navigate('/agent/connexion') : setErreur(e.message)));
  }, [params]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!connecte) return <Navigate to="/agent/connexion" replace />;

  const filtrer = (k, v) => {
    const next = new URLSearchParams(params);
    if (v) next.set(k, v);
    else next.delete(k);
    next.delete('page');
    setParams(next);
  };
  const pages = page ? Math.max(1, Math.ceil(page.total / page.par_page)) : 1;

  return (
    <>
      <div className="row-between">
        <h1>Dossiers</h1>
        <p className="muted">
          {connecte.nom} ·{' '}
          <button type="button" className="linklike" onClick={() => { session.clear(); navigate('/agent/connexion'); }}>
            Se déconnecter
          </button>
        </p>
      </div>

      <div className="filters">
        <select aria-label="Filtrer par statut" value={statut} onChange={(e) => filtrer('statut', e.target.value)}>
          <option value="">Tous les statuts</option>
          {Object.entries(STATUTS).map(([k, s]) => <option key={k} value={k}>{s.label}</option>)}
        </select>
        <select aria-label="Filtrer par type" value={categorie} onChange={(e) => filtrer('categorie', e.target.value)}>
          <option value="">Tous les types</option>
          {Object.entries(CATEGORIES).map(([k, c]) => <option key={k} value={k}>{c.label}</option>)}
        </select>
        <form onSubmit={(e) => { e.preventDefault(); filtrer('q', q.trim()); }} className="filters__search">
          <input aria-label="Rechercher" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Référence, numéro, site, mot…" maxLength={100} />
          <button className="btn btn--small">Rechercher</button>
        </form>
      </div>

      {erreur && <p className="error" role="alert">{erreur}</p>}
      {page && (
        <>
          <p className="muted">{page.total} dossier{page.total > 1 ? 's' : ''}</p>
          {page.elements.length === 0 ? (
            <p className="empty">Aucun dossier ne correspond.</p>
          ) : (
            <ul className="dossiers">
              {page.elements.map((d) => (
                <li key={d.id}>
                  <Link to={`/agent/dossiers/${d.id}`} className="dossier">
                    <div className="row-between">
                      <strong>{d.reference}</strong>
                      <Badge statut={d.statut} />
                    </div>
                    <p className="muted small">
                      {CATEGORIES[d.categorie].label} · {CANAUX[d.canal]} · {dateHeureFr(d.cree_le)}
                      {d.montant_perdu ? ` · ${fcfa(d.montant_perdu)}` : ''}
                    </p>
                    <p>{d.extrait}</p>
                  </Link>
                </li>
              ))}
            </ul>
          )}
          {pages > 1 && (
            <nav className="pager" aria-label="Pages">
              <button className="btn btn--ghost btn--small" disabled={numero <= 1} onClick={() => filtrer('page', String(numero - 1))}>← Précédent</button>
              <span>Page {numero} / {pages}</span>
              <button className="btn btn--ghost btn--small" disabled={numero >= pages} onClick={() => filtrer('page', String(numero + 1))}>Suivant →</button>
            </nav>
          )}
        </>
      )}
    </>
  );
}
