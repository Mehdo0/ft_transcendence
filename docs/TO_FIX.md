# FIXED
✅ Surrender: le joueur qui abandonne gagnait la partie → maintenant l'adversaire gagne (game_logic.py)
✅ Disconnect: crash quand get_opponents retournait list[str] au lieu de User → fixé (websocket.py)
✅ beforeNavigate: fermeture propre du WebSocket quand on quitte le lobby
✅ onbeforeunload: envoie un surrender au backend quand on ferme l'onglet en pleine game
✅ UI: barres de score grisées + label "(Offline)" quand l'adversaire se déconnecte

# RESTE À FAIRE

Si on clique pas `return to lobby` ⇾ on est pas ajouté a la game d'après -> retour automatique au lobby

Si on quitte la page on est pas retiré de la game / lobby
  -> on peut lancer un quickmatch en revenant sur home alors qu'on fait toujours partie d'un lobby privé techniquement (partiellement fixé par onbeforeunload)

retour en arrière peut rejoindre une game qui n'existe pas (partiellement fixé par beforeNavigate)

Add refresh token

enlever les asserts (juste avant push)

## 🔴 CRITIQUE — (trouvés par test suite 15 juin)

### Double connexion WebSocket écrase la première (websocket.py:30)
`connections[user.username] = websocket` écrase sans fermer l'ancienne.
→ Si un joueur ouvre 2 onglets, la 2ème WS écrase la 1ère.
→ Quand la 2ème se ferme, `disconnect_user` retire le joueur du lobby/game en cours.
→ En cascade : player_left → lobby fermé si host → game à 1 joueur.

**Fix :** fermer l'ancienne connexion avant d'écraser (send_json + close) ou refuser la 2ème.

## 🟡 MEDIUM — (trouvés par test suite 15 juin)

### start_game sans code → return silencieux (game_logic.py:159-162)
Si le client envoie `{"type":"start_game"}` sans `code`, ou code invalide → aucun message d'erreur. Le client attend indéfiniment.

### start_game exclut les joueurs déconnectés sans prévenir (game_logic.py:170-172)
`[player for player in lobby["players"] if player in connections]` — si un joueur est déco, il est exclu silencieusement, la game peut démarrer à 1 joueur.

### Échec auth WS ferme sans message (websocket.py:26-27)
`except Exception: return` → le client reçoit une HTTP 500 générique, zéro explication.
**Fix :** accepter, envoyer `{"type":"error","message":"auth failed"}`, puis fermer.

## 🟢 LOW — (trouvés par test suite 15 juin)

### Mots de passe en clair dans la DB (database.py, services.py:70-72)
Aucun hachage (bcrypt/argon2). Les passwords sont stockés et comparés en clair.

### assert en prod (database.py:94, services.py:30)
`assert user is not None` / `assert isinstance(strokes, list)` → ignorés avec `python -O`.

### Code mort : double except Exception (api.py:74-78)
Le 2ème `except Exception` n'est jamais atteint.

### Pas de rate limiting sur /api/token et /api/register/
Vulnérable au brute force.
