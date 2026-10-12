import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, session } from '../../api.js';

export default function Connexion() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [motDePasse, setMotDePasse] = useState('');
  const [erreur, setErreur] = useState('');
  const [charge, setCharge] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setErreur('');
    setCharge(true);
    try {
      session.set(await api('/api/auth/connexion', { method: 'POST', body: { email, mot_de_passe: motDePasse } }));
      navigate('/agent');
    } catch (err) {
      setErreur(err.message);
    } finally {
      setCharge(false);
    }
  }

  return (
    <form className="card form form--narrow" onSubmit={onSubmit}>
      <h1>Espace agents</h1>
      <p className="muted">Réservé aux agents chargés d'examiner les signalements.</p>
      <div className="field">
        <label htmlFor="email">Email</label>
        <input id="email" type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} required />
      </div>
      <div className="field">
        <label htmlFor="mdp">Mot de passe</label>
        <input id="mdp" type="password" autoComplete="current-password" value={motDePasse} onChange={(e) => setMotDePasse(e.target.value)} required />
      </div>
      {erreur && <p className="error" role="alert">{erreur}</p>}
      <button className="btn" disabled={charge}>{charge ? 'Connexion…' : 'Se connecter'}</button>
    </form>
  );
}
