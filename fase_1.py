import csv
import math
from abc import ABC, abstractmethod


class ConjuntDadesBase(ABC):
    def __init__(self, fitxer_valoracions, fitxer_items):
        self.fitxer_valoracions = fitxer_valoracions
        self.fitxer_items = fitxer_items
        self.valoracions = []
        self.items = {}

    def carregar_dades(self):
        with open(self.fitxer_valoracions, 'r', encoding='utf-8') as fitxer:
            lector = csv.reader(fitxer)
            next(lector)
            self.valoracions = []
            for fila in lector:
                usuari_id = str(fila[0])
                item_id = str(fila[1])
                puntuacio = float(fila[2])
                if puntuacio != 0:
                    self.valoracions.append((usuari_id, item_id, puntuacio))

        with open(self.fitxer_items, 'r', encoding='utf-8') as fitxer:
            lector = csv.reader(fitxer)
            next(lector)
            self.items = {}
            for fila in lector:
                item_id = str(fila[0])
                nom_item = fila[1]
                self.items[item_id] = nom_item

    def obtenir_usuaris(self):
        return sorted({v[0] for v in self.valoracions})

    def obtenir_valoracions_usuari(self, usuari_id):
        dades = {}
        for usuari, item, puntuacio in self.valoracions:
            if usuari == usuari_id:
                dades[item] = puntuacio
        return dades

    def mitjana_global(self, min_vots=0):
        mitjanes = []
        for item_id in self.items:
            num_vots = self.num_vots(item_id)
            if num_vots >= min_vots:
                mitjana = self.mitjana_item(item_id)
                if mitjana > 0:
                    mitjanes.append(mitjana)
        if not mitjanes:
            return 0
        return sum(mitjanes) / len(mitjanes)

    def mitjana_item(self, item_id):
        puntuacions = [puntuacio for _, item, puntuacio in self.valoracions if item == item_id]
        if not puntuacions:
            return 0
        return sum(puntuacions) / len(puntuacions)

    def num_vots(self, item_id):
        return sum(1 for _, item, _ in self.valoracions if item == item_id)

    def items_no_valorats(self, usuari_id):
        valorats = set(self.obtenir_valoracions_usuari(usuari_id).keys())
        return [item_id for item_id in self.items if item_id not in valorats]


class PelliculesDataset(ConjuntDadesBase):
    pass


class LlibresDataset(ConjuntDadesBase):
    pass


class Recomanador(ABC):
    def __init__(self, conjunt_dades):
        self.conjunt_dades = conjunt_dades

    @abstractmethod
    def recomana(self, usuari_id, limit=5):
        pass


class RecomanadorSimple(Recomanador):
    def __init__(self, conjunt_dades, min_vots=3):
        super().__init__(conjunt_dades)
        self.min_vots = min_vots

    def puntuacio(self, item_id):
        num_vots = self.conjunt_dades.num_vots(item_id)
        if num_vots < self.min_vots:
            return None

        avg_item = self.conjunt_dades.mitjana_item(item_id)
        avg_global = self.conjunt_dades.mitjana_global(self.min_vots)

        score = (
            (num_vots / (num_vots + self.min_vots)) * avg_item
            + (self.min_vots / (num_vots + self.min_vots)) * avg_global
        )
        return score

    def recomana(self, usuari_id, limit=5):
        candidats = self.conjunt_dades.items_no_valorats(usuari_id)
        puntuacions = []

        for item_id in candidats:
            score = self.puntuacio(item_id)
            if score is not None:
                puntuacions.append((item_id, self.conjunt_dades.items[item_id], score))

        puntuacions.sort(key=lambda x: x[2], reverse=True)
        return puntuacions[:limit]


class RecomanadorCollaboratiu(Recomanador):
    def __init__(self, conjunt_dades, k_veins=2):
        super().__init__(conjunt_dades)
        self.k_veins = k_veins

    def similitud_cosinus(self, usuari1, usuari2):
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

    def obtenir_veins(self, usuari_id):
        similituds = []
        for altre_usuari in self.conjunt_dades.obtenir_usuaris():
            if altre_usuari != usuari_id:
                sim = self.similitud_cosinus(usuari_id, altre_usuari)
                similituds.append((altre_usuari, sim))

        similituds.sort(key=lambda x: x[1], reverse=True)
        return similituds[:self.k_veins]

    def mitjana_usuari(self, usuari_id):
        valoracions = self.conjunt_dades.obtenir_valoracions_usuari(usuari_id)
        if not valoracions:
            return 0
        return sum(valoracions.values()) / len(valoracions)

    def predir_puntuacio(self, usuari_id, item_id, veins):
        mu = self.mitjana_usuari(usuari_id)
        numerador = 0
        denominador = 0

        for vei_id, similitud in veins:
            valoracions_vei = self.conjunt_dades.obtenir_valoracions_usuari(vei_id)
            if item_id in valoracions_vei:
                mv = self.mitjana_usuari(vei_id)
                numerador += similitud * (valoracions_vei[item_id] - mv)
                denominador += abs(similitud)

        if denominador == 0:
            return None

        return mu + (numerador / denominador)

    def recomana(self, usuari_id, limit=5):
        veins = self.obtenir_veins(usuari_id)
        candidats = self.conjunt_dades.items_no_valorats(usuari_id)
        prediccions = []

        for item_id in candidats:
            puntuacio = self.predir_puntuacio(usuari_id, item_id, veins)
            if puntuacio is not None:
                prediccions.append((item_id, self.conjunt_dades.items[item_id], puntuacio))

        prediccions.sort(key=lambda x: x[2], reverse=True)
        return prediccions[:limit]


def mostrar_recomanacions(recomanacions):
    if not recomanacions:
        print('No hi ha recomanacions disponibles per a aquest usuari.')
        return

    print('\nRecomanacions:')
    for item_id, nom, score in recomanacions:
        print(f'- {nom} (ID: {item_id}) -> puntuació predita: {score:.2f}')


def main():
    print('SISTEMA DE RECOMANACIONS')
    print('------------------------')

    tipus_dades = input('Selecciona el tipus de dades (pelis/llibres): ').strip().lower()

    if tipus_dades == 'pelis':
        dataset = PelliculesDataset('MovieLens100k/ratings.csv', 'MovieLens100k/movies.csv')
    elif tipus_dades == 'llibres':
        dataset = LlibresDataset('Books/Ratings.csv', 'Books/Books.csv')
    else:
        print('Tipus de dades no vàlid.')
        return

    try:
        dataset.carregar_dades()
    except FileNotFoundError as e:
        print(f'Error: no s\\'ha trobat el fitxer {e.filename}')
        return

   
