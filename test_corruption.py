import os
import errno
from unittest.mock import patch

# 1. On importe ta fonction depuis ton fichier principal (imaginons qu'il s'appelle recovery.py)
from recovery import recuperer_fichier

print("--- CRÉATION DU FICHIER TEST ---")
with open("fichier_sain.txt", "wb") as f:
    # On crée un fichier de 30 octets
    f.write(b"AAAAAAAAAABBBBBBBBBBCCCCCCCCCC") 

# 2. On sauvegarde la vraie fonction os.read pour s'en servir quand même
vrai_os_read = os.read
compteur_lecture = 0

# 3. On crée le "piège" : notre fausse fonction de lecture
def fausse_lecture(fd, taille):
    global compteur_lecture
    compteur_lecture += 1
    
    # Au 2ème tour de boucle, on simule l'explosion du disque dur !
    if compteur_lecture == 2:
        print("Simulation du crash secteur...")
        erreur = OSError("Crash disque dur simulé")
        erreur.errno = errno.EIO
        raise erreur
        
    # Sinon, on lit normalement avec la vraie fonction
    return vrai_os_read(fd, taille)

print("\n--- DÉMARRAGE DE LA RÉCUPÉRATION ---")
# 4. Magie : patch remplace os.read par fausse_lecture uniquement dans ce bloc 'with'
with patch('os.read', side_effect=fausse_lecture):
    # On lit par blocs de 10 octets pour avoir 3 tours de boucle
    statut, empreinte = recuperer_fichier("fichier_sain.txt", "fichier_sauve.txt", 10)

print("\n--- RÉSULTAT DU TEST ---")
print(f"Statut final : {statut}")
print(f"Empreinte SHA-256 : {empreinte}")

# 5. Vérification visuelle
with open("fichier_sauve.txt", "rb") as f:
    contenu_sauve = f.read()
    print(f"Contenu récupéré : {contenu_sauve}")