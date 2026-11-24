# Matglede – notater for Claude

## Kodekart (Graphify)
Les `graphify-out/GRAPH_REPORT.md` før du leter i koden. Den viser moduler, sentrale
funksjoner ("god nodes") og hvordan delene henger sammen, så du slipper å lese alt.

Oppdater kartet når koden er endret (tar sekunder, ingen API-kostnad):

```
pip install graphifyy
graphify update .
```

Ekskluderte filer står i `.graphifyignore` (vendor-React, logoer, bilder, seed-data).
Bare `GRAPH_REPORT.md` committes. `graph.json` og `graph.html` lages lokalt og kan
brukes til oppslag, f.eks. `graphify query "handleliste"` eller `graphify explain "pick_product"`.
