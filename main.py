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
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S") #Converteix el temps d'ara a un format de cadena amb estructura YYYYMMDD-HHMMSS
    log_filename = f"log_{timestamp}.txt" #Creem un arxiu per cada execució
    logger = logging.getLogger("Recomanador") #Creem un logger amb el nom "Recomanador"
    logger.setLevel(logging.DEBUG) #Donem un nivell de logging DEBUG al logger
    file_handler = logging.FileHandler(log_filename) #Creem un handler que escriu els missatges de log a un arxiu
    file_handler.setLevel(logging.DEBUG) #El arxiu de log guardarà tots els missatges de nivell DEBUG
    console_handler = logging.StreamHandler()#Creem un handler que escriu els missatges de log a la consola
    console_handler.setLevel(logging.INFO) #La consola mostrarà només missatges de nivell INFO
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    #%(asctime)s data i hora, %(levelname)s nivell del missatge (INFO, DEBUG, ERROR), %(message)s el missatge real
    file_handler.setFormatter(formatter) #Apliquem el format al handler de fitxer
    console_handler.setFormatter(formatter) #Apliquem el format al handler de consola
    logger.addHandler(file_handler) #Afegim el handler de fitxer al logger
    logger.addHandler(console_handler) #Afegim el handler de consola al logger
    return logger
logger = configurar_logging()

class DatasetBase(ABC):

    def __init__(self, fitxer_valoracions: str, fitxer_items: str):
        self.fitxer_valoracions = fitxer_valoracions
        self.fitxer_items = fitxer_items
        self.valoracions = []
        self.items = {} #Creem un diccionari per buscar el nom_item amb el seu item_id
        self.valoracions_per_usuari = {} #Creem un diccionari per buscar les valoracions d'un usuari amb el seu usuari_id
        self.valoracions_per_item = {} #Creem un diccionari per buscar les valoracions d'un item amb el seu item_id
        self.num_votes_per_item = {} #Creem un diccionari per guardar el nombre de valoracions per cada item
        self.avg_item_per_item = {} #Creem un diccionari per guardar la mitjana de valoracions per cada item
        self.avg_global_cached = 0 #Creem una variable per guardar la mitjana global de valoracions, que es calcularà un cop carregades les dades

    def carregar_dades(self):
        raise NotImplementedError

    def actualitzar_indices(self):
        self.num_votes_per_item = {item_id: len(puntuacions) for item_id, puntuacions in self.valoracions_per_item.items()}
        self.avg_item_per_item = {item_id: (sum(puntuacions)/len(puntuacions)) for item_id, puntuacions in self.valoracions_per_item.items()}
        self.avg_global_cached = self._calcular_avg_global_cached()
        logger.info(f"Índexs actualitzats. Total d'ítems: {len(self.items)}")

    def _calcular_avg_global_cached(self, min_vots: int = 0) -> float:
        mitjanes = [self.avg_item_per_item[item_id] for item_id, num_vots in self.num_votes_per_item.items() if num_vots >= min_vots]
        if not mitjanes:
            return 0
        return sum(mitjanes)/len(mitjanes)

    def obtenir_usuaris(self) -> List[str]:
        return sorted(self.valoracions_per_usuari.keys()) #Retornem una llista ordenada dels usuaris que han fet valoracions

    def obtenir_valoracions_usuari(self, usuari_id: str) -> Dict[str, float]:
        return dict(self.valoracions_per_usuari.get(usuari_id, {})) #Retornem un diccionari de les valoracions d'un usuari, on les claus són els item_id i els valors són les puntuacions, si l'usuari no ha fet valoracions, retornem un diccionari buit.

    def get_avg_global(self, min_vots: int = 0) -> float:
        if min_vots <= 0:
            return self.avg_global_cached 
        return self._calcular_avg_global_cached(min_vots)

    def get_item_avg(self, item_id: str) -> float:
        return self.avg_item_per_item.get(item_id, 0)

    def get_num_votes(self, item_id: str) -> int:
        return self.num_votes_per_item.get(item_id, 0)

    def get_items_no_valorats(self, usuari_id: str) -> List[str]:
        valorats = set(self.valoracions_per_usuari.get(usuari_id, {}).keys())
        return [item_id for item_id in self.items if item_id not in valorats]

    def get_item_features(self, item_id: str) -> str:
        return self.items_details.get(item_id, "") #Evitem el error de KeyError

class PelliculesDataset(DatasetBase):
   
    def carregar_dades(self):
        logger.info("Carregant dades de pel·lícules...")
        with open(self.fitxer_valoracions, 'r') as fitxer:
            lector = csv.reader(fitxer)
            next(lector)
            self.valoracions = []
            self.valoracions_per_usuari = {}
            self.valoracions_per_item = {}
            for fila in lector:
                usuari_id = str(fila[0])
                item_id = str(fila[1])
                puntuacio = float(fila[2])
                if puntuacio != 0:
                    self.valoracions.append((usuari_id, item_id, puntuacio))
                    self.valoracions_per_usuari.setdefault(usuari_id, {})[item_id] = puntuacio #Guardem la valoració de l'usuari per aquest item
                    self.valoracions_per_item.setdefault(item_id, []).append(puntuacio) #Guardem la valoració d'aquest item per aquest usuari
        with open(self.fitxer_items, 'r') as fitxer:
            lector = csv.reader(fitxer)
            next(lector)
            self.items = {}
            self.items_details = {}
            for fila in lector:
                item_id = str(fila[0])
                nom_item = fila[1]
                generes = fila[2] if len(fila) > 2 else "" #Evitem el error de IndexError si no hi ha gèneres
                self.items[item_id] = nom_item
                self.items_details[item_id] = generes 

        self.actualitzar_indices()
        logger.info(f"Pel·lícules carregades: {len(self.items)} pel·lícules, {len(self.valoracions)} valoracions")


class LlibresDataset(DatasetBase):
    def carregar_dades(self):
        logger.info("Carregant dades de llibres...")
        
        with open(self.fitxer_valoracions, 'r') as fitxer:
            lector = csv.reader(fitxer)
            next(lector)
            self.valoracions = []
            self.valoracions_per_usuari = {}
            self.valoracions_per_item = {}
            for fila in lector:
                usuari_id = str(fila[0])
                item_id = str(fila[1])
                puntuacio = float(fila[2])
                if puntuacio != 0:
                    self.valoracions.append((usuari_id, item_id, puntuacio))
                    self.valoracions_per_usuari.setdefault(usuari_id, {})[item_id] = puntuacio #Guardem la valoració de l'usuari per aquest item
                    self.valoracions_per_item.setdefault(item_id, []).append(puntuacio) #Guardem la valoració d'aquest item per aquest usuari

        self.items = {}
        for _, item_id, _ in self.valoracions:
            if item_id not in self.items:
                self.items[item_id] = f"Llibre (ISBN: {item_id})"

        self.actualitzar_indices()
        logger.info(f"Llibres carregats: {len(self.items)} llibres, {len(self.valoracions)} valoracions")

class Evaluador:
    def calcular_mae(self, prediccions: List[float], valoracions_reals: List[float]) -> float:
        if not prediccions or len(prediccions) != len(valoracions_reals):
            return 0
        errores = [abs(p - r) for p, r in zip(prediccions, valoracions_reals)]
        return sum(errores) / len(errores)

    def calcular_rmse(self, prediccions: List[float], valoracions_reals: List[float]) -> float:
        if not prediccions or len(prediccions) != len(valoracions_reals):
            return 0
        errores_cuadrados = [(p - r) ** 2 for p, r in zip(prediccions, valoracions_reals)]
        mse = sum(errores_cuadrados) / len(errores_cuadrados)
        return math.sqrt(mse)

    def evaluar_recomendador(self, recomanador, dataset: DatasetBase, usuari_id: str) -> Tuple[float, float]:
        valoracions_usuari = dataset.obtenir_valoracions_usuari(usuari_id)
        if not valoracions_usuari:
            logger.warning(f"Usuari {usuari_id} sense valoracions")
            return 0, 0
        prediccions = []
        valoracions_reals = []
        for item_id, puntuacio_real in valoracions_usuari.items():
            puntuacio_predita = recomanador._predir_item(usuari_id, item_id)
            if puntuacio_predita is not None:
                prediccions.append(puntuacio_predita)
                valoracions_reals.append(puntuacio_real)
        mae = self.calcular_mae(prediccions, valoracions_reals)
        rmse = self.calcular_rmse(prediccions, valoracions_reals)
        return mae, rmse
class Recomanador(ABC):
    def __init__(self, conjunt_dades: DatasetBase):
        self.conjunt_dades = conjunt_dades

    @abstractmethod
    def recomana(self, usuari_id: str, limit: int = 5) -> List[Tuple[str, str, float]]:
        raise NotImplementedError

    @abstractmethod
    def _predir_item(self, usuari_id: str, item_id: str) -> Optional[float]:
        raise NotImplementedError


class RecomanadorSimple(Recomanador):
    def __init__(self, conjunt_dades: DatasetBase, min_vots: int = 3):
        super().__init__(conjunt_dades)
        self.min_vots = min_vots
        logger.info(f"Recomanador Simple inicialitzat amb min_vots={min_vots}")

    def _calcula_score(self, item_id: str) -> Optional[float]:
        num_vots = self.conjunt_dades.get_num_votes(item_id)
        if num_vots < self.min_vots:
            return None
        avg_item = self.conjunt_dades.get_item_avg(item_id)
        avg_global = self.conjunt_dades.get_avg_global(self.min_vots)

        score = ((num_vots / (num_vots + self.min_vots)) * avg_item + (self.min_vots / (num_vots + self.min_vots)) * avg_global)
        return score

    def _predir_item(self, usuari_id: str, item_id: str) -> Optional[float]:
        return self._calcula_score(item_id)

    def recomana(self, usuari_id: str, limit: int = 5) -> List[Tuple[str, str, float]]:
        logger.debug(f"Generant recomanacions simples per a l'usuari {usuari_id}")
        candidats = self.conjunt_dades.get_items_no_valorats(usuari_id)
        recomanacions = []
        
        for item_id in candidats:
            puntuacio = self._calcula_score(item_id)
            if puntuacio is not None:
                nom_item = self.conjunt_dades.items.get(item_id, f"Item {item_id}")
                recomanacions.append((item_id, nom_item, puntuacio))
        
        recomanacions.sort(key=lambda x: x[2], reverse=True)
        logger.info(f"Generades {len(recomanacions[:limit])} recomanacions simples")
        return recomanacions[:limit]


class RecomanadorCollaboratiu(Recomanador):
    def __init__(self, conjunt_dades: DatasetBase, k_veins: int = 2):
        super().__init__(conjunt_dades)
        self.k_veins = k_veins
        logger.info(f"Recomanador Col·laboratiu inicialitzat amb k_veins={k_veins}")

    def _calcula_similitud(self, usuari1: str, usuari2: str) -> float:
        val1 = self.conjunt_dades.obtenir_valoracions_usuari(usuari1)
        val2 = self.conjunt_dades.obtenir_valoracions_usuari(usuari2)
        items_comuns = [item for item in val1 if item in val2]
        if not items_comuns:
            return 0
        numerador = sum(val1[item] * val2[item] for item in items_comuns)
        norma1 = math.sqrt(sum(val1[item] ** 2 for item in items_comuns))
        norma2 = math.sqrt(sum(val2[item] ** 2 for item in items_comuns))
        if norma1 == 0 or norma2 == 0:
            return 0
        return numerador / (norma1 * norma2)

    def _troba_veins(self, usuari_id: str) -> List[Tuple[str, float]]:
        similituds = []
        for altres_usuari in self.conjunt_dades.obtenir_usuaris():
            if altres_usuari != usuari_id:
                sim = self._calcula_similitud(usuari_id, altres_usuari)
                similituds.append((altres_usuari, sim))
        similituds.sort(key=lambda x: x[1], reverse=True)
        return similituds[:self.k_veins]

    def _mitjana_usuari(self, usuari_id: str) -> float:
        valoracions = self.conjunt_dades.obtenir_valoracions_usuari(usuari_id)
        if not valoracions:
            return 0
        return sum(valoracions.values()) / len(valoracions)

    def _predir_item(self, usuari_id: str, item_id: str) -> Optional[float]:
        veins = self._troba_veins(usuari_id)
        if not veins:
            return None
        mu = self._mitjana_usuari(usuari_id)
        numerador = 0
        denominador = 0
        for vei_id, similitud in veins:
            valoracions_vei = self.conjunt_dades.obtenir_valoracions_usuari(vei_id)
            if item_id in valoracions_vei:
                mv = self._mitjana_usuari(vei_id)
                numerador += similitud * (valoracions_vei[item_id] - mv)
                denominador += abs(similitud)
        if denominador == 0:
            return None
        return mu + (numerador / denominador)

    def recomana(self, usuari_id: str, limit: int = 5) -> List[Tuple[str, str, float]]:
        logger.debug(f"Generant recomanacions col·laboratives per a l'usuari {usuari_id}")
        veins = self._troba_veins(usuari_id)
        if not veins: #Si no te veins semblants, no podem fer recomanacions col·laboratives
            logger.warning(f"No s'han trobat veïns per a l'usuari {usuari_id}")
            return []
        candidats = self.conjunt_dades.get_items_no_valorats(usuari_id) #Obtenim els ítems que l'usuari no ha valorat, que seran els candidats a recomanar
        prediccions = []
        for item_id in candidats:
            puntuacio = self._predir_item(usuari_id, item_id) #Calculem la puntuació predita per aquest item (la mitjana ponderada)
            if puntuacio is not None:
                prediccions.append((item_id, self.conjunt_dades.items[item_id], puntuacio)) #Afegim a la llista de prediccions una tupla amb el item_id, el nom del item i la puntuació predita
        prediccions.sort(key=lambda x: x[2], reverse=True) #Ordenem les prediccions per puntuació de manera descendente, de més alta a més baixa
        logger.info(f"Generades {len(prediccions[:limit])} recomanacions col·laboratives")
        return prediccions[:limit]

class RecomanadorContingut(Recomanador):
    def __init__(self, conjunt_dades: DatasetBase, pmax: float = 5.0):
        super().__init__(conjunt_dades)
        self.pmax = pmax
        self.tfidf_matrix = None
        self.vocabulary = []
        self.perfils_usuaris = {}
        self.item_list = []
        sample_features = list(conjunt_dades.items_details.values())
        if not sample_features or all(not f for f in sample_features):
            raise ValueError("El dataset no té característiques d'ítems per a l'anàlisi basat en contingut")
        logger.info("Recomanador basat en contingut inicialitzat")
        self._construir_matriz_tfidf()

    def _construir_matriz_tfidf(self):
        logger.debug("Construint matriu TF-IDF...")
        self.item_list = sorted(self.conjunt_dades.items.keys())
        item_features = [self.conjunt_dades.get_item_features(item_id) for item_id in self.item_list]
        tfidf_vectorizer = TfidfVectorizer(stop_words='english', lowercase=True) #Elimina paraules en anglès que estan vuides o que no aporten informació
        self.tfidf_matrix = tfidf_vectorizer.fit_transform(item_features).toarray() #Creem la matriu TF-IDF a partir de les característiques dels ítems, converteix els generes en una matriu numèrica
        self.vocabulary = tfidf_vectorizer.get_feature_names_out() #Extreu el nom de les caracteristiques i les guarda en un array
        logger.info(f"Matriz TF-IDF construida: {self.tfidf_matrix.shape}") #Ens retorna les dimensions de la matriu TF-IDF
        logger.info(f"Vocabulario: {len(self.vocabulary)} características")
        logger.debug(f"Primeres características: {list(self.vocabulary[:10])}") #Mostra les primeres 10 característiques del vocabulari per verificar que se han extret correctament

    def _calcular_perfil_usuari(self, usuari_id: str) -> np.ndarray:
        if usuari_id in self.perfils_usuaris: #Si el perfil del usuari ja ha estat calculat
            return self.perfils_usuaris[usuari_id] #Retorna el perfil del usuari
        valoracions = self.conjunt_dades.obtenir_valoracions_usuari(usuari_id) #Obté les valoracions de l'usuari, que es un diccionari on la clau és el item_id i el valor és la puntuació que ha donat l'usuari a aquest item
        if not valoracions: #Si l'usuari no té valoracions, retorna un vector de zeros
            logger.warning(f"Usuari {usuari_id} sense valoracions") #Mostra un avís en el log que l'usuari no té valoracions
            return np.zeros(len(self.vocabulary)) #Retorna un vector de zeros amb la mateixa longitud que el vocabulari, que representa un perfil d'usuari sense preferències específiques
        puntuacions_vector = np.zeros(len(self.item_list))
        for idx, item_id in enumerate(self.item_list):
            if item_id in valoracions:
                puntuacions_vector[idx] = valoracions[item_id]
        #Calcular perfil amb les formules de la presentació
        suma_ponderada = puntuacions_vector @ self.tfidf_matrix
        suma_puntuacions = np.sum(puntuacions_vector)
        if suma_puntuacions == 0:
            perfil = np.zeros(len(self.vocabulary))
        else:
            perfil = suma_ponderada / suma_puntuacions 
        self.perfils_usuaris[usuari_id] = perfil
        logger.debug(f"Perfil calculado per usuario {usuari_id}")
        return perfil

    def _calcular_similitud_items(self, usuari_id: str) -> np.ndarray:
        perfil = self._calcular_perfil_usuari(usuari_id)        
        similituds = self.tfidf_matrix @ perfil # @es el operador de multiplicació de matrius en numpy
        logger.debug(f"Similituds calculades per a l'usuari {usuari_id}")
        return similituds

    def _calcular_puntuacio_final(self, similituds: np.ndarray) -> np.ndarray:
        return similituds * self.pmax 

    def _predir_item(self, usuari_id: str, item_id: str) -> Optional[float]:
        try:
            idx = self.item_list.index(item_id) #Obtenim l'índex de l'item_id en la llista de items, si no està en la llista es llança un ValueError
            similituds = self._calcular_similitud_items(usuari_id)
            puntuacions = self._calcular_puntuacio_final(similituds)
            return float(puntuacions[idx])
        except ValueError:
            logger.warning(f"Ítem {item_id} no trobat") #Si el item_id no està en la llista de items, es llança un ValueError
            return None

    def recomana(self, usuari_id: str, limit: int = 5) -> List[Tuple[str, str, float]]:
        logger.debug(f"Generant recomanacions basades en contingut per a l'usuari {usuari_id}")
        similituds = self._calcular_similitud_items(usuari_id)
        puntuacions = self._calcular_puntuacio_final(similituds)
        valorats = set(self.conjunt_dades.obtenir_valoracions_usuari(usuari_id).keys())
        recomanacions = []
        for idx, item_id in enumerate(self.item_list):
            if item_id not in valorats:
                nom_item = self.conjunt_dades.items.get(item_id, f"ítem {item_id}")
                recomanacions.append((
                    item_id,
                    nom_item,
                    float(puntuacions[idx])
                ))
        recomanacions.sort(key=lambda x: x[2], reverse=True) #Ordenem les recomanacions per puntuació de manera descendent
        logger.info(f"Generades {len(recomanacions[:limit])} recomanacions basades en contingut")
        return recomanacions[:limit]

def mostrar_recomanacions(recomanacions: List[Tuple[str, str, float]]):
    if not recomanacions:
        print("No hi ha recomanacions disponibles per a aquest usuari.")
        return

    print("RECOMANACIONS:")
    print()
    for i, (item_id, nom, score) in enumerate(recomanacions, 1):
        print(f'{i}. {nom}')
        print(f'   ID: {item_id} | Puntuació predita: {score:.2f}/5.0')
    print()

def mostrar_evaluacio(mae: float, rmse: float):
    print("RESULTATS DE L'AVALUACIÓ:")
    print()
    print(f"MAE (Mean Absolute Error): {mae:.4f}") #Mostra els valors amb 4 decimals perquè en té massa decimals
    print(f"RMSE (Root Mean Square Error): {rmse:.4f}")
    print()

def guardar_recomanador(recomanador: Recomanador, nom_archivo: str):
    try:
        with open(nom_archivo, 'wb') as f: #wb es un fitxer binari
            pickle.dump(recomanador, f) #Utilizem pickle per guardar l'objecte en wb i per tant no cal recalcular-lo cada cop que l'utilizem
        logger.info(f"Recomanador guardat a {nom_archivo}")
    except Exception as e:
        logger.error(f"Error en guardar el recomanador: {e}") #Mostra quin error ha ocorregut al intentar guardar el recomanador

def cargar_recomanador(nom_archivo: str) -> Optional[Recomanador]: #Pot retornar un recomanador o None si no s'ha pogut carregar
    try:
        with open(nom_archivo, 'rb') as f: #rb es un fitxer binari de lectura
            recomanador = pickle.load(f) #Utilizam pickle per carregar l'objecte guardat en el fitxer
        logger.info(f"Recomanador carregat des de {nom_archivo}")
        return recomanador
    except FileNotFoundError:
        logger.debug(f"Fitxer {nom_archivo} no trobat")
        return None
    except Exception as e:
        logger.error(f"Error en carregar el recomanador: {e}")
        return None

def obtenir_nom_archivo_pickle(dataset_type: str, method: str) -> str:
    return f"recommender_{dataset_type}_{method}.dat" #El nom del fitxer es genera a partir del tipus de dataset i del mètode de recomanació

def main():
    print()
    print("SISTEMA DE RECOMANACIONS DE ÍTEMS")
    print()
    logger.info("SISTEMA DE RECOMANACIONS INICIAT")
    print("Conjunts de dades disponibles:")
    print("1. Pel·lícules (MovieLens)")
    print("2. Llibres")
    print()
    tipus_dades = input("Tria el tipus de dades (pelis/llibres): ").strip().lower()

    if tipus_dades == "pelis" or tipus_dades == "1":
        dataset = PelliculesDataset('dataset/MovieLens100k/ratings.csv', 'dataset/MovieLens100k/movies.csv')
        dataset_type = "pelis"
    elif tipus_dades == "llibres" or tipus_dades == "2":
        dataset = LlibresDataset('dataset/Books/Ratings.csv', 'dataset/Books/Users.csv')
        dataset_type = "llibres"
    else:
        print("Tipus de dades no vàlid.")
        logger.error("S'ha seleccionat un tipus de dataset invàlid")
        return
    try:
        dataset.carregar_dades()
    except FileNotFoundError as e:
        print(f"Error: no s'ha trobat el fitxer {e.filename}")
        logger.error(f"Fitxer no trobat: {e.filename}")
        return
    usuaris = dataset.obtenir_usuaris()
    if not usuaris:
        print("No hi ha dades disponibles.")
        logger.error("No hi ha dades disponibles en el dataset")
        return
    print(f"Usuaris disponibles ({len(usuaris)} total): {', '.join(usuaris[:10])}...")
    print("Sistemes de recomanació disponibles:")
    print("1. Simple (items més populars)")
    print("2. Col·laboratiu (usuaris similars)")
    if dataset_type == "pelis":
        print("3. Basat en contingut (TF-IDF)")
    tipus_recomana = input("Tria el tipus de recomanació (simple/col·laboratiu/contingut): ").strip().lower()

    if tipus_recomana == "simple" or tipus_recomana == "1":
        method = "simple"
        min_vots = input("Nombre mínim de valoracions (defecte 3): ").strip()
        try:
            min_vots = int(min_vots) if min_vots else 3
        except ValueError:
            min_vots = 3
        pickle_file = obtenir_nom_archivo_pickle(dataset_type, method)
        recomanador = cargar_recomanador(pickle_file)
        if recomanador is None:
            recomanador = RecomanadorSimple(dataset, min_vots)
            guardar_recomanador(recomanador, pickle_file)

    elif tipus_recomana == "col·laboratiu" or tipus_recomana == "colaboratiu" or tipus_recomana == "2":
        method = "col·laboratiu"
        k_veins = input("Nombre de veïns més similars (defecte 2): ").strip()
        try:
            k_veins = int(k_veins) if k_veins else 2
        except ValueError:
            k_veins = 2
        pickle_file = obtenir_nom_archivo_pickle(dataset_type, method)
        recomanador = cargar_recomanador(pickle_file)
        if recomanador is None:
            recomanador = RecomanadorCollaboratiu(dataset, k_veins)
            guardar_recomanador(recomanador, pickle_file)

    elif tipus_recomana == "contingut" or tipus_recomana == "3":
        if dataset_type != "pelis":
            print("El dataset de llibres no té característiques per a l'anàlisi basat en contingut.")
            logger.warning("Intent de fer servir recomanació basada en contingut amb dataset de llibres")
            return
        method = "contingut"
        pickle_file = obtenir_nom_archivo_pickle(dataset_type, method)
        recomanador = cargar_recomanador(pickle_file)
        if recomanador is None:
            try:
                print("Construint matriu TF-IDF...")
                recomanador = RecomanadorContingut(dataset)
                guardar_recomanador(recomanador, pickle_file)
            except ValueError as e:
                print(f"Error: {e}")
                logger.error(f"Error al crear recomendador basado en contenido: {e}")
                return
    else:
        print("Tipus de recomanació no vàlid.")
        logger.error("Tipo de recomendador inválido seleccionado")
        return

    while True:
        print("Accions disponibles:")
        print("1. Generar recomanacions")
        print("2. Avaluar recomanador")
        print("3. Sortir")
        accio = input("Tria una acció (1/2/3): ").strip()
        if accio == "1" or accio.lower() == "recomanar":
            usuari_id = input("Introdueix l'ID de l'usuari: ").strip()
            if usuari_id not in usuaris:
                print("Usuari no vàlid.")
                logger.warning(f"Usuari invàlid: {usuari_id}")
                continue
            limit = input("Nombre de recomanacions (defecte 5): ").strip()
            try:
                limit = int(limit) if limit else 5
            except ValueError:
                limit = 5
            print("Calculant recomanacions...")
            logger.info(f"Generant {limit} recomanacions per a l'usuari {usuari_id} ({method})")
            recomanacions = recomanador.recomana(usuari_id, limit)
            mostrar_recomanacions(recomanacions)
        elif accio == "2" or accio.lower() == "avaluar":
            usuari_id = input("Introdueix l'ID de l'usuari a avaluar: ").strip()
            if usuari_id not in usuaris:
                print("Usuari no vàlid.")
                logger.warning(f"Usuari invàlid per a l'avaluació: {usuari_id}")
                continue
            print("Calculant avaluació...")
            logger.info(f"Avaluant recomanador per a l'usuari {usuari_id}")
            evaluador = Evaluador()
            mae, rmse = evaluador.evaluar_recomendador(recomanador, dataset, usuari_id)
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
