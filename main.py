from etl import run_etl

def main():
    print("Lancement du pipeline VeriPix")
    run_etl()
    print("ETL terminé avec succès !")

if __name__ == "__main__":
    main()
