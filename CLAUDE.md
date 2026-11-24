# Matglede

Norsk app for ukeplan, oppskrifter og handleliste. Python-delen her (`matglede/`, `db/`, `seed/`, `tests/`) bygger varedatabasen fra Kassalapp. Se README.md for datamodell og kommandoer.

## Kodekart

Les `docs/GRAPH_REPORT.md` før du leter rundt i filene. Det er et kunnskapskart (Graphify, 23.11.2026) over hele prosjektet: hvilke funksjoner som henger sammen, de viktigste nodene og hvilke deler som hører til hvilket område. Bruk det til å finne riktig fil, og les så bare de filene du trenger.

Kartet dekker også appen (`app/`) og AI-workeren, som ikke ligger på main. Stemmer kartet ikke med koden, er det koden som gjelder.

## Tester

`python -m unittest discover tests`
