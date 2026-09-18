# Module d'observabilité et de supervision

Ce projet met en place un environnement de **supervision, observabilité et diagnostic d'incidents** basé sur Docker.

L'objectif du lab est de centraliser les métriques, journaux et alertes, puis de tester la capacité de diagnostic à l'aide de **pannes simulées par injection**.

## Stack utilisée

- **Grafana** : visualisation des métriques et tableaux de bord
- **Prometheus** : collecte des métriques et évaluation des règles d'alerte
- **Alertmanager** : gestion et routage des alertes
- **Elasticsearch** : stockage et indexation des journaux
- **Logstash** : collecte et traitement des logs
- **Kibana** : recherche et visualisation des journaux
- **Blackbox Exporter** : tests de disponibilité et de connectivité
- **Docker Compose** : orchestration de l'environnement
- **Simulateur Python** : génération contrôlée de pannes et de métriques anormales

## Architecture du projet

```text
.
├── alertmanager/          # Configuration Alertmanager
├── alert-receiver/        # Récepteur Python des alertes
├── blackbox/              # Configuration Blackbox Exporter
├── certs/                 # Certificats utilisés par la stack
├── diagnostics/           # Captures et éléments de diagnostic
├── injects/               # Scénarios de panne
│   ├── 11-dns
│   ├── 12-reseau
│   ├── 13-dhcp
│   ├── 14-tls
│   ├── 15-backup
│   ├── 16-auth
│   ├── 17-disque
│   ├── 18-conteneur
│   ├── 19-dependance
│   ├── 20-securite
│   ├── preuves
│   └── simulateur/
├── logstash/              # Configuration et pipelines Logstash
├── prometheus/            # Configuration, jobs et règles Prometheus
├── tls-beats/             # Certificats TLS Linux / Windows / serveur
├── compose.yaml
├── compose.override.yaml
├── compose.injects.yaml
├── compose.inject18.yml
├── compose.inject19.yml
└── compose.simulateur.yml
```

## Scénarios d'injection

| ID | Scénario | Exemple d'effet observé |
|---:|---|---|
| 11 | DNS | Requêtes DNS en échec ou lentes |
| 12 | Réseau | Hausse des erreurs réseau et de la latence |
| 13 | DHCP | Pool DHCP presque ou totalement épuisé |
| 14 | TLS | Certificat proche de son expiration |
| 15 | Sauvegarde | Sauvegarde incomplète |
| 16 | Authentification | Backend d'authentification indisponible / échecs massifs |
| 17 | Stockage | Latence élevée sur les opérations disque |
| 18 | Conteneur | Conteneur instable / crash loop |
| 19 | Dépendance | Dépendance applicative indisponible |
| 20 | Sécurité | Activité d'authentification inhabituelle |

Les scénarios servent à provoquer volontairement des anomalies afin de vérifier :

1. leur détection par Prometheus ;
2. le déclenchement des alertes ;
3. leur affichage dans Grafana ;
4. la présence d'éléments de diagnostic dans les métriques et les logs ;
5. la capacité à identifier la cause et proposer une remédiation.

## Démarrage

Depuis la racine du projet :

```bash
docker compose up -d
```

Selon le scénario étudié, des fichiers Compose complémentaires peuvent être utilisés.

Pour vérifier l'état des conteneurs :

```bash
docker compose ps
```

ou :

```bash
docker ps
```

## Accès aux principaux services

| Service | Adresse locale |
|---|---|
| Grafana | http://127.0.0.1:3000 |
| Prometheus | http://127.0.0.1:9090 |
| Alertmanager | http://127.0.0.1:9093 |
| Kibana | http://127.0.0.1:5601 |
| Elasticsearch | http://127.0.0.1:9200 |
| Blackbox Exporter | http://127.0.0.1:9115 |

## Commandes utiles

### Vérifier les conteneurs

```bash
docker ps
```

### Consulter les ressources

```bash
docker stats --no-stream
```

### Lire les logs d'un service

```bash
docker logs <nom_du_conteneur> --tail 100
```

### Tester Prometheus

```bash
curl -s http://127.0.0.1:9090/-/healthy
```

### Consulter les métriques du simulateur

```bash
curl -s http://127.0.0.1:18083/metrics
```

### Filtrer une famille de métriques

```bash
curl -s http://127.0.0.1:18083/metrics | grep -i dns
curl -s http://127.0.0.1:18083/metrics | grep -i network
curl -s http://127.0.0.1:18083/metrics | grep -i dhcp
curl -s http://127.0.0.1:18083/metrics | grep -i tls
curl -s http://127.0.0.1:18083/metrics | grep -i backup
```

## Méthode de diagnostic attendue

Pour chaque alerte :

```text
Alerte
  ↓
Identifier le service ou le job concerné
  ↓
Consulter la métrique à l'origine de l'alerte
  ↓
Comparer avec l'état système / conteneur / réseau
  ↓
Consulter les événements ou journaux utiles
  ↓
Identifier la cause probable
  ↓
Proposer une solution sans modifier la simulation
```

Le but n'est pas nécessairement de corriger directement la panne injectée, mais de **comprendre ce qui provoque l'alerte et de proposer une remédiation cohérente**.

## Exemple d'analyse

Pour une alerte indiquant une hausse des erreurs réseau :

- identifier l'interface concernée ;
- vérifier les erreurs RX/TX ;
- comparer la latence ;
- contrôler CPU et mémoire ;
- examiner les événements réseau ;
- déterminer si le problème provient de l'hôte, d'un conteneur ou d'un scénario simulé ;
- proposer la correction adaptée.

## Fichiers importants

- `prometheus/prometheus.yml` : configuration Prometheus
- `prometheus/rules/` : règles d'alertes
- `alertmanager/alertmanager.yml` : routage des alertes
- `blackbox/blackbox.yml` : probes Blackbox
- `logstash/pipeline/` : pipelines de collecte des logs
- `injects/simulateur/simulator.py` : simulateur de métriques et d'incidents
- `notes-exploitation.md` : notes d'exploitation du lab

## Objectif pédagogique

Ce lab permet de travailler la chaîne complète de supervision :

**collecte → métriques → logs → visualisation → alerting → diagnostic → proposition de remédiation**

L'environnement est volontairement conçu pour générer des incidents reproductibles afin de s'entraîner sans impacter une infrastructure de production.
