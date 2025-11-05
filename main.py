import subprocess
import sys

def main():
    print("Lancement du pipeline VeriPix")

    # Création 
    print("Création de la base")
    subprocess.run([sys.executable, "creation_sqlite.py"])

    # ELT complet (extract load transform)
    print("Lancement de l'ETL")
    subprocess.run([sys.executable, "etl.py"])

    print("Fin")

if __name__ == "__main__":
    main()
