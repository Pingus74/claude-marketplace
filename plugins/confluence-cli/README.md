# confluence-cli

**Plugin Claude Code**: leggi, crea, aggiorna, cerca pagine Confluence Cloud e carica allegati/immagini — tutto tramite l'API v2 REST di Atlassian.

Permette di chiedere a Claude cose tipo _"leggi questa pagina Confluence"_, _"pubblica il documento X come pagina sotto il parent Y"_, _"cerca tutte le pagine su Gross Negligence nello space CS"_ senza passare da browser o copia-incolla.

**Python 3 standard library only** → zero dipendenze esterne, funziona su macOS, Linux, Windows.

---

## Come funziona

Quando Claude rileva che stai chiedendo qualcosa che riguarda Confluence (URL `atlassian.net/wiki`, parole come "pagina wiki", "Confluence", ID space/page/folder), attiva automaticamente la skill confluence-cli del plugin e invoca uno degli 11 comandi esposti dallo script `scripts/confluence.py`. Le credenziali vengono lette da `~/.atlassian-token` o da env var.

Le **operazioni di scrittura** (create/update/delete/upload) richiedono sempre la tua conferma esplicita nella conversazione prima di essere eseguite — Claude non pubblica niente all'insaputa.

---

## Prerequisiti

- **Claude Code** installato
- **Python 3.8+** (preinstallato su Mac/Linux; Windows: https://www.python.org/downloads/)
- **Account Atlassian** con accesso allo space Confluence da cui vuoi leggere/scrivere
- **API token personale Atlassian** → generabile su https://id.atlassian.com/manage-profile/security/api-tokens (1 minuto)

---

## Installazione

> ⚠️ I comandi che iniziano con `/plugin ...` sono **slash command di Claude Code**. Vanno digitati **nella chat di Claude Code**, non nel terminale zsh/bash.

### 1. Aggiungi il marketplace

Nella chat di Claude Code:

```
/plugin marketplace add https://github.com/Pingus74/claude-marketplace
```

### 2. Installa il plugin

```
/plugin install confluence-cli@pingus74-claude-marketplace
```

Claude Code clonerà il plugin in `~/.claude/plugins/cache/pingus74-claude-marketplace/confluence-cli/<versione>/` e lo renderà disponibile come skill `confluence-cli`.

### Update e uninstall

```
/plugin marketplace update
/plugin uninstall confluence-cli@pingus74-claude-marketplace
/plugin marketplace remove pingus74-claude-marketplace
```

### Uso in sviluppo (senza marketplace)

Se stai sviluppando il plugin e vuoi testarlo senza passare da GitHub:

```
/plugin marketplace add /path/locale/al/checkout/claude-marketplace
/plugin install confluence-cli@pingus74-claude-marketplace
```

---

## Setup iniziale (prima volta, una sola)

Dopo aver installato il plugin, lancia **nel tuo terminale** (non in Claude Code):

```bash
python3 "$(find ~/.claude/plugins -name setup.py -path '*confluence-cli*' 2>/dev/null | head -1)"
```

> Questa riga trova dinamicamente lo script di setup indipendentemente dalla versione/marketplace in cui è installato. Su Windows: `python` al posto di `python3` se l'alias non è configurato.

Lo script ti chiederà:
- **Email Atlassian** (es. `nome.cognome@coverzen.it`)
- **Site** (default `coverzen.atlassian.net`)
- **API token** — input nascosto, incolla con Cmd+V / Ctrl+V. Il terminale non lo mostrerà.

Fa una chiamata di test all'API. Se le credenziali sono valide, salva tutto in `~/.atlassian-token` con permessi `0600` (solo tu puoi leggerlo) e stampa `OK — connected as <Tuo Nome>`. Altrimenti stampa l'errore e ti fa riprovare.

Il token **non passa mai dalla chat con Claude**.

### Aggiornare/cambiare il token

Ri-lancia lo stesso comando: sovrascrive il file dopo conferma.

### Revocare un token

1. Vai su https://id.atlassian.com/manage-profile/security/api-tokens
2. "Revoke" sul token sospetto
3. Generane uno nuovo
4. Ri-lancia setup.py

---

## Come si usa (dalla chat con Claude)

Parli in linguaggio naturale, Claude fa il resto. Esempi:

- _"Leggi la pagina Confluence con ID 41451569 e fammi un riassunto."_
- _"Cerca su Confluence le pagine che parlano di Gross Negligence."_
- _"Prendi il file `gross-negligence-flows.md` del progetto e pubblicalo come pagina Confluence sotto il parent _Tech Specs_ nello space CS."_
- _"Aggiorna la pagina <URL> aggiungendo una sezione 'Monitoring' con questo contenuto: …"_
- _"Carica questo PNG come immagine della pagina <URL> e inseriscila dopo il titolo Overview."_

Claude ti mostra sempre il contenuto da pubblicare prima di ogni operazione di scrittura e aspetta il tuo OK.

---

## Comandi esposti dallo script

| Comando | Cosa fa |
|---|---|
| `whoami` | Identifica l'utente autenticato (health check delle credenziali) |
| `get-space <key>` | Risolve uno space key (es. `CS`) nei suoi dettagli |
| `get-page <id>` | Legge una pagina per ID (formato storage o view) |
| `list-children <pageId>` | Elenca i figli diretti di una pagina |
| `list-folder <folderId>` | Elenca i figli di una folder |
| `search "<CQL>"` | Ricerca CQL (es. `space=CS AND title ~ "RCG"`) |
| `create-page` | Crea una pagina nuova sotto un parent |
| `update-page <id>` | Aggiorna body/titolo di una pagina (auto-increment versione) |
| `delete-page <id>` | Cancella una pagina (irreversibile, richiede conferma esplicita) |
| `list-attachments <id>` | Elenca gli allegati di una pagina |
| `upload-attachment <id> <file>` | Carica un file/immagine come allegato |

Help completo:

```bash
python3 "$(find ~/.claude/plugins -name confluence.py -path '*confluence-cli*' 2>/dev/null | head -1)" --help
```

---

## Fallback a env variables

Se preferisci non avere un file con credenziali, puoi esportarle in sessione:

```bash
export ATLASSIAN_EMAIL=nome.cognome@coverzen.it
export ATLASSIAN_SITE=coverzen.atlassian.net
export ATLASSIAN_API_TOKEN=<il-tuo-token>
```

Gli env var hanno precedenza sul file. Utili in CI.

---

## Sicurezza

- `~/.atlassian-token` ha permessi `0600`: solo il tuo utente lo legge.
- Il token **non è mai scritto in chat** né finisce nei log di Claude. Lo gestisci solo tu in locale.
- Il plugin **non contiene credenziali** — il repo è pubblicabile/cloneable tranquillamente.
- Le operazioni distruttive (delete, overwrite) richiedono conferma esplicita.
- Le operazioni di scrittura mostrano sempre il contenuto prima di pubblicare.

Su Mac con FileVault attivo (default), il file credenziali è cifrato a riposo. Token compromesso → revoca immediata su Atlassian.

---

## Troubleshooting

| Sintomo | Causa | Fix |
|---|---|---|
| `/plugin: command not found` in zsh | Hai digitato uno slash command nel terminale | Digitalo **nella chat di Claude Code**, non nel terminale |
| `Credentials missing` | Mai fatto setup | Lancia `setup.py` (vedi sopra) |
| `HTTP 401 Unauthorized` | Token revocato o sbagliato | Rigenera su Atlassian e ri-lancia `setup.py` |
| `HTTP 403 Forbidden` | Non hai permesso su quello space/pagina | Chiedi al space admin |
| `HTTP 404 Not Found` | ID pagina/folder sbagliato o pagina cancellata | Verifica l'ID; non tirare a indovinare |
| `HTTP 409 Conflict` su update | Qualcun altro ha modificato la pagina dopo il tuo get | Re-fetch e riprova |
| `HTTP 429 Too Many Requests` | Rate limit Atlassian | Aspetta 30-60s |
| Su Windows `python3` non trovato | Alias mancante | Usa `python` al suo posto |

---

## Struttura del plugin

```
plugins/confluence-cli/
├── .claude-plugin/
│   └── plugin.json           # manifest plugin
├── README.md                 # questo file (per umani)
└── skills/
    └── confluence-cli/
        ├── SKILL.md          # istruzioni per Claude (auto-lette)
        ├── scripts/
        │   ├── setup.py      # setup interattivo credenziali
        │   └── confluence.py # CLI con 11 comandi
        ├── templates/        # skeleton storage-format riusabili
        │   ├── spec-api.xml
        │   ├── flow-doc.xml
        │   └── adr.xml
        └── references/
            └── storage-format.md  # cheatsheet XHTML Confluence
```

---

## Versione

**1.0.0** — stabile. Supporto read/write/search/attachments; tutti gli 11 comandi esercitati in test end-to-end contro Confluence Cloud; Python 3 stdlib only; cross-platform.

## Maintainer

Stefano Grechi — <stefano.grechi@coverzen.it>

## Licenza

MIT — vedi [LICENSE](../../LICENSE) nel root del marketplace.
