import csv
import math
from abc import ABC, abstractmethod


class DatasetBase(ABC):
    def __init__(self, fitxer_valoracions, fitxer_items):
        self.fitxer_valoracions = fitxer_valoracions
        self.fitxer_items = fitxer_items
        self.valoracions = []
        self.items = {}

    def carregar_dades(self):
        with open(self.fitxer_valoracions, 'r') as fitxer:
            lector = csv.reader(fitxer)
            next(lector)
            self.valoracions = []
            for fila in lector:
                usuari_id = str(fila[0])
                item_id = str(fila[1])
                puntuacio = float(fila[2])
                if puntuacio != 0:
                    self.valoracions.append((usuari_id, item_id, puntuacio))

        with open(self.fitxer_items, 'r') as fitxer:
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

    def get_avg_global(self, min_vots=0):
        mitjanes = []
        for item_id in self.items:
            num_vots = self.get_num_votes(item_id)
            if num_vots >= min_vots:
                mitjana = self.get_item_avg(item_id)
                if mitjana > 0:
                    mitjanes.append(mitjana)
        if not mitjanes:
            return 0
        return sum(mitjanes) / len(mitjanes)

    def get_item_avg(self, item_id):
        puntuacions = [puntuacio for _, item, puntuacio in self.valoracions if item == item_id]
        if not puntuacions:
            return 0
        return sum(puntuacions) / len(puntuacions)

    def get_num_votes(self, item_id):
        return sum(1 for _, item, _ in self.valoracions if item == item_id)

    def get_items_no_valorats(self, usuari_id):
        valorats = set(self.obtenir_valoracions_usuari(usuari_id).keys())
        return [item_id for item_id in self.items if item_id not in valorats]



class PelliculesDataset(DatasetBase):
    def __init__(self, fitxer_valoracions, fitxer_items):
        super().__init__(fitxer_valoracions, fitxer_items)


class LlibresDataset(DatasetBase):
    def __init__(self, fitxer_valoracions, fitxer_items):
        super().__init__(fitxer_valoracions, fitxer_items)

    def carregar_dades(self):
        # Carregar valoracions de libros
        with open(self.fitxer_valoracions, 'r') as fitxer:
            lector = csv.reader(fitxer)
            next(lector)  # Saltar capçalera
            self.valoracions = []
            for fila in lector:
                usuari_id = str(fila[0])
                item_id = str(fila[1])  # ISBN
                puntuacio = float(fila[2])
                if puntuacio != 0:
                    self.valoracions.append((usuari_id, item_id, puntuacio))

        # Per als items de libros, els identifiquem pel ISBN
        self.items = {}
        for _, item_id, _ in self.valoracions:
            if item_id not in self.items:
                self.items[item_id] = f'Llibre (ISBN: {item_id})'


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
        # Atributo según diagrama
        self._avg_global = None

    def calcula_puntuacio(self, item_id):
        num_vots = self.conjunt_dades.get_num_votes(item_id)
        if num_vots < self.min_vots:
            return None

        avg_item = self.conjunt_dades.get_item_avg(item_id)
        avg_global = self.conjunt_dades.get_avg_global(self.min_vots)

        score = (
            (num_vots / (num_vots + self.min_vots)) * avg_item
            + (self.min_vots / (num_vots + self.min_vots)) * avg_global
        )
        return score

    def recomana(self, usuari_id, limit=5):
        candidats = self.conjunt_dades.items_no_valorats(usuari_id)
        recomanacions = []
        
        for item_id in candidats:
            puntuacio = self.calcula_puntuacio(item_id)
            if puntuacio is not None:
                nom_item = self.conjunt_dades.items.get(item_id, f'Item {item_id}')
                recomanacions.append((item_id, nom_item, puntuacio))
        
        recomanacions.sort(key=lambda x: x[2], reverse=True)
        return recomanacions[:limit]



class RecomanadorCollaboratiu(Recomanador):
    def __init__(self, conjunt_dades, k_veins=2):
        super().__init__(conjunt_dades)
        self.k_veins = k_veins

    def calcula_similitud(self, usuari1, usuari2):
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

    def troba_veins(self, usuari_id):
        similituds = []
        for altre_usuari in self.conjunt_dades.obtenir_usuaris():
            if altre_usuari != usuari_id:
                sim = self.calcula_similitud(usuari_id, altre_usuari)
                similituds.append((altre_usuari, sim))

        similituds.sort(key=lambda x: x[1], reverse=True)
        return similituds[:self.k_veins]

    def mitjana_usuari(self, usuari_id):
        valoracions = self.conjunt_dades.obtenir_valoracions_usuari(usuari_id)
        if not valoracions:
            return 0
        return sum(valoracions.values()) / len(valoracions)

    def predir_valoracions(self, usuari_id, item_id, veins):
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
        veins = self.troba_veins(usuari_id)
        candidats = self.conjunt_dades.get_items_no_valorats(usuari_id)
        prediccions = []
        for item_id in candidats:
            puntuacio = self.predir_valoracions(usuari_id, item_id, veins)
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
        dataset = PelliculesDataset('pelicules_Dataset/ratings.csv', 'pelicules_Dataset/movies.csv')
    elif tipus_dades == 'llibres':
        dataset = LlibresDataset('Libros_dataset/Ratings.csv', 'Libros_dataset/Users.csv')
    else:
        print('Tipus de dades no vàlid.')
        return

    try:
        dataset.carregar_dades()
    except FileNotFoundError as e:
        print(f'Error: no s\'ha trobat el fitxer {e.filename}')
        return

    usuaris = dataset.obtenir_usuaris()
    if not usuaris:
        print('No hi ha dades disponibles.')
        return

    print(f'\nUsuaris disponibles: {", ".join(usuaris[:10])}...')
    usuari_id = input('Introdueix l\'ID de l\'usuari: ').strip()

    if usuari_id not in usuaris:
        print('Usuari no vàlid.')
        return

    tipus_recomana = input('\nTipus de recomana (simple/col·laboratiu): ').strip().lower()

    if tipus_recomana == 'simple':
        min_vots = input('Nombre mínim de valoracions (defecte 3): ').strip()
        try:
            min_vots = int(min_vots) if min_vots else 3
        except ValueError:
            min_vots = 3
        recomanador = RecomanadorSimple(dataset, min_vots)
    elif tipus_recomana == 'col·laboratiu' or tipus_recomana == 'colaboratiu':
        k_veins = input('Nombre de veïns més similars (defecte 2): ').strip()
        try:
            k_veins = int(k_veins) if k_veins else 2
        except ValueError:
            k_veins = 2
        recomanador = RecomanadorCollaboratiu(dataset, k_veins)
    else:
        print('Tipus de recomanador no vàlid.')
        return

    limit = input('Nombre de recomanacions (defecte 5): ').strip()
    try:
        limit = int(limit) if limit else 5
    except ValueError:
        limit = 5

    print('\nCalculant recomanacions...')
    recomanacions = recomanador.recomana(usuari_id, limit)
    mostrar_recomanacions(recomanacions)


if __name__ == '__main__':
    main()
