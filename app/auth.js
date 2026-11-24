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
    return { uid: u.uid, name: u.displayName || '', email: (u.email || '').toLowerCase(), photo: u.photoURL || '', verified: !!u.emailVerified,
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
    'auth/missing-email': 'Skriv inn e-postadressen din.',
    'auth/network-request-failed': 'Ingen nettforbindelse.',
    'not-configured': 'Innlogging er ikke satt opp ennå.'
  };
  function message(e) { return MSG[(e && (e.code || e.message)) || ''] || 'Noe gikk galt. Prøv igjen.'; }

  function FV() { return window.firebase.firestore.FieldValue; }
  function setHousehold(uid, hid) {
    return db.collection('users').doc(uid).set({ household: hid || FV().delete() }, { merge: true });
  }

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
    resetPassword: function (email) { return start().then(function () { return auth.sendPasswordResetEmail(email); }); },
    // Kortvarig bevis på hvem brukeren er, for kall til bildegjenkjenningen (worker/)
    idToken: function () { return auth && auth.currentUser ? auth.currentUser.getIdToken() : Promise.reject(new Error('not-signed-in')); },
    signOut: function () { return auth ? auth.signOut() : Promise.resolve(); },
    // Brukerdata: ett dokument per bruker i users/{uid} = { app, household? }
    loadData: function (uid) {
      return start().then(function () { return db.collection('users').doc(uid).get(); })
        .then(function (d) { return d.exists ? d.data() : null; });
    },
    // E-postkontoer må bekrefte adressen før de kan se invitasjoner (se firestore.rules)
    sendVerify: function () { return auth.currentUser.sendEmailVerification(); },
    reloadUser: function () {
      return auth.currentUser.reload().then(function () { return auth.currentUser.getIdToken(true); })
        .then(function () { current = toUser(auth.currentUser); emit(); return current; });
    },
    saveData: function (uid, data) {
      return start().then(function () {
        return db.collection('users').doc(uid).set({ app: data, updatedAt: window.firebase.firestore.FieldValue.serverTimestamp() }, { mergeFields: ['app', 'updatedAt'] }); // app byttes helt, så slettede nøkler forsvinner
      });
    },
    // Delt app: households/{id} = { members: [uid], names: {uid: navn}, invited: [e-post], app: {...} }.
    // invites/{e-post} = { hid, from } peker den inviterte til husholdningen.
    hh: {
      create: function (uid, name, data) {
        var ref = db.collection('households').doc(), o = { members: [uid], names: {}, invited: [], app: data };
        o.names[uid] = name;
        return ref.set(o).then(function () { return setHousehold(uid, ref.id); }).then(function () { return ref.id; });
      },
      watch: function (hid, cb, err) { return db.collection('households').doc(hid).onSnapshot(cb, err); },
      // Bare feltene som er endret skrives, så to som endrer hver sin ting samtidig ikke overskriver hverandre
      save: function (hid, changed) {
        var o = { updatedAt: FV().serverTimestamp() };
        Object.keys(changed).forEach(function (k) { o['app.' + k] = changed[k]; });
        return db.collection('households').doc(hid).update(o);
      },
      invite: function (hid, email, from) {
        return db.collection('households').doc(hid).update({ invited: FV().arrayUnion(email) })
          .then(function () { return db.collection('invites').doc(email).set({ hid: hid, from: from }); });
      },
      uninvite: function (hid, email) {
        return db.collection('households').doc(hid).update({ invited: FV().arrayRemove(email) })
          .then(function () { return db.collection('invites').doc(email).delete(); });
      },
      findInvite: function (email) {
        return start().then(function () { return db.collection('invites').doc(email).get(); })
          .then(function (d) { return d.exists ? d.data() : null; });
      },
      decline: function (hid, email) {
        return db.collection('invites').doc(email).delete()
          .then(function () { return db.collection('households').doc(hid).update({ invited: FV().arrayRemove(email) }); })
          .catch(function () {}); // husholdningen kan være borte
      },
      join: function (hid, uid, email, name) {
        var o = { members: FV().arrayUnion(uid), invited: FV().arrayRemove(email) };
        o['names.' + uid] = name;
        return db.collection('households').doc(hid).update(o)
          .then(function () { return setHousehold(uid, hid); })
          .then(function () { return db.collection('invites').doc(email).delete().catch(function () {}); });
      },
      // Den som går ut beholder en kopi av det som var delt
      leave: function (hid, uid, data) {
        return db.collection('households').doc(hid).update({ members: FV().arrayRemove(uid) }).catch(function () {})
          .then(function () { return db.collection('users').doc(uid).update({ app: data, household: FV().delete() }); });
      },
      forget: function (uid) { return setHousehold(uid, null); }
    },
    // Anonyme tellere i popular/{nøkkel} = { n }. Se firestore.rules.
    popular: function () {
      return start().then(function () { return db.collection('popular').get(); })
        .then(function (q) { var o = {}; q.forEach(function (d) { o[d.id] = d.data().n || 0; }); return o; });
    },
    bump: function (key, d) {
      return start().then(function () { return db.collection('popular').doc(key).set({ n: window.firebase.firestore.FieldValue.increment(d) }, { merge: true }); });
    }
  };
})();
