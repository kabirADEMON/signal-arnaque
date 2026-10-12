export const CATEGORIES = {
  mobile_money: { label: 'Mobile Money', aide: 'Faux transfert, faux gain, demande de code, « erreur d\'envoi ».' },
  faux_profil: { label: 'Faux profil', aide: 'Usurpation d\'identité sur WhatsApp, Facebook, TikTok…' },
  faux_site: { label: 'Faux site', aide: 'Site qui imite une banque, un opérateur ou un service public.' },
  faux_emploi: { label: 'Fausse offre d\'emploi', aide: 'Frais de dossier ou de formation exigés avant d\'être « recruté ».' },
  autre: { label: 'Autre arnaque', aide: 'Vente fictive, faux investissement, chantage…' },
};

export const CANAUX = {
  whatsapp: 'WhatsApp',
  sms: 'SMS',
  appel: 'Appel téléphonique',
  facebook: 'Facebook ou autre réseau',
  site_web: 'Site web',
  autre: 'Autre',
};

export const STATUTS = {
  recu: { label: 'Reçu', aide: 'Votre signalement est enregistré.' },
  en_examen: { label: 'En examen', aide: 'Un agent vérifie les informations.' },
  valide: { label: 'Validé', aide: 'L\'arnaque est confirmée ; les éléments signalés deviennent consultables.' },
  rejete: { label: 'Rejeté', aide: 'Les informations n\'ont pas permis de confirmer l\'arnaque.' },
};

export const TYPES_ELEMENT = {
  telephone: { label: 'Numéro de téléphone', exemple: '01 97 12 34 56' },
  site: { label: 'Site web', exemple: 'https://exemple-faux-site.com' },
  profil: { label: 'Profil ou nom utilisé', exemple: '@nom.du.profil' },
};

export const fcfa = (n) => `${new Intl.NumberFormat('fr-FR').format(n)} F CFA`;
export const dateFr = (iso) => new Date(iso).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' });
export const dateHeureFr = (iso) =>
  new Date(iso).toLocaleString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });

// « +2290197123456 » -> « +229 01 97 12 34 56 » ; les autres valeurs restent telles quelles.
export const lisible = (type, valeur) =>
  type === 'telephone' && /^\+229\d{10}$/.test(valeur)
    ? `+229 ${valeur.slice(4).replace(/(\d{2})(?=\d)/g, '$1 ')}`
    : valeur;
