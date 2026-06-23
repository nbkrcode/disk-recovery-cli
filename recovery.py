import os
import errno
import argparse
from tqdm import tqdm  
import hashlib

def lister_fichiers(dossier_source):
    """
    Étape de Pre-Scan : Parcourt le dossier et retourne une liste 
    de tous les chemins absolus des fichiers à copier.
    """
    chemins_fichiers = []
    for dossier_actuel, sous_dossiers, fichiers in os.walk(dossier_source):
        for fichier in fichiers:
            chemins_fichiers.append(os.path.join(dossier_actuel, fichier))
    return chemins_fichiers


def recuperer_fichier(chemin_source, chemin_destination, taille_bloc):
    """ 
    Copie un fichier unique.
    Retourne un code d'état : "SAIN", "PARTIEL" ou "ERREUR"
    """
    try:
        fd_source = os.open(chemin_source, os.O_RDONLY)
        fd_dest = os.open(chemin_destination, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    except OSError:
        # Erreur de droits ou fichier inexistant
        return "ERREUR"

    fichier_est_partiel = False
    hasher=hashlib.sha256()  #calcul du hash pour verif integrité

    while True:
        try:
            data = os.read(fd_source, taille_bloc)
            if not data:
                break
            os.write(fd_dest, data)
            hasher.update(data)  # mise à jour du hash avec les données lues
        except OSError as e:
            if e.errno == errno.EIO:
                # Erreur matérielle détectée : on marque le fichier comme partiellement corrompu
                fichier_est_partiel = True
                
                # On écrit des zéros pour maintenir la structure
                zeros = b'\x00' * taille_bloc
                os.write(fd_dest, zeros)
                hasher.update(zeros)  # mise à jour du hash avec des zéros pour les blocs corrompus
                
                # On saute par-dessus l'erreur
                os.lseek(fd_source, taille_bloc, os.SEEK_CUR)
                continue
            else:
                # Autre erreur critique pendant la lecture
                os.close(fd_source)
                os.close(fd_dest)
                return "ERREUR"

    os.close(fd_source)
    os.close(fd_dest)

    empreinte_finale = hasher.hexdigest() #calcul de l'empreinte finale du fichier copié
    
    # On détermine le statut final du fichier
    if fichier_est_partiel:
        return "PARTIEL", empreinte_finale
    else:
        return "SAIN", empreinte_finale


def recuperer_dossier(dossier_source, dossier_destination, taille_bloc):
    """ Gère la logique globale de récupération avec barre de progression et statistiques """
    
    print(f"\n[1/2] Analyse du dossier source en cours : {dossier_source}")
    liste_fichiers = lister_fichiers(dossier_source)
    total_fichiers = len(liste_fichiers)
    
    if total_fichiers == 0:
        print("Aucun fichier trouvé dans le dossier source.")
        return

    print(f"      -> {total_fichiers} fichiers trouvés.\n")
    print(f"[2/2] Démarrage de la récupération vers : {dossier_destination}\n")

    # Initialisation de nos compteurs de statistiques
    stats = {
        "SAIN": 0,
        "PARTIEL": 0,
        "ERREUR": 0
    }

    # Création de la barre de progression tqdm
    barre_progression = tqdm(liste_fichiers, desc="Récupération", unit="fichier")

    for chemin_complet_source in barre_progression:
        # 1. Préparation des chemins
        chemin_relatif = os.path.relpath(chemin_complet_source, dossier_source)
        chemin_complet_dest = os.path.join(dossier_destination, chemin_relatif)
        
        # 2. Création des dossiers cibles si nécessaires
        dossier_parent_dest = os.path.dirname(chemin_complet_dest)
        os.makedirs(dossier_parent_dest, exist_ok=True)
        
        # 3. Lancement de la copie et récupération du statut
        statut, empreinte = recuperer_fichier(chemin_complet_source, chemin_complet_dest, taille_bloc)
        
        if empreinte:
            with open(os.path.join(dossier_destination, "rapport_hashes.txt"), "a") as f_rapport:
                f_rapport.write(f"{empreinte}  {chemin_relatif}\n")

        # 4. Mise à jour des statistiques
        stats[statut] += 1

    # --- AFFICHAGE DU RAPPORT FINAL ---
    pourcentage_reussite = ((stats["SAIN"] + stats["PARTIEL"]) / total_fichiers) * 100
    
    print("\n" + "="*50)
    print(" 📊 RAPPORT DE RÉCUPÉRATION")
    print("="*50)
    print(f" Total des fichiers traités : {total_fichiers}")
    print(f" ✅ Fichiers copiés 100% intacts   : {stats['SAIN']}")
    print(f" ⚠️  Fichiers sauvés partiellement  : {stats['PARTIEL']} (Secteurs défectueux ignorés)")
    print(f" ❌ Fichiers totalement perdus     : {stats['ERREUR']}")
    print("-" * 50)
    print(f" Taux de récupération global      : {pourcentage_reussite:.2f}%")
    print("="*50 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Outil CLI pour récupérer des données sur des disques corrompus.",
        epilog="Exemple : python recovery.py /Volumes/Source /Volumes/Dest --block-size 4096"
    )

    parser.add_argument("source", help="Le chemin du dossier corrompu à lire")
    parser.add_argument("destination", help="Le chemin du dossier où sauvegarder les données")
    parser.add_argument(
        "-b", "--block-size", 
        type=int, 
        default=4096, 
        help="Taille des blocs de lecture en octets (défaut: 4096)"
    )

    args = parser.parse_args()

    if not os.path.exists(args.source):
        print(f"[ERREUR FATALE] Le dossier source '{args.source}' n'existe pas.")
        return

    # Lancement du processus
    recuperer_dossier(args.source, args.destination, args.block_size)

if __name__ == "__main__":
    main()