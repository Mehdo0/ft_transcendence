# 🔍 ft_transcendence — Rapport de Test

**Date :** 15 juin 2026  
**Branche :** `dev`  
**Méthode :** 24 tests automatisés (API REST + WebSocket) + code review

---

## 📊 RÉSUMÉ : 22/24 tests passés ✅

| Domaine | Tests | Passés | Échoués |
|---------|-------|--------|---------|
| Auth (register, login, JWT, logout) | 6 | 6 | 0 |
| Ranking / Stats | 4 | 4 | 0 |
| WebSocket + Lobby | 8 | 7 | 1 |
| Game Flow | 2 | 1 | 1 |
| Matchmaking | 4 | 4 | 0 |
| **TOTAL** | **24** | **22** | **2** |

Les 2 échecs sont causés par **un seul bug racine** (connexion WebSocket overwrite).

---

## 🔴 BUGS CRITIQUES

### #1 — Double connexion WebSocket écrase la première
**Fichier :** `backend/ws/websocket.py:30`  
**Sévérité :** 🔴 CRITICAL

```python
connections[user.username] = websocket  # écrase sans fermer l'ancienne
```

**Problème :** Si un joueur ouvre 2 onglets avec le même compte, la 2ème connexion WebSocket écrase la 1ère dans le dictionnaire `connections`. Quand la 2ème se ferme, `disconnect_user` retire le joueur du lobby/game en cours — même si le 1er onglet est toujours actif.

**Impact en cascade :**
- ❌ Le joueur est expulsé de son lobby ("player_left")
- ❌ Si c'est le host qui est expulsé, le lobby est fermé ("lobby_closed")
- ❌ `start_game` crée une game à 1 joueur car l'adversaire n'est plus dans `connections`
- ❌ L'ancien WebSocket devient orphelin (toujours ouvert mais plus tracké)

**Fix suggéré :**
```python
# Avant d'écraser, fermer l'ancienne connexion avec un message
old_ws = connections.get(user.username)
if old_ws and old_ws != websocket:
    try:
        await old_ws.send_json({"type": "duplicate_connection"})
        await old_ws.close()
    except:
        pass
connections[user.username] = websocket
```

---

## 🟡 BUGS MEDIUM

### #2 — `start_game` : return silencieux sans code
**Fichier :** `backend/game/game_logic.py:159-162`

```python
async def start_game(payload: dict, user: User):
    code = payload.get("code")
    if code not in lobbies:
        return  # ❌ aucun message d'erreur au client
```

Si le client envoie `{"type": "start_game"}` sans `code`, ou avec un code invalide, le serveur ne répond rien. Le client attend indéfiniment.

**Fix :** Envoyer un message d'erreur avant le return.

---

### #3 — `start_game` exclut silencieusement les joueurs déconnectés
**Fichier :** `backend/game/game_logic.py:170-172`

```python
players = get_users(
    [player for player in lobby["players"] if player in connections]
)
```

Si un joueur du lobby n'est pas dans `connections`, il est silencieusement exclu. La game peut démarrer à 1 joueur. Aucune erreur ni au client ni dans les logs.

**Fix :** Vérifier que tous les joueurs du lobby sont connectés, sinon envoyer une erreur.

---

### #4 — Échec d'auth WebSocket : fermeture sans message d'erreur
**Fichier :** `backend/ws/websocket.py:26-27`

```python
except Exception:
    return  # ferme la connexion sans explication
```

Le client reçoit une erreur HTTP 500 générique sans savoir que c'est un problème d'auth.

**Fix :** Accepter la connexion, envoyer `{"type": "error", "message": "authentication failed"}`, puis fermer.

---

## 🟢 BUGS LOW

### #5 — `assert` dans le code de production
**Fichiers :**
- `backend/core/database.py:94` — `assert user is not None`
- `backend/services/services.py:30` — `assert isinstance(strokes, list)`

Les `assert` sont ignorés si Python est lancé avec `-O` (optimized). Utiliser des exceptions explicites.

---

### #6 — Code mort : double `except Exception`
**Fichier :** `backend/api/api.py:74-78`

```python
except Exception as e:
    ...
except Exception as e:  # ❌ jamais atteint
    ...
```

Le deuxième `except` est inatteignable.

---

### #7 — Pas de rate limiting sur auth
`/api/token` et `/api/register/` n'ont pas de rate limiting → vulnérable au brute force.

---

### #8 — Mots de passe en clair
**Fichier :** `backend/core/database.py` + `backend/services/services.py:70-72`

Les mots de passe sont stockés et comparés en clair. Aucun hachage (bcrypt, argon2).

---

## 🔵 NOTES / AMÉLIORATIONS SUGGÉRÉES

| # | Description | Fichier |
|---|-------------|---------|
| 9 | Pas de refresh token — JWT expire, pas de mécanisme de renouvellement | `services.py` |
| 10 | `max(scores.values())` peut planter si scores vide | `game_logic.py:138` |
| 11 | `handle_disconnect_grace_period` : si `get_user(opponents[0])` échoue (user supprimé), la game reste bloquée | `websocket.py:130-131` |
| 12 | Cookie `max_age` utilise `ACCESS_TOKEN_EXPIRE_MINUTES * 60` mais `exp` dans le JWT peut diverger | `api.py:58`, `services.py:82` |

---

## ✅ CE QUI FONCTIONNE BIEN

- ✅ Auth complète (register → login → JWT cookie → /me → logout)
- ✅ Duplicate register rejeté (409)
- ✅ Login mauvais password / user inexistant rejeté (401)
- ✅ `/me` protégé sans cookie (403)
- ✅ Lobby : création, join, double join rejeté, lobby inexistant rejeté
- ✅ Matchmaking : file d'attente, match trouvé, ranked=True
- ✅ Ranking + stats utilisateur
- ✅ AI guesses reçus après strokes
- ✅ Score updates broadcastés
- ✅ Reconnexion avec grace period (logique en place)

---

## 🎯 PRIORITÉ DE FIX

1. **🔴 Immédiat** — Bug #1 (double connexion WS) — casse tout le game flow
2. **🟡 Semaine** — Bugs #2, #3, #4 (start_game silencieux, exclusion joueurs, auth WS)
3. **🟢 Avant soutenance** — #5, #6, #7, #8 (asserts, code mort, rate limiting, hashage mdp)
4. **🔵 Nice to have** — #9-12 (refresh token, edge cases)
