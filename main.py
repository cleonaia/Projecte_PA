import csv
import numpy as np
import abc, abstractmethod
import os 


class DatasetBase(ABC):
    def __init__(self, ratings_file, items_file):
        self.ratings = None
        self.items = None
        self.ratings_file = ratings_file
        self.items_file = items_file

    def carrega_dades(self):
        ll=[]
        with open(self.rating,'r') as csv_file:
            csvreades = csv.reader(csv_file)
            fields = next(csvreader)
            for f in csvreader:
                parts = f.split(,).strip()
                row = self.ratings(row[0:4])
                ll.append(row)
    def avg_gloval(self):
        suma=0
        for i in self.items:
            suma+=i.ratings
        return suma/len(self.items)

    def avg_items_no_puntuats(self):
        
    def recomana(self,peli):
        if self.peli>altre.peli:
            return self.peli
        else:
            return altre.peli
              
def score(num_vots,min_vots,avg_item,avg_global):
  nota = ((num_vots/(num_vots+min_vots))*avg_item)+((num_vots/(num_vots+min_vots))*avg_global)
  return nota
def prediccio(min_vots):

class RecomanadorSimple(Recomanador):
    def __init__(self, dataset, min_vots):
        self.suma_p=suma_p
        self.min_vots=min_vots
    def puntuacio(self, avg_item,avg_global,num_vots):
        punts = ((num_vots*avg_item)/(num_vots + min_vots))+
class RecomanadorCollaboratiu(Recomanador):
    def __init__(self, dataset, k_veins=5):
        super().__init__(dataset)
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
    

    def recomienda(self, usuari_id):
        items_no_valorats = self._dades.get_items_no_valorats(usuari_id)
        if not items_no_valorats:
            return []
            
        veins = self.troba_veins(usuari_id)
        scores = {}
        
        for item_id in items_no_valorats:
            puntuacio = self.calcula_puntuacio(usuari_id, item_id, veins)
            if puntuacio is not None:
                scores[item_id] = puntuacio
        
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
