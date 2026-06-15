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