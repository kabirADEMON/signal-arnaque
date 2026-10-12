// Petit client pour l'API : messages d'erreur lisibles et jeton des agents.

const TOKEN_KEY = 'sa-jeton';

export const session = {
  get: () => {
    try {
      return JSON.parse(sessionStorage.getItem(TOKEN_KEY));
    } catch {
      return null;
    }
  },
  set: (value) => sessionStorage.setItem(TOKEN_KEY, JSON.stringify(value)),
  clear: () => sessionStorage.removeItem(TOKEN_KEY),
};

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

function message(status, body) {
  if (status === 429) return 'Trop de tentatives. Réessayez dans quelques minutes.';
  const detail = body?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return 'Certains champs sont incomplets ou invalides. Vérifiez le formulaire.';
  return "Le service ne répond pas comme prévu. Réessayez plus tard.";
}

export async function api(path, { method = 'GET', body, auth = false } = {}) {
  const headers = { Accept: 'application/json' };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (auth) {
    const s = session.get();
    if (s) headers.Authorization = `Bearer ${s.access_token}`;
  }
  let res;
  try {
    res = await fetch(path, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
  } catch {
    throw new ApiError('Impossible de joindre le service. Vérifiez votre connexion.', 0);
  }
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    if (res.status === 401 && auth) session.clear();
    throw new ApiError(message(res.status, data), res.status);
  }
  return data;
}
