import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api.js';
import { CATEGORIES, TYPES_ELEMENT, dateFr, fcfa, lisible } from '../labels.js';

function Verifier() {
  const [valeur, setValeur] = useState('');
  const [resultat, setResultat] = useState(null);
  const [erreur, setErreur] = useState('');
  const [charge, setCharge] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    if (valeur.trim().length < 3) return setErreur('Saisissez un numéro, un site ou un nom de profil.');
    setCharge(true);
    setErreur('');
    try {
      setResultat(await api(`/api/verifier?valeur=${encodeURIComponent(valeur.trim())}`));
    } catch (err) {
      setErreur(err.message);
      setResultat(null);
    } finally {
      setCharge(false);
    }
  }

  return (
    <section className="card verify" aria-labelledby="verify-title">
      <h2 id="verify-title">Vérifier avant de payer</h2>
      <p className="muted">Un numéro, un site ou un profil vous semble suspect ? Regardez s'il a déjà été signalé.</p>
      <form className="verify__form" onSubmit={onSubmit}>
        <label htmlFor="valeur" className="sr-only">Numéro, site ou profil</label>
        <input id="valeur" value={valeur} onChange={(e) => setValeur(e.target.value)}
               placeholder="01 97 12 34 56, faux-site.com ou @profil" maxLength={300} />
        <button className="btn" disabled={charge}>{charge ? 'Recherche…' : 'Vérifier'}</button>
      </form>
      {erreur && <p className="error" role="alert">{erreur}</p>}
      {resultat && (
        <div className={`verdict ${resultat.signalements_valides ? 'verdict--alerte' : 'verdict--rien'}`} role="status">
          {resultat.signalements_valides ? (
            <>
              <strong>
                Attention : {resultat.signalements_valides} signalement{resultat.signalements_valides > 1 ? 's' : ''} confirmé
                {resultat.signalements_valides > 1 ? 's' : ''}
              </strong>
              <p>
                {TYPES_ELEMENT[resultat.type].label} « {lisible(resultat.type, resultat.valeur_normalisee)} » ·{' '}
                {resultat.categories.map((c) => CATEGORIES[c].label).join(', ')} · dernier le {dateFr(resultat.dernier_signalement)}.
              </p>
              <p>Ne payez pas et ne communiquez aucun code.</p>
            </>
          ) : (
            <>
              <strong>Aucun signalement confirmé pour « {lisible(resultat.type, resultat.valeur_normalisee)} »</strong>
              <p>Cela ne prouve pas que c'est sûr : restez prudent, surtout si l'on vous presse ou vous demande un code.</p>
            </>
          )}
        </div>
      )}
      <p className="small muted">Seuls les signalements vérifiés par un agent sont pris en compte.</p>
    </section>
  );
}

export default function Accueil() {
  const [stats, setStats] = useState(null);
  useEffect(() => {
    api('/api/statistiques').then(setStats).catch(() => {});
  }, []);

  return (
    <>
      <section className="hero">
        <p className="eyebrow">Mobile Money · faux profils · faux sites</p>
        <h1>Victime ou témoin d'une arnaque en ligne&nbsp;?</h1>
        <p className="lead">
          Signalez-la en quelques minutes, sans créer de compte. Chaque signalement est examiné, et les
          numéros ou sites confirmés aident les autres à ne pas tomber dans le même piège.
        </p>
        <div className="actions">
          <Link to="/signaler" className="btn btn--accent">Signaler une arnaque</Link>
          <Link to="/suivi" className="btn btn--ghost">Suivre mon signalement</Link>
        </div>
      </section>

      <Verifier />

      {stats && (
        <section className="kpis" aria-label="Chiffres clés">
          <div><strong>{stats.total}</strong><span>signalements reçus</span></div>
          <div><strong>{stats.valides}</strong><span>arnaques confirmées</span></div>
          <div><strong>{fcfa(stats.montant_perdu_valide)}</strong><span>pertes confirmées</span></div>
          <Link to="/statistiques" className="kpis__link">Voir les statistiques →</Link>
        </section>
      )}

      <section aria-labelledby="types-title">
        <h2 id="types-title">Ce que vous pouvez signaler</h2>
        <ul className="types">
          {Object.entries(CATEGORIES).map(([k, c]) => (
            <li key={k}>
              <strong>{c.label}</strong>
              <span>{c.aide}</span>
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}
