import csv
import numpy as np
from abc import ABC, abstractmethod
import os


class ConjuntDadesBase(ABC):
    def __init__(self, fitxer_valoracions, fitxer_items): 
        self.valoracions = []
        self.items = []
        self.fitxer_valoracions = fitxer_valoracions
        self.fitxer_items = fitxer_items

    def carrega_dades(self):
        with open(self.fitxer_valoracions, 'r') as H:
            next(H)
            for linia in H:
                part = linia.strip().split(',')

                #Preguntar si es pot fer amb matriu
                
                self.valoracions.append([part[0], part[1], float(part[2])])
        with open(self.fitxer_items, 'r') as f:
            next(f)
            for linia in f:
                part = linia.strip().split(',')
                self.items.append(part[0])

    def mitjana_global(self):
        suma = 0
        comptador = 0
        for linia in self.fitxer_valoracions:
            part = linia.strip().split(',')
            suma += float(part[2])
            comptador += 1
        if comptador == 0:
            return 0
        return suma / comptador
    
    def mitjana_item(self, item_id):
        suma = 0
        comptador = 0
        for v in self.valoracions:
            if v[1] == item_id:
                suma += v[2]
                comptador += 1
        if comptador == 0:
            return 0
        return suma / comptador

    def num_vots(self, item_id):
        comptador = 0
        for v in self.valoracions:
            if v[1] == item_id:
                comptador += 1
        return comptador

    def items_no_valorats(self, usuari_id):
        valorats = []
        for v in self.valoracions:
            if v[0] == usuari_id:
                valorats.append(v[1])
        no_valorats = []
        for item in self.items:
            if item not in valorats:
                no_valorats.append(item)
        return no_valorats

class Recomanador(ABC):
    def __init__(self, conjunt_dades):
        self.conjunt_dades = conjunt_dades

    @abstractmethod
    def recomana(self, usuari_id):
        raise NotImplementedError

class RecomanadorSimple(Recomanador):
    def __init__(self, conjunt_dades, min_vots):
        super().__init__(conjunt_dades)
        self.min_vots = min_vots

    def puntuacio(self, item_id):
        mitjana_item = self.conjunt_dades.mitjana_item(item_id)
        mitjana_global = self.conjunt_dades.mitjana_global()
        num_vots = self.conjunt_dades.num_vots(item_id)
        return ((num_vots / (num_vots + self.min_vots)) * mitjana_item) + ((self.min_vots / (num_vots + self.min_vots)) * mitjana_global)


class RecomanadorCollaboratiu(Recomanador):
    def __init__(self, conjunt_dades, k_veins=5):
        super().__init__(conjunt_dades)
        self._k_veins = k_veins  # Nombre de veins a considerar

    def calcula_similitud(self, usuari1, usuari2):
        # Obtenir valoracions dels dos usuaris
        valoracions_usuari1 = self._dades._ratings[self._dades._ratings[:, 0] == usuari1]
        valoracions_usuari2 = self._dades._ratings[self._dades._ratings[:, 0] == usuari2]

        items_comuns = np.intersect1d(valoracions_usuari1[:, 1], valoracions_usuari2[:, 1])
        if len(items_comuns) < 2:  
            return 0.0

        puntuacions1 = []
        puntuacions2 = []
        
        for item in items_comuns:
            punt1 = valoracions_usuari1[valoracions_usuari1[:, 1] == item][0][2]
            punt2 = valoracions_usuari2[valoracions_usuari2[:, 1] == item][0][2]
            puntuacions1.append(float(punt1))
            puntuacions2.append(float(punt2))
        
        puntuacions1 = np.array(puntuacions1, dtype=float)
        puntuacions2 = np.array(puntuacions2, dtype=float)
        
        if np.all(puntuacions1 == puntuacions1[0]) or np.all(puntuacions2 == puntuacions2[0]):
            return 0.0
        
        try:
            # Calcula correlació de Pearson
            corr = np.corrcoef(puntuacions1, puntuacions2)[0, 1]
            return 0.0 if np.isnan(corr) else corr
        except:
            return 0.0
    
    def troba_veins(self, usuari_id):
        # Obtenir tots els usuaris excepte l'actual
        usuaris = np.unique(self._dades._ratings[:, 0])
        usuaris = usuaris[usuaris != usuari_id]
        
        similituds = []
        for usuari in usuaris:
            similitud = self.calcula_similitud(usuari_id, usuari)
            if not np.isnan(similitud):
                similituds.append((usuari, similitud))
        
        similituds.sort(key=lambda x: x[1], reverse=True)
        return similituds[:self._k_veins]
    

    def recomana(self, usuari_id):
        items_a_provar = self.conjunt_dades.items_no_valorats(usuari_id)
        scores = {}
        for item_id in items_a_provar:
            scores[item_id] = self.puntuacio(item_id)
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
"""
if __name__ == "__main__":
    #Si fem print de v ens mostre ratings.csv tal cual, com fer per a que ens mostri el fitxer?
    v = "ratings.csv"
    i = "pelicules_Dataset/movies.csv"
    print(v)
    dades = ConjuntDadesBase(v, i)
    print("Mitjana global:", dades.mitjana_global())
    print("Mitjana item '1':", dades.mitjana_item('1'))
    print("Num vots item '1':", dades.num_vots('1'))
    print("Items no valorats per usuari '1':", dades.items_no_valorats('1'))
    
