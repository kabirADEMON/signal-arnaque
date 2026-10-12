// Parcours complet dans un vrai navigateur : signaler, suivre, instruire, vérifier.
// Prérequis : serveur de démonstration lancé (backend : python dev.py demo --neuf, front compilé),
// et Playwright disponible :  node e2e/parcours.cjs <chemin vers le paquet playwright> <dossier des captures>
const { chromium } = require(process.argv[2] || 'playwright');
const OUT = process.argv[3] || 'docs';
const BASE = 'http://127.0.0.1:8000';
const ok = (cond, msg) => { if (!cond) throw new Error('ÉCHEC : ' + msg); console.log('✓ ' + msg); };

(async () => {
  const browser = await chromium.launch({ channel: 'msedge' });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  // Les refus volontaires du test (mauvais code : 404, validation sans motif : 409) ne sont pas des bugs.
  page.on('console', (m) => m.type() === 'error' && !/status of (404|409)/.test(m.text()) && errors.push(m.text()));

  // 1. Accueil
  await page.goto(BASE + '/');
  await page.getByRole('heading', { name: /Victime ou témoin/ }).waitFor();
  await page.screenshot({ path: OUT + '/accueil.png', fullPage: true });
  ok(true, 'accueil affiché');

  // 2. Signalement par le formulaire
  await page.getByRole('link', { name: 'Signaler une arnaque' }).click();
  await page.getByRole('button', { name: 'Envoyer le signalement' }).click();
  ok(await page.getByRole('alert').textContent() === "Choisissez le type d'arnaque.", 'validation : type obligatoire');
  await page.getByRole('radio', { name: /^Mobile Money/ }).check();
  await page.getByLabel('Comment avez-vous été contacté ? *').selectOption('sms');
  await page.getByLabel("Que s'est-il passé ? *").fill("SMS annonçant un gain de 200 000 F ; on m'a demandé 7 500 F de frais puis mon code.");
  await page.getByLabel('Valeur').first().fill('00 00 00 99');
  await page.getByLabel('Montant perdu (F CFA)').fill('7500');
  await page.screenshot({ path: OUT + '/signaler.png', fullPage: true });
  await page.getByRole('button', { name: 'Envoyer le signalement' }).click();
  await page.getByRole('heading', { name: /signalement est enregistré/ }).waitFor();
  const ref = (await page.locator('.codes dd').nth(0).textContent()).trim();
  const code = (await page.locator('.codes dd').nth(1).textContent()).trim();
  ok(/^SA-[A-Z0-9]{8}$/.test(ref), `référence reçue ${ref}`);
  await page.screenshot({ path: OUT + '/confirmation.png' });

  // 3. Suivi par le déclarant
  await page.getByRole('link', { name: 'Suivre mon signalement' }).click();
  await page.getByLabel('Référence').fill(ref);
  await page.getByLabel('Code de suivi').fill('MAUVAISCOD');
  await page.getByRole('button', { name: 'Voir' }).click();
  ok((await page.getByRole('alert').textContent()).includes('incorrect'), 'mauvais code refusé');
  await page.getByLabel('Code de suivi').fill(code);
  await page.getByRole('button', { name: 'Voir' }).click();
  await page.getByRole('heading', { name: ref }).waitFor();
  ok(await page.locator('.card .badge').first().textContent() === 'Reçu', 'statut « Reçu » visible');

  // 4. L'agent instruit le dossier
  await page.goto(BASE + '/agent');
  await page.getByLabel('Email').fill('agent@demo.bj');
  await page.getByLabel('Mot de passe').fill('demo-signal-2026');
  await page.getByRole('button', { name: 'Se connecter' }).click();
  await page.getByRole('heading', { name: 'Dossiers' }).waitFor();
  await page.screenshot({ path: OUT + '/agent-dossiers.png', fullPage: true });
  await page.getByLabel('Rechercher').fill(ref);
  await page.getByRole('button', { name: 'Rechercher' }).click();
  await page.getByText(ref).click();
  await page.getByRole('button', { name: 'Mettre en examen' }).click();
  await page.getByRole('button', { name: "Valider l'arnaque" }).click();
  ok((await page.getByRole('alert').textContent()).includes('motif'), 'motif exigé pour valider');
  await page.getByLabel('Motif communiqué au déclarant').fill('Numéro déjà signalé, arnaque confirmée.');
  await page.getByRole('button', { name: "Valider l'arnaque" }).click();
  await page.locator('h1 + .badge, .row-between .badge').filter({ hasText: 'Validé' }).first().waitFor();
  ok(true, 'dossier validé par l’agent');
  await page.screenshot({ path: OUT + '/agent-dossier.png', fullPage: true });

  // 5. Un autre citoyen vérifie le numéro, écrit autrement
  await page.goto(BASE + '/');
  await page.getByLabel('Numéro, site ou profil').fill('+229 01 00 00 00 99');
  await page.getByRole('button', { name: 'Vérifier' }).click();
  const verdict = await page.locator('.verdict').textContent();
  ok(/Attention : \d+ signalements? confirmés?/.test(verdict), 'la vérification signale le numéro');
  await page.locator('.verify').screenshot({ path: OUT + '/verifier.png' });

  // 6. Statistiques
  await page.getByRole('link', { name: 'Statistiques' }).first().click();
  await page.getByRole('heading', { name: 'Par type d\'arnaque' }).waitFor();
  await page.screenshot({ path: OUT + '/statistiques.png', fullPage: true });

  // 7. Téléphone
  const mobile = await browser.newPage({ viewport: { width: 390, height: 844 }, isMobile: true });
  await mobile.goto(BASE + '/signaler');
  await mobile.screenshot({ path: OUT + '/mobile-signaler.png', fullPage: true });
  const overflow = await mobile.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
  ok(!overflow, 'pas de défilement horizontal sur téléphone');

  ok(errors.length === 0, 'aucune erreur JavaScript' + (errors.length ? ' : ' + errors.join(' | ') : ''));
  await browser.close();
})().catch((e) => { console.error(e.message); process.exit(1); });
