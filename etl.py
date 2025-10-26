#Extract
import subprocess

def run_extract_scripts():
    try:
        print("Lancement de scrap_artif.py...")
        subprocess.run(["python", "scrap_artif.py"], check=True)
        
        print("Lancement de api_reelle2.py...")
        subprocess.run(["python", "api_reelle2.py"], check=True)

        print("Extraction terminée.")
    except: print("Erreur lors de l'exécution")






#Transform




#Load
if __name__ == "__main__":
    run_extract_scripts()