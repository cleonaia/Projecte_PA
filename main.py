import csv
import math
import logging
import pickle
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

def configurar_logging():
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_filename = f"log_{timestamp}.txt"
    logger = logging.getLogger("Recomanador")
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
logger = configurar_logging()
def mostrar_recomanacions(recomanacions: List[Tuple[str, str, float]]):
    if not recomanacions:
        print('No hi ha recomanacions disponibles per a aquest usuari.')
        return

    print('\n' + '='*70)
    print('RECOMANACIONS:')
    print('='*70)
    for i, (item_id, nom, score) in enumerate(recomanacions, 1):
        print(f'{i}. {nom}')
        print(f'   ID: {item_id} | Puntuació predita: {score:.2f}/5.0')
    print('='*70 + '\n')


def mostrar_evaluacio(mae: float, rmse: float):
    print('\n' + '='*70)
    print("RESULTATS DE L'AVALUACIÓ:")
    print('='*70)
    print(f'MAE (Mean Absolute Error):       {mae:.4f}')
    print(f'RMSE (Root Mean Square Error):   {rmse:.4f}')
    print('='*70 + '\n')


def guardar_recomanador(recomanador: Recomanador, nom_archivo: str):
    try:
        with open(nom_archivo, 'wb') as f:
            pickle.dump(recomanador, f)
        logger.info(f"Recomanador guardat a {nom_archivo}")
    except Exception as e:
        logger.error(f"Error en guardar el recomanador: {e}")


def cargar_recomanador(nom_archivo: str) -> Optional[Recomanador]:

    try:
        with open(nom_archivo, 'rb') as f:
            recomanador = pickle.load(f)
        logger.info(f"Recomanador carregat des de {nom_archivo}")
        return recomanador
    except FileNotFoundError:
        logger.debug(f"Fitxer {nom_archivo} no trobat")
        return None
    except Exception as e:
        logger.error(f"Error en carregar el recomanador: {e}")
        return None


def obtenir_nom_archivo_pickle(dataset_type: str, method: str) -> str:
    return f"recommender_{dataset_type}_{method}.dat"

def main():
    
    print('\n' + '='*70)
    print('SISTEMA DE RECOMANACIONS DE ÍTEMS')
    print('='*70)
    logger.info("="*70)
    logger.info("SISTEMA DE RECOMANACIONS - INICIAT")
    logger.info("="*70)
    print('\nConjunts de dades disponibles:')
    print('1. Pel·lícules (MovieLens)')
    print('2. Llibres')
    
    tipus_dades = input('\nTria el tipus de dades (pelis/llibres): ').strip().lower()

    if tipus_dades == 'pelis' or tipus_dades == '1':
        dataset = PelliculesDataset('pelicules_Dataset/ratings.csv', 'pelicules_Dataset/movies.csv')
        dataset_type = 'pelis'
    elif tipus_dades == 'llibres' or tipus_dades == '2':
        dataset = LlibresDataset('Libros_dataset/Ratings.csv', 'Libros_dataset/Users.csv')
        dataset_type = 'llibres'
    else:
        print('Tipus de dades no vàlid.')
        logger.error("S'ha seleccionat un tipus de dataset invàlid")
        return

    try:
        dataset.carregar_dades()
    except FileNotFoundError as e:
        print(f'Error: no s\'ha trobat el fitxer {e.filename}')
        logger.error(f"Fitxer no trobat: {e.filename}")
        return

    usuaris = dataset.obtenir_usuaris()
    if not usuaris:
        print('No hi ha dades disponibles.')
        logger.error("No hi ha dades disponibles en el dataset")
        return

    print(f'Usuaris disponibles ({len(usuaris)} total): {", ".join(usuaris[:10])}...')
    print('Sistemes de recomanació disponibles:')
    print('1. Simple (items més populars)')
    print('2. Col·laboratiu (usuaris similars)')
    if dataset_type == 'pelis':
        print('3. Basat en contingut (TF-IDF)')
    
    tipus_recomana = input('\nTria el tipus de recomanació (simple/col·laboratiu/contingut): ').strip().lower()

    if tipus_recomana == 'simple' or tipus_recomana == '1':
        method = 'simple'
        min_vots = input('Nombre mínim de valoracions (defecte 3): ').strip()
        try:
            min_vots = int(min_vots) if min_vots else 3
        except ValueError:
            min_vots = 3
        pickle_file = obtenir_nom_archivo_pickle(dataset_type, method)
        recomanador = cargar_recomanador(pickle_file)
        if recomanador is None:
            recomanador = RecomanadorSimple(dataset, min_vots)
            guardar_recomanador(recomanador, pickle_file)
    
    elif tipus_recomana == 'col·laboratiu' or tipus_recomana == 'colaboratiu' or tipus_recomana == '2':
        method = 'colaboratiu'
        k_veins = input('Nombre de veïns més similars (defecte 2): ').strip()
        try:
            k_veins = int(k_veins) if k_veins else 2
        except ValueError:
            k_veins = 2
        pickle_file = obtenir_nom_archivo_pickle(dataset_type, method)
        recomanador = cargar_recomanador(pickle_file)
        if recomanador is None:
            recomanador = RecomanadorCollaboratiu(dataset, k_veins)
            guardar_recomanador(recomanador, pickle_file)
    
    elif tipus_recomana == 'contingut' or tipus_recomana == '3':
        if dataset_type != 'pelis':
            print('El dataset de llibres no té característiques per a l\'anàlisi basat en contingut.')
            logger.warning("Intent de fer servir recomanació basada en contingut amb dataset de llibres")
            return
        
        method = 'contingut'
        pickle_file = obtenir_nom_archivo_pickle(dataset_type, method)
        recomanador = cargar_recomanador(pickle_file)
        if recomanador is None:
            try:
                print("Construint matriu TF-IDF (això pot trigar)...")
                recomanador = RecomanadorContingut(dataset)
                guardar_recomanador(recomanador, pickle_file)
            except ValueError as e:
                print(f'Error: {e}')
                logger.error(f"Error al crear recomendador basado en contenido: {e}")
                return
    else:
        print('Tipus de recomanació no vàlid.')
        logger.error("Tipo de recomendador inválido seleccionado")
        return

    while True:
        print('Accions disponibles:')
        print('1. Generar recomanacions')
        print('2. Avaluar recomanador')
        print('3. Sortir')
        
        accio = input('Tria una acció (1/2/3): ').strip()

        if accio == '1' or accio.lower() == 'recomanar':
            usuari_id = input("Introdueix l'ID de l'usuari: ").strip()
            if usuari_id not in usuaris:
                print("Usuari no vàlid.")
                logger.warning(f"Usuari invàlid: {usuari_id}")
                continue

            limit = input('Nombre de recomanacions (defecte 5): ').strip()
            try:
                limit = int(limit) if limit else 5
            except ValueError:
                limit = 5

            print("Calculant recomanacions...")
            logger.info(f"Generant {limit} recomanacions per a l'usuari {usuari_id} ({method})")
            recomanacions = recomanador.recomana(usuari_id, limit)
            mostrar_recomanacions(recomanacions)

        elif accio == '2' or accio.lower() == 'avaluar':
            usuari_id = input("Introdueix l'ID de l'usuari a avaluar: ").strip()

            if usuari_id not in usuaris:
                print("Usuari no vàlid.")
                logger.warning(f"Usuari invàlid per a l'avaluació: {usuari_id}")
                continue

            print("Calculant avaluació...")
            logger.info(f"Avaluant recomanador per a l'usuari {usuari_id}")
            mae, rmse = Evaluador.evaluar_recomendador(recomanador, dataset, usuari_id)
            mostrar_evaluacio(mae, rmse)
            logger.info(f"Resultats: MAE={mae:.4f}, RMSE={rmse:.4f}")

        elif accio == "3" or accio.lower() == "sortir":
            print("Fins aviat!")
            logger.info("Sistema finalitzat")
            break

        else:
            print("Opció no vàlida.")


if __name__ == "__main__":
    main()
