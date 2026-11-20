// Innlogging og lagring per bruker med Firebase (Google-konto eller e-post og passord).
// Appen bruker bare window.MatgledeAuth. Uten oppsett i auth-config.js er innlogging av,
// og appen virker som før uten konto.
(function () {
  var SDK = 'https://www.gstatic.com/firebasejs/10.12.2/';
  var cfg = window.MATGLEDE_FIREBASE || null;
  var configured = !!(cfg && cfg.apiKey && cfg.projectId);
  var listeners = [];
  var current = null;
  var auth = null, db = null, ready = null;

  function load(src) {
    return new Promise(function (resolve, reject) {
      var s = document.createElement('script');
      s.src = src; s.async = false;
      s.onload = resolve;
      s.onerror = function () { reject(new Error('Fikk ikke lastet ' + src)); };
      document.head.appendChild(s);
    });
  }

  function toUser(u) {
    if (!u) return null;
    return { uid: u.uid, name: u.displayName || '', email: u.email || '', photo: u.photoURL || '',
      google: (u.providerData || []).some(function (p) { return p && p.providerId === 'google.com'; }) };
  }

  function emit() { listeners.forEach(function (cb) { try { cb(current); } catch (e) { console.error(e); } }); }

  function start() {
    if (!configured) return Promise.reject(new Error('not-configured'));
    if (ready) return ready;
    ready = load(SDK + 'firebase-app-compat.js')
      .then(function () { return Promise.all([load(SDK + 'firebase-auth-compat.js'), load(SDK + 'firebase-firestore-compat.js')]); })
      .then(function () {
        var app = window.firebase.initializeApp(cfg);
        auth = app.auth();
        db = app.firestore();
        auth.languageCode = 'no';
        auth.getRedirectResult().catch(function () {});
        auth.onAuthStateChanged(function (u) { current = toUser(u); emit(); });
      });
    return ready;
  }

  // Firebase-feilkoder -> norsk tekst
  var MSG = {
    'auth/invalid-email': 'E-postadressen ser ikke riktig ut.',
    'auth/missing-password': 'Skriv inn et passord.',
    'auth/weak-password': 'Passordet må ha minst 6 tegn.',
    'auth/email-already-in-use': 'Det finnes allerede en konto med denne e-posten. Logg inn i stedet.',
    'auth/invalid-credential': 'Feil e-post eller passord.',
    'auth/wrong-password': 'Feil e-post eller passord.',
    'auth/user-not-found': 'Fant ingen konto med denne e-posten.',
    'auth/too-many-requests': 'For mange forsøk. Vent litt og prøv igjen.',
    'auth/popup-closed-by-user': 'Innloggingen ble avbrutt.',
    'auth/cancelled-popup-request': 'Innloggingen ble avbrutt.',
    'auth/unauthorized-domain': 'Dette nettstedet er ikke godkjent for innlogging ennå (Firebase: Authorized domains).',
    'auth/operation-not-allowed': 'Denne innloggingsmåten er ikke slått på i Firebase ennå.',
    'auth/network-request-failed': 'Ingen nettforbindelse.',
    'not-configured': 'Innlogging er ikke satt opp ennå.'
  };
  function message(e) { return MSG[(e && (e.code || e.message)) || ''] || 'Noe gikk galt. Prøv igjen.'; }

  window.MatgledeAuth = {
    configured: configured,
    message: message,
    init: function () { return configured ? start().catch(function (e) { console.error(e); }) : Promise.resolve(); },
    onChange: function (cb) { listeners.push(cb); if (current) cb(current); },
    user: function () { return current; },
    signInGoogle: function () {
      return start().then(function () {
        var p = new window.firebase.auth.GoogleAuthProvider();
        p.setCustomParameters({ prompt: 'select_account' });
        return auth.signInWithPopup(p).catch(function (e) {
          if (e && e.code === 'auth/popup-blocked') return auth.signInWithRedirect(p);
          throw e;
        });
      });
    },
    signInEmail: function (email, pw) { return start().then(function () { return auth.signInWithEmailAndPassword(email, pw); }); },
    signUpEmail: function (email, pw, name) {
      return start().then(function () { return auth.createUserWithEmailAndPassword(email, pw); })
        .then(function (cred) {
          if (!name) return cred;
          return cred.user.updateProfile({ displayName: name }).then(function () { current = toUser(cred.user); emit(); return cred; });
        });
    },
    signOut: function () { return auth ? auth.signOut() : Promise.resolve(); },
    // Brukerdata: ett dokument per bruker i users/{uid}
    loadData: function (uid) {
      return start().then(function () { return db.collection('users').doc(uid).get(); })
        .then(function (d) { return d.exists ? (d.data().app || null) : null; });
    },
    saveData: function (uid, data) {
      return start().then(function () {
        return db.collection('users').doc(uid).set({ app: data, updatedAt: window.firebase.firestore.FieldValue.serverTimestamp() }, { merge: true });
      });
    }
  };
})();
