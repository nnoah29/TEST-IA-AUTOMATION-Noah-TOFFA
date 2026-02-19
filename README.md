# FANGA — Automatisation IA pour la classification de fichiers

Il s'agit d'une pipeline d'automatisation IA, qui à pour but de classifier et de renommer automatiquement des fichiers d'organisation de la structure FANGA(société de mobilité électrique 2-roues en Côte d'Ivoire).


---

## Setup et exécution

### Prérequis

- Python 3.10+
- Une clé API **Gemini** (ou **OpenAI**)

### Installation

```bash
# 1. Cloner le dépôt
git clone <url_du_repo>
cd Owner avatar
TEST-IA-AUTOMATION-Noah-TOFFA

# 2. Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env et renseigner votre clé API
```

### Lancement

```bash
# Générer les fichiers mock (10 fichiers de démonstration)
python generate_mocks.py

# Lancer le pipeline
python main.py
```

Les fichiers organisés seront dans `data/fanga_organised/` et le rapport dans `data/fanga_organised/rapport_traitement.json`.



## Architecture

Le projet suis une achitecture modulaire

```
FANGA/
├── main.py                  # Point d'entrée, configure les logs
├── generate_mocks.py        # Génère les fichiers de test (fanga_inbox/)
├── requirements.txt
├── .env.example
│
├── src/
│   ├── config.py            # Paramètres (pydantic-settings, lecture .env)
│   ├── models.py            # Modèles Pydantic (FileAnalysis, ProcessingResult)
│   ├── extractors.py        # Extraction de contenu par type de fichier
│   ├── ai_engine.py         # Moteurs IA (OpenAI & Gemini, pattern Strategy)
│   ├── pipeline.py          # Orchestrateur principal du traitement
│   └── report.py            # Génération du rapport JSON
│
├── data/
│   ├── fanga_inbox/         # Dossier source (fichiers à traiter)
│   ├── fanga_organised/     # Dossier de sortie (fichiers classifiés)
│   │   ├── Contrats/
│   │   ├── Facture/
│   │   ├── Photos/
│   │   ├── Rapports/
│   │   ├── Export_csv/
│   │   ├── Documents_identite/
│   │   ├── Maintenance/
│   │   ├── Autres/
│   │   ├── A_verifier/      # Fichiers dont la confiance est < seuil
│   │   └── rapport_traitement.json
│   └── logs/                # Logs persistés (rotation quotidienne)
│
└── tests/
    └── test_pipeline.py     # Tests unitaires (pytest)
```

### Rôle de chaque module

| Module | Rôle                                                                             |
|---|----------------------------------------------------------------------------------|
| `config.py` | Definition des parametre de configuration externe au code du projet.             |
| `models.py` | Définition des structures de données.                                            |
| `extractors.py` | Extrait le texte des fichiers selon leur extension (PDF, DOCX, XLSX, CSV).       |
| `ai_engine.py` | La couche IA, implémente la logique des appels apis des modeles OpenAI et GOOGLE |
| `pipeline.py` | Orchestre chaque fichier : extraction → analyse IA → renommage → déplacement.    |
| `report.py` | Génère le `rapport_traitement.json` final.                                       |

Le code est modulaire et testable. Et chaque module est indépendant, les uns des autres.

---

## 🧠 Stratégie de classification

### Approche : Structured Output LLM + Prompt Engineering

La classification repose sur un appel LLM unique par fichier avec **sortie structurée Pydantic**, ce qui garantit une réponse JSON valide.

**Pipeline par fichier :**

```
Fichier → Extraction contenu (texte/image) → Prompt LLM contextuel → FileAnalysis (catégorie + score + description) → Renommage → Déplacement
```

**Prompt system :** Le prompt décrit les 8 catégories métier de FANGA avec leurs critères (ex: "Maintenance : bugs applicatifs, captures d'écran d'erreurs, pannes, réparations, entretien matériel/flotte"). Cela ancre la classification dans le contexte métier réel.

**Score de confiance :** Le modèle retourne un score `[0, 1]`. Si `confiance < CONFIDENCE_THRESHOLD` (défaut : 0.7), le fichier est déplacé dans `A_verifier/` avec une note explicative, et le pipeline continue sans interruption.

**Support Vision :** Les fichiers image (`.jpg`, `.png`, `.webp`) sont encodés en base64 et envoyés directement au modèle multimodal (Gemini Vision ou GPT-4o Vision), permettant une classification basée sur le contenu visuel réel.

**Fournisseurs supportés :**

| Provider | Variable `.env` | Modèle par défaut |
|---|---|---|
| Google Gemini | `AI_PROVIDER=gemini` | `gemini-3-flash-preview` |
| OpenAI | `AI_PROVIDER=openai` | `gpt-4o` |

**Robustesse :** Chaque appel LLM est relancé jusqu'à 3 fois avec backoff exponentiel (`tenacity`). Toute exception par fichier est captée : le fichier est déplacé dans `Erreurs/` et le pipeline continue.

---

## Améliorations envisagées à moyen terme

1. **Surveillance de dossier en temps réel** : Remplacer le scan ponctuel par un watcher  pour traiter les fichiers dès leur arrivée dans `fanga_inbox/`.
2. **Détection de doublons** : Calcul de hash (SHA-256) de chaque fichier pour éviter les retraitements et signaler les copies identiques avec des noms différents.
3. **Interface de révision** : Petite UI (Streamlit ou web) pour qu'un opérateur traite rapidement les fichiers dans `A_verifier/` : voir le fichier, valider ou corriger la catégorie proposée.
4. **Notifications** : Envoi de résumé par email ou Slack à la fin de chaque batch (nombre de fichiers traités, erreurs, fichiers à vérifier).
5. **File d'attente** : Pour des volumes importants, placer les fichiers dans une queue (Celery + Redis) pour un traitement asynchrone et horizontal.
6. **Fine-tuning / few-shot** : Enrichir le prompt avec des exemples réels issus du contexte FANGA pour améliorer la précision sur les cas ambigus.

---

## Question finale — Passage à l'échelle

> FANGA prévoit de traiter automatiquement des milliers de fichiers par jour provenant de dizaines d'agences partenaires en Côte d'Ivoire, avec des noms de fichiers parfois incohérents et des formats variés. Comment feriez-vous évoluer votre solution pour répondre à ce volume, garantir la fiabilité de la classification et intégrer une boucle de correction humaine lorsque le modèle se trompe ?

L'architecture actuelle est synchrone et mono-thread. Pour des milliers de fichiers/jour, je migrerais vers une **architecture asynchrone orientée événements** :

- **Ingestion** : Chaque agence partenaire dépose ses fichiers dans un bucket S3 dédié (ou un Google Drive partagé). Un événement `ObjectCreated` déclenche un message dans une **queue** (SQS, RabbitMQ ou Redis Streams).
- **Workers parallèles** : Plusieurs workers Python (`Celery` ou `asyncio`) consomment la queue, chacun traitant un fichier indépendamment.
- **Gestion des doublons** : Chaque fichier est identifié par son hash SHA-256. Si un fichier déjà traité réapparaît (même contenu, nom différent), il est détecté comme doublon sans appel LLM.
- **Stratification par confiance** : Garder le seuil à 70% mais affiner avec des seuils par catégorie (ex: Documents_identite à 85% car plus sensible).
- **Consensus multi-modèles** : Pour les cas ambigus (60–80%), lancer deux modèles (ex: Gemini + GPT-4o) et ne valider que si les deux s'accordent. Sinon → révision humaine.
- **Interface de révision** : Une UI simple (admin web) affiche les fichiers de `A_verifier/` avec leur aperçu, la catégorie proposée par le modèle et son score. L'opérateur peut valider, corriger ou rejeter en un clic.
