import { useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api.js';
import { CANAUX, CATEGORIES, TYPES_ELEMENT } from '../labels.js';

const VIDE = { categorie: '', canal: '', description: '', montant_perdu: '', date_faits: '', contact: '' };
const aujourdhui = () => new Date().toISOString().slice(0, 10);

function Confirmation({ reference, code }) {
  const [copie, setCopie] = useState(false);
  async function copier() {
    try {
      await navigator.clipboard.writeText(`Référence : ${reference}\nCode de suivi : ${code}`);
      setCopie(true);
    } catch {
      /* le texte reste affiché et sélectionnable */
    }
  }
  return (
    <section className="card confirm" aria-labelledby="ok-title">
      <h1 id="ok-title">Merci, votre signalement est enregistré</h1>
      <p>Notez ces deux informations : elles vous permettent de suivre votre dossier. <strong>Le code ne sera plus affiché.</strong></p>
      <dl className="codes">
        <div><dt>Référence</dt><dd>{reference}</dd></div>
        <div><dt>Code de suivi</dt><dd>{code}</dd></div>
      </dl>
      <div className="actions">
        <button type="button" className="btn btn--ghost" onClick={copier}>{copie ? 'Copié ✓' : 'Copier'}</button>
        <Link to="/suivi" className="btn">Suivre mon signalement</Link>
      </div>
      <p className="small muted">Si vous avez perdu de l'argent, contactez aussi votre opérateur au plus vite : un transfert peut parfois être bloqué.</p>
    </section>
  );
}

export default function Signaler() {
  const [form, setForm] = useState(VIDE);
  const [elements, setElements] = useState([{ type: 'telephone', valeur: '' }]);
  const [erreur, setErreur] = useState('');
  const [envoi, setEnvoi] = useState(false);
  const [cree, setCree] = useState(null);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const setElement = (i, k, v) => setElements((list) => list.map((el, j) => (j === i ? { ...el, [k]: v } : el)));

  async function onSubmit(e) {
    e.preventDefault();
    setErreur('');
    if (!form.categorie) return setErreur("Choisissez le type d'arnaque.");
    if (!form.canal) return setErreur('Indiquez comment vous avez été contacté.');
    if (form.description.trim().length < 20) return setErreur('Décrivez ce qui s\'est passé en quelques phrases (20 caractères au moins).');
    setEnvoi(true);
    try {
      const body = {
        categorie: form.categorie,
        canal: form.canal,
        description: form.description,
        montant_perdu: form.montant_perdu === '' ? null : Number(form.montant_perdu),
        date_faits: form.date_faits || null,
        contact: form.contact || null,
        elements: elements.filter((el) => el.valeur.trim().length >= 2),
      };
      setCree(await api('/api/signalements', { method: 'POST', body }));
      window.scrollTo(0, 0);
    } catch (err) {
      setErreur(err.message);
    } finally {
      setEnvoi(false);
    }
  }

  if (cree) return <Confirmation reference={cree.reference} code={cree.code_suivi} />;

  return (
    <form className="form" onSubmit={onSubmit} noValidate>
      <h1>Signaler une arnaque</h1>
      <p className="lead">Aucun compte n'est nécessaire. Les champs marqués d'un astérisque sont obligatoires.</p>

      <fieldset>
        <legend>Type d'arnaque *</legend>
        <div className="choices">
          {Object.entries(CATEGORIES).map(([k, c]) => (
            <label key={k} className={`choice ${form.categorie === k ? 'is-on' : ''}`}>
              <input type="radio" name="categorie" value={k} checked={form.categorie === k} onChange={set('categorie')} />
              <strong>{c.label}</strong>
              <span>{c.aide}</span>
            </label>
          ))}
        </div>
      </fieldset>

      <div className="field">
        <label htmlFor="canal">Comment avez-vous été contacté ? *</label>
        <select id="canal" value={form.canal} onChange={set('canal')}>
          <option value="">Choisir…</option>
          {Object.entries(CANAUX).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
      </div>

      <div className="field">
        <label htmlFor="description">Que s'est-il passé ? *</label>
        <textarea id="description" rows={6} maxLength={4000} value={form.description} onChange={set('description')}
                  placeholder="Ex. : J'ai reçu un message disant que j'avais gagné un bonus MoMo. On m'a demandé d'envoyer 5 000 F de frais…" />
        <span className="hint">{form.description.length} / 4000</span>
      </div>

      <fieldset>
        <legend>Numéros, sites ou profils utilisés par l'escroc</legend>
        <p className="hint">Ils seront comparés aux autres signalements. Une même ligne peut être écrite de plusieurs façons : nous les rapprochons.</p>
        {elements.map((el, i) => (
          <div className="element" key={i}>
            <label className="sr-only" htmlFor={`type-${i}`}>Type</label>
            <select id={`type-${i}`} value={el.type} onChange={(e) => setElement(i, 'type', e.target.value)}>
              {Object.entries(TYPES_ELEMENT).map(([k, t]) => <option key={k} value={k}>{t.label}</option>)}
            </select>
            <label className="sr-only" htmlFor={`valeur-${i}`}>Valeur</label>
            <input id={`valeur-${i}`} value={el.valeur} maxLength={300} placeholder={TYPES_ELEMENT[el.type].exemple}
                   onChange={(e) => setElement(i, 'valeur', e.target.value)} />
            {elements.length > 1 && (
              <button type="button" className="btn btn--ghost btn--small" aria-label={`Retirer l'élément ${i + 1}`}
                      onClick={() => setElements((list) => list.filter((_, j) => j !== i))}>Retirer</button>
            )}
          </div>
        ))}
        {elements.length < 10 && (
          <button type="button" className="btn btn--ghost btn--small" onClick={() => setElements((l) => [...l, { type: 'telephone', valeur: '' }])}>
            + Ajouter un élément
          </button>
        )}
      </fieldset>

      <div className="grid2">
        <div className="field">
          <label htmlFor="montant">Montant perdu (F CFA)</label>
          <input id="montant" type="number" inputMode="numeric" min="0" step="1" value={form.montant_perdu} onChange={set('montant_perdu')} placeholder="0" />
        </div>
        <div className="field">
          <label htmlFor="date">Date des faits</label>
          <input id="date" type="date" max={aujourdhui()} value={form.date_faits} onChange={set('date_faits')} />
        </div>
      </div>

      <div className="field">
        <label htmlFor="contact">Votre email ou téléphone (facultatif)</label>
        <input id="contact" maxLength={254} value={form.contact} onChange={set('contact')} placeholder="Pour qu'un agent puisse vous recontacter" />
        <span className="hint">Visible uniquement par les agents qui traitent votre dossier. Jamais publié.</span>
      </div>

      {erreur && <p className="error" role="alert">{erreur}</p>}
      <button className="btn btn--accent btn--large" disabled={envoi}>{envoi ? 'Envoi…' : 'Envoyer le signalement'}</button>
    </form>
  );
}
