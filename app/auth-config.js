// Firebase-oppsett for innlogging. Lim inn verdiene fra Firebase-konsollen
// (Prosjektinnstillinger → Dine apper → Web-app → SDK-oppsett → Config).
// Disse verdiene er ikke hemmelige: de identifiserer bare prosjektet, og tilgangen styres
// av reglene i firestore.rules. La feltene stå tomme for å kjøre appen uten innlogging.
window.MATGLEDE_FIREBASE = {
  apiKey: "",
  authDomain: "",
  projectId: "",
  appId: ""
};
