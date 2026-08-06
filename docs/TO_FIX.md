---
lang: FR
---

# FIXED
- [X] `Surrender` : le joueur qui abandonne gagnait la partie → maintenant l'adversaire gagne (game_logic.py)
- [X] `Disconnect` : crash quand get_opponents retournait list[str] au lieu de User → fixé (websocket.py)
- [X] `beforeNavigate` : fermeture propre du WebSocket quand on quitte le lobby
- [X] `onbeforeunload` : envoie un surrender au backend quand on ferme l'onglet en pleine game
- [X] `UI` : barres de score grisées + label "(Offline)" quand l'adversaire se déconnecte

# RESTE À FAIRE

Quand websocket est fermé sur page lobby -> erreur + renvoye sur page home/login OU reconnection du websocket

Si on quitte la page on est pas retiré de la game / lobby
  -> on peut lancer un quickmatch en revenant sur home alors qu'on fait toujours partie d'un lobby privé techniquement (partiellement fixé par onbeforeunload)

retour en arrière peut rejoindre une game qui n'existe pas (partiellement fixé par beforeNavigate)

si on retourne au lobby et on lance le jeu avant le retour de tous les joueurs ça casse tout. host ne peu plus lancer le jeu.

surrender doesnt do anything when solo game

Add refresh token

remove tout les assert avant de push
