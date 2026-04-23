# confluence-cli

Skill per Claude Code: leggere, creare, aggiornare, cercare pagine Confluence Cloud e caricare allegati/immagini — tutto tramite l'API v2 REST di Atlassian.

Permette di chiedere a Claude cose tipo _"leggi questa pagina Confluence"_, _"pubblica il documento X come pagina sotto il parent Y"_, _"cerca tutte le pagine su gross negligence nello space CS"_ senza dover passare da browser o copia-incolla.

**Python 3 standard library only** → funziona su macOS, Linux e Windows senza installare dipendenze.

---

## Come funziona

Quando Claude rileva che stai chiedendo qualcosa che riguarda Confluence (URL `atlassian.net/wiki`, parole come "pagina wiki", "Confluence", ID space/page/folder), attiva automaticamente questa skill e invoca uno degli 11 comandi esposti dallo script `scripts/confluence.py`. Le credenziali vengono lette da `~/.atlassian-token` o da env vars.

Le **operazioni di scrittura** (create/update/delete/upload) richiedono sempre la tua conferma esplicita nella conversazione prima di essere eseguite — Claude non pubblica niente all'insaputa.

---

## Prerequisiti

- **Python 3.8+** (di solito preinstallato su Mac/Linux; su Windows: https://www.python.org/downloads/)
- **Account Atlassian** con accesso allo space Confluence da cui vuoi leggere/scrivere
- **API token personale** → generabile su https://id.atlassian.com/manage-profile/security/api-tokens (1 minuto)

---

## Installazione

### Come skill utente (metodo attuale)

Copia la cartella in `~/.claude/skills/`:

```bash
# via rsync (Mac/Linux)
rsync -a /path/alla/cartella/confluence-cli/ ~/.claude/skills/confluence-cli/

# oppure via git clone (se distribuita su repo)
git clone <url-repo> ~/.claude/skills/confluence-cli
```

Claude la rileva automaticamente alla prossima sessione.

### Come plugin (in futuro)

Quando sarà confezionata come plugin Coverzen:

```
/plugin marketplace add <url-repo-coverzen-plugins>
/plugin install confluence
```

---

## Setup iniziale (prima volta)

Una volta sola, sul tuo Mac/Linux/Windows, lancia:

```bash
python3 ~/.claude/skills/confluence-cli/scripts/setup.py
```

> Su Windows: `python` al posto di `python3` se l'alias non è configurato.

Lo script ti chiederà:
- **Email Atlassian** (es. `nome.cognome@coverzen.it`)
- **Site** (default `coverzen.atlassian.net`)
- **API token** — input nascosto, incolla con Cmd+V / Ctrl+V. Il terminale non lo mostrerà.

Fa una chiamata di test all'API. Se le credenziali sono valide, salva tutto in `~/.atlassian-token` con permessi `0600` (solo tu puoi leggerlo) e stampa `OK — connected as <Tuo Nome>`. Altrimenti stampa l'errore e ti fa riprovare.

Il token **non passa mai dalla chat con Claude**.

### Aggiornare/cambiare il token

Ri-lancia `setup.py`: sovrascrive il file esistente dopo conferma.

### Revocare un token

Se pensi che un token sia stato esposto:
1. Vai su https://id.atlassian.com/manage-profile/security/api-tokens
2. "Revoke" sul token sospetto
3. Generane uno nuovo
4. Ri-lancia `setup.py`

---

## Come si usa (dalla chat con Claude)

Parli in linguaggio naturale, Claude fa il resto. Esempi:

- _"Leggi la pagina Confluence con ID 41451569 e fammi un riassunto."_
- _"Cerca su Confluence le pagine che parlano di Gross Negligence."_
- _"Prendi il file `gross-negligence-flows.md` nel progetto e pubblicalo come pagina Confluence sotto il parent _Tech Specs_ nello space CS."_
- _"Aggiorna la pagina <URL> aggiungendo una sezione 'Monitoring' con questo contenuto: …"_
- _"Carica questo PNG come immagine della pagina <URL> e inseriscila dopo il titolo Overview."_

Claude ti mostrerà il contenuto da pubblicare prima di ogni operazione di scrittura e aspetterà il tuo OK.

---

## Cosa può fare (comandi esposti)

| Comando | Cosa fa |
|---|---|
| `whoami` | Identifica l'utente autenticato (health check delle credenziali) |
| `get-space <key>` | Risolve uno space key (es. `CS`) nei suoi dettagli |
| `get-page <id>` | Legge una pagina per ID (formato storage o view) |
| `list-children <pageId>` | Elenca i figli diretti di una pagina |
| `list-folder <folderId>` | Elenca i figli di una folder |
| `search "<CQL>"` | Ricerca CQL (es. `space=CS AND title ~ "RCG"`) |
| `create-page` | Crea una pagina nuova sotto un parent |
| `update-page <id>` | Aggiorna body/titolo di una pagina (auto-increment della versione) |
| `delete-page <id>` | Cancella una pagina (irreversibile, richiede conferma esplicita) |
| `list-attachments <id>` | Elenca gli allegati di una pagina |
| `upload-attachment <id> <file>` | Carica un file/immagine come allegato |

Documentazione comandi: `python3 ~/.claude/skills/confluence-cli/scripts/confluence.py --help`.

---

## Fallback a env variables

Se preferisci non avere un file con credenziali, puoi esportarle in sessione:

```bash
export ATLASSIAN_EMAIL=nome.cognome@coverzen.it
export ATLASSIAN_SITE=coverzen.atlassian.net
export ATLASSIAN_API_TOKEN=<il-tuo-token>
```

Gli env var hanno la precedenza sul file. Utile anche per CI.

---

## Sicurezza

- `~/.atlassian-token` ha permessi `0600`: solo il tuo utente lo legge.
- Il token **non è mai scritto in chat** né finisce in log di Claude. Lo gestisci solo tu in locale.
- Il plugin/skill **non contiene credenziali** — puoi fare commit/push tranquillo.
- Le operazioni distruttive (delete, overwrite) richiedono conferma esplicita.
- Le operazioni di scrittura mostrano sempre il contenuto prima di pubblicare.

Se il Mac ha FileVault attivo (default), il file è cifrato a riposo. Con un token API compromesso, Atlassian permette revoca immediata.

---

## Troubleshooting

| Sintomo | Causa | Fix |
|---|---|---|
| `Credentials missing` | Mai fatto setup | Lancia `scripts/setup.py` |
| `HTTP 401 Unauthorized` | Token revocato o sbagliato | Rigenera su Atlassian + `setup.py` |
| `HTTP 403 Forbidden` | Non hai permesso su quello space/pagina | Chiedi al space admin |
| `HTTP 404 Not Found` | ID pagina/folder sbagliato o pagina cancellata | Verifica l'ID; non tirare a indovinare |
| `HTTP 409 Conflict` su update | Qualcun altro ha modificato la pagina dopo il tuo get | Re-fetch e riprova |
| `HTTP 429 Too Many Requests` | Rate limit Atlassian | Aspetta 30-60s |
| Su Windows `python3` non trovato | Alias mancante | Usa `python` |

---

## Struttura

```
confluence-cli/
├── SKILL.md                   # Istruzioni per Claude (auto-lette)
├── README.md                  # Questo file (per umani)
├── scripts/
│   ├── setup.py               # Setup interattivo credenziali
│   └── confluence.py          # CLI con 11 comandi
├── templates/                 # Skeleton storage-format riusabili
│   ├── spec-api.xml           # Template doc endpoint REST
│   ├── flow-doc.xml           # Template doc flusso/architettura
│   └── adr.xml                # Template Architecture Decision Record
└── references/
    └── storage-format.md      # Cheatsheet formato Confluence (XHTML esteso)
```

---

## Versione

**1.0.0** — supporto read/write/search/attachments, Python 3 stdlib only, cross-platform.

## Maintainer

Coverzen Engineering — contattare il team su Slack `#engineering` per segnalazioni.

## Licenza

Uso interno Coverzen.
