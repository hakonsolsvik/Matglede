// Firebase-oppsett for innlogging. Lim inn verdiene fra Firebase-konsollen
// (Prosjektinnstillinger → Dine apper → Web-app → SDK-oppsett → Config).
// Disse verdiene er ikke hemmelige: de identifiserer bare prosjektet, og tilgangen styres
// av reglene i firestore.rules. La feltene stå tomme for å kjøre appen uten innlogging.
window.MATGLEDE_FIREBASE = {
  apiKey: "AIzaSyDwzAxrmUaNaZUz3LtJrdH0q8TLX2ueTb4",
  authDomain: "matglede-4dbc5.firebaseapp.com",
  projectId: "matglede-4dbc5",
  appId: "1:903715759901:web:eddcac960cb3b9c3cf63f4"
};
// Adressen til bildegjenkjenningen (worker/, se README der). Tom = knappen sier at den ikke er slått på ennå.
window.MATGLEDE_AI_URL = "https://matglede-bilde.matglede-bilde.workers.dev";
