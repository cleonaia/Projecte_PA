import csv
import math
from abc import ABC, abstractmethod

class DatasetBase(ABC): #Classe abstracta base per gestionar datasets
    def __init__(self, fitxer_valoracions, fitxer_items):
        self.fitxer_valoracions = fitxer_valoracions
        self.fitxer_items = fitxer_items
        self.valoracions = []
        self.items = {} #Creem un diccionari per buscar el nom_item amb el seu item_id
        self.valoracions_per_usuari = {} #Creem un diccionari per buscar les valoracions d'un usuari amb el seu usuari_id
        self.valoracions_per_item = {} #Creem un diccionari per buscar les valoracions d'un item amb el seu item_id
        self.num_vots_per_item = {} #Creem un diccionari per guardar el nombre de valoracions per cada item
        self.avg_item_per_item = {} #Creem un diccionari per guardar la mitjana de valoracions per cada item
        self.avg_global_cached = 0 #Creem una variable per guardar la mitjana global de valoracions per evitar recalcular-la constantment.

    def carregar_dades(self):
        with open(self.fitxer_valoracions, 'r') as fitxer: #Carreguem les valoracions des del fitxer CSV
            lector = csv.reader(fitxer) 
            next(lector) #Saltem la primera fila que conté els noms de les columnes
            self.valoracions = []
            self.valoracions_per_usuari = {} #Inicialitzem el diccionari de valoracions per usuari on la clau és l'usuari_id i el valor és un altre diccionari on la clau és l'item_id i el valor és la puntuació
            self.valoracions_per_item = {} #Inicialitzem el diccionari de valoracions per item on la clau és l'item_id i el valor és una llista de puntuacions
            for fila in lector:
                usuari_id = str(fila[0])
                item_id = str(fila[1])
                puntuacio = float(fila[2])
                if puntuacio != 0: #Només guardem les valoracions que són diferents de 0, ja que el 0 indica que l'usuari no ha valorat aquell item
                    self.valoracions.append((usuari_id, item_id, puntuacio)) #Afegim la valoració a la llista de valoracions
                    if usuari_id not in self.valoracions_per_usuari: #Si l'usuari_id no està al diccionari de valoracions per usuari, el creem amb un diccionari buit com a valor
                        self.valoracions_per_usuari[usuari_id] = {} #Si l'item_id no està al diccionari de valoracions per item, el creem amb una llista buida com a valor
                    if item_id not in self.valoracions_per_item: #Si l'item_id no està al diccionari de valoracions per item, el creem amb una llista buida com a valor
                        self.valoracions_per_item[item_id] = [] #Afegim la puntuació al diccionari de valoracions per usuari i al diccionari de valoracions per item
                    self.valoracions_per_usuari[usuari_id][item_id] = puntuacio
                    self.valoracions_per_item[item_id].append(puntuacio)
        with open(self.fitxer_items, 'r') as fitxer: #Carreguem els items des del fitxer CSV
            lector = csv.reader(fitxer)
            next(lector) #Saltem la primera fila que conté els noms de les columnes
            self.items = {} #Inicialitzem el diccionari d'items on la clau és l'item_id i el valor és el nom de l'item
            for fila in lector:
                item_id = str(fila[0])
                nom_item = fila[1]
                self.items[item_id] = nom_item

        self.actualitzar_index() 
    #Un cop carregades les dades, actualitzem els diccionaris de nombre de valoracions per item, mitjana de valoracions per item i mitjana global de valoracions

    def actualitzar_index(self):
        self.num_vots_per_item = {item_id: len(puntuacions) for item_id, puntuacions in self.valoracions_per_item.items()} #Actualitzem el diccionari de nombre de valoracions per item,
        # on la clau és l'item_id i el valor és la longitud de la llista de puntuacions per aquell item
        self.avg_item_per_item = {item_id: (sum(puntuacions) / len(puntuacions)) for item_id, puntuacions in self.valoracions_per_item.items()} #Actualitzem el diccionari de mitjana de valoracions per item, 
        #on la clau és l'item_id i el valor és la mitjana de puntuacions
        self.avg_global_cached = self._calcular_avg_global_cached() 
    #Actualitzem la variable de mitjana global de valoracions, que es calcularà un cop carregades les dades i es guardarà en aquesta variable per evitar recalcular-la cada vegada que es demani
    
    def _calcular_avg_global_cached(self, min_vots: int = 0) -> float:
        mitjanes = [self.avg_item_per_item[item_id]#Obtenim la mitjana de valoracions per item només per aquells items que tenen un nombre de valoracions igual o superior al mínim
            for item_id, num_vots in self.num_vots_per_item.items()
            if num_vots >= min_vots] #Si el nombre de valoracions per item és menor que el mínim, no s'inclou la mitjana d'aquest item en el càlcul de la mitjana global
        if not mitjanes: #Si no hi ha cap item que compleixi el criteri de mínim de valoracions, retornem 0
            return 0
        return sum(mitjanes) / len(mitjanes) #Retornem la mitjana de les mitjanes de valoracions per item que compleixen el criteri de mínim de valoracions

    def obtenir_usuaris(self) -> List[str]:
        return sorted(self.valoracions_per_usuari.keys()) #Retornem una llista ordenada dels usuaris que han fet valoracions, que són les claus del diccionari de valoracions per usuari

    def obtenir_valoracions_usuari(self, usuari_id: str) -> Dict[str, float]:
        return dict(self.valoracions_per_usuari.get(usuari_id, {})) #Retornem un diccionari de les valoracions d'un usuari, que és el valor associat a l'usuari_id en el diccionari de valoracions per usuari. 
        #Si l'usuari_id no existeix, retornem un diccionari buit

    def get_avg_global(self, min_vots: int = 0) -> float:
        if min_vots <= 0: #Si el mínim de valoracions és 0 o negatiu, retornem la mitjana global cachejada, 
            #que es va calcular un cop carregades les dades i es va guardar en la variable avg_global_cached.
            return self.avg_global_cached
        return self._calcular_avg_global_cached(min_vots) #Si el mínim de valoracions és positiu, recalculem la mitjana global amb el nou mínim de valoracions

    def get_item_avg(self, item_id: str) -> float:
        return self.avg_item_per_item.get(item_id, 0)

    def get_num_vots(self, item_id: str) -> int:
        return self.num_vots_per_item.get(item_id, 0)

    def get_items_no_valorats(self, usuari_id: str) -> List[str]:
        valorats = set(self.valoracions_per_usuari.get(usuari_id, {}).keys())
        return [item_id for item_id in self.items if item_id not in valorats]

class PelliculesDataset(DatasetBase):
    def __init__(self, fitxer_valoracions, fitxer_items):
        super().__init__(fitxer_valoracions, fitxer_items)

class LlibresDataset(DatasetBase):
    def __init__(self, fitxer_valoracions, fitxer_items):
        super().__init__(fitxer_valoracions, fitxer_items)

    def carregar_dades(self): #Sobrescrivim el mètode de càrrega de dades perquè el format dels fitxers de llibres és diferent al de pel·lícules
        with open(self.fitxer_valoracions, 'r') as fitxer:
            lector = csv.reader(fitxer)
            next(lector)
            self.valoracions = []
            self.valoracions_per_usuari = {} #Inicialitzem el diccionari de valoracions per usuari on la clau és l'usuari_id i el valor és un altre diccionari on la clau és l'item_id i el valor és la puntuació
            self.valoracions_per_item = {} #Inicialitzem el diccionari de valoracions per item on la clau és l'item_id i el valor és una llista de puntuacions
            for fila in lector:
                usuari_id = str(fila[0])
                item_id = str(fila[1])
                puntuacio = float(fila[2])
                if puntuacio != 0:
                    self.valoracions.append((usuari_id, item_id, puntuacio))
                    self.valoracions_per_usuari.setdefault(usuari_id, {})[item_id] = puntuacio
                    self.valoracions_per_item.setdefault(item_id, []).append(puntuacio)

        self.items = {}
        for _, item_id, _ in self.valoracions: #Si el dataset de llibres no té un fitxer d'ítems amb noms, podem crear noms genèrics basats en l'ID del llibre (ISBN)
            if item_id not in self.items:#Si l'item_id no està al diccionari d'items, el creem amb un nom basat en el seu codi, ja que el fitxer de llibres no conté els noms dels llibres
                self.items[item_id] = f"Llibre (Codi: {item_id})"

        self.actualitzar_index()


class Recomanador(ABC):
    def __init__(self, conjunt_dades: DatasetBase):
        self.conjunt_dades = conjunt_dades

    @abstractmethod
    def recomana(self, usuari_id: str, limit: int = 5) -> List[Tuple[str, str, float]]:
        raise NotImplementedError

class RecomanadorSimple(Recomanador):
    def __init__(self, conjunt_dades: DatasetBase, min_vots: int = 3):
        super().__init__(conjunt_dades)
        self.min_vots = min_vots
        self._avg_global = None

    def _calcula_score(self, item_id: str) -> float:
        num_vots = self.conjunt_dades.get_num_vots(item_id) #Obtenim el nombre de valoracions per aquest item
        if num_vots < self.min_vots: #Si el nombre de valoracions per aquest item és menor que el mínim no podem calcular un score fiable, així que retornem None
            return None

        avg_item = self.conjunt_dades.get_item_avg(item_id)
        avg_global = self.conjunt_dades.get_avg_global(self.min_vots)

        score = ((num_vots / (num_vots + self.min_vots)) * avg_item + (self.min_vots / (num_vots + self.min_vots)) * avg_global)
        return score
    
    def recomana(self, usuari_id: str, limit: int = 5) -> List[Tuple[str, str, float]]:
        candidats = self.conjunt_dades.get_items_no_valorats(usuari_id)#Obtenim la llista d'items que l'usuari no ha valorat, que són els candidats a ser recomanats
        recomanacions = []
        for item_id in candidats:
            puntuacio = self.calcula_score(item_id)#Calculem el score per cada item candidat, que es basa en la mitjana de valoracions per aquell item i la mitjana global de valoracions, ponderades pel nombre de valoracions per aquell item i el mínim de valoracions
            if puntuacio is not None:
                nom_item = self.conjunt_dades.items.get(item_id, f"Item {item_id}")
                recomanacions.append((item_id, nom_item, puntuacio))
        
        recomanacions.sort(key=lambda x: x[2], reverse=True)#Ordenem les recomanacions per puntuació de manera descendent, els items amb millor nota apareixen primer
        return recomanacions[:limit] #Retornem només les primeres recomanacions segons el límit establert, que en el nostre cas és 5 per defecte

class RecomanadorCollaboratiu(Recomanador):
    def __init__(self, conjunt_dades: DatasetBase, k_veins: int = 2):
        super().__init__(conjunt_dades)
        self.k_veins = k_veins

    def _calcula_similitud(self, usuari1: str, usuari2: str) -> float: #Calculem la similitud entre dos usuaris utilitzant la similitud del cosinus, que es basa en les valoracions que han fet els dos usuaris sobre els mateixos items
        val1 = self.conjunt_dades.obtenir_valoracions_usuari(usuari1)
        val2 = self.conjunt_dades.obtenir_valoracions_usuari(usuari2)
        
        items_comuns = [item for item in val1 if item in val2]#Obtenim la llista d'items que han valorat els dos usuaris, que són els items comuns que utilitzarem per calcular la similitud
        if not items_comuns:
            return 0 #Si no hi ha items comuns, la similitud és 0
        numerador = sum(val1[item] * val2[item] for item in items_comuns)
        norma1 = math.sqrt(sum(val1[item] ** 2 for item in items_comuns))
        norma2 = math.sqrt(sum(val2[item] ** 2 for item in items_comuns))
        #Apliquem la formula que hi ha a la presentació
        if norma1 == 0 or norma2 == 0: #Si la norma d'algun dels dos usuaris és 0, la similitud no es pot calcular i retornem 0
            return 0

        return numerador / (norma1 * norma2) 

    def _troba_veins(self, usuari_id: str) -> List[Tuple[str, float]]:#Trobem els k usuaris més similars a l'usuari_id, que seran els veïns que utilitzarem per fer les recomanacions col·laboratives
        similituds = []
        for altre_usuari in self.conjunt_dades.obtenir_usuaris(): #Mirem tots els usuaris del conjunt de dades per calcular la similitud amb l'usuari_id
            if altre_usuari != usuari_id: #Només considerem els usuaris diferents a l'usuari_id
                sim = self.calcula_similitud(usuari_id, altre_usuari)#Calculem la similitud entre l'usuari_id i l'altre_usuari, que es basa en les valoracions que han fet els dos usuaris sobre els mateixos items
                similituds.append((altre_usuari, sim))#Afegim la tupla (altre_usuari, sim) a la llista de similituds, on altre_usuari és l'ID de l'altre usuari i sim és la similitud calculada entre els dos usuaris

        similituds.sort(key=lambda x: x[1], reverse=True)#Ordenem la llista de similituds per la segona posició de cada tupla de manera descendent, els usuaris més similars apareixen primer
        return similituds[:self.k_veins] #Retornem només els primers k veins de la llista de similituds
    
    def _mitjana_usuari(self, usuari_id: str) -> float:
        valoracions = self.conjunt_dades.obtenir_valoracions_usuari(usuari_id) #Obtenim les valoracions de l'usuari_id, que és un diccionari on la clau és l'item_id i el valor és la puntuació que ha donat l'usuari a aquell item
        if not valoracions: #Si l'usuari no ha fet cap valoració, la mitjana és 0
            return 0
        return sum(valoracions.values()) / len(valoracions)

    def predir_valoracions(self, usuari_id: str, item_id:str, veins:int) -> float:#Predim la valoració que l'usuari_id donaria a l'item_id utilitzant les valoracions dels veins, que són els k usuaris més similars a l'usuari_id
        m = self.mitjana_usuari(usuari_id)
        numerador = 0
        denominador = 0

        for vei_id, similitud in veins: #Per cada vei_id i la seva similitud amb l'usuari_id, obtenim les valoracions del vei_id i mirem si ha valorat l'item_id que volem predir
            valoracions_vei = self.conjunt_dades.obtenir_valoracions_usuari(vei_id) #Obtenim les valoracions del vei_id, que és un diccionari on la clau és l'item_id i el valor és la puntuació que ha donat el vei_id a aquell item
            if item_id in valoracions_vei: #Si el vei_id ha valorat l'item_id que volem predir, utilitzem aquesta valoració per al càlcul de la puntuació predita per l'usuari_id
                mv = self.mitjana_usuari(vei_id) #Obtenim la mitjana de valoracions del vei_id, que utilitzarem per centrar les valoracions del vei_id al voltant de la seva mitjana
                numerador += similitud * (valoracions_vei[item_id] - mv) #Afegim al numerador la contribució del vei_id a la puntuació predita per l'usuari_id, que es basa en la similitud entre els dos usuaris i la diferència entre la valoració del vei_id per l'item_id i la mitjana de valoracions del vei_id
                denominador += abs(similitud) #Afegim al denominador la contribució de la similitud entre els dos usuaris, que utilitzarem per normalitzar la puntuació predita per l'usuari_id

        if denominador == 0: #Si el denominador és 0, significa que cap dels veins ha valorat l'item_id que volem predir, o que la similitud entre els veins i l'usuari_id és 0
            return None

        return m + (numerador / denominador)

    def recomana(self, usuari_id: str, limit: int = 5) -> List[Tuple[str, str, float]]:
        veins = self.troba_veins(usuari_id) #Obtenim els k veins més similars a l'usuari_id, que són els usuaris que utilitzarem per fer les recomanacions col·laboratives
        candidats = self.conjunt_dades.get_items_no_valorats(usuari_id) #Obtenim la llista d'items que l'usuari_id no ha valorat, que són els candidats a ser recomanats
        prediccions = []
        for item_id in candidats:
            puntuacio = self.predir_valoracions(usuari_id, item_id, veins) #Predim la valoració que l'usuari_id donaria a l'item_id utilitzant les valoracions dels veins, que es basa en la mitjana de valoracions de l'usuari_id i les valoracions dels veins que han valorat l'item_id
            if puntuacio is not None:
                prediccions.append((item_id, self.conjunt_dades.items[item_id], puntuacio))

        prediccions.sort(key=lambda x: x[2], reverse=True)#Ordenem les prediccions per la tercera posició de cada tupla de manera descendent, els items amb millor puntuació predita apareixen primer
        return prediccions[:limit]#Retornem només les primeres prediccions segons el límit establert, que en el nostre cas és 5 per defecte


def mostrar_recomanacions(recomanacions) -> str:
    if not recomanacions:#Si la llista de recomanacions està buida, mostrem un missatge indicant que no hi ha recomanacions disponibles per a aquest usuari
        print("No hi ha recomanacions disponibles per a aquest usuari.")
        return

    print("Recomanacions:")
    for item_id, nom, score in recomanacions:
        print(f"- {nom} (ID: {item_id}), puntuació predita: {score:.2f}") #Mostrem el nom de l'item, el seu ID i la puntuació predita amb dos decimals


def main():
    print("SISTEMA DE RECOMANACIONS")
    tipus_dades = input("Selecciona el tipus de dades (pelis(p)/llibres(ll)): ").strip().lower()
    if tipus_dades == "pelis" or tipus_dades == "p":
        dataset = PelliculesDataset("pelicules_Dataset/ratings.csv", "pelicules_Dataset/movies.csv")
    elif tipus_dades == "llibres" or tipus_dades == "ll":
        dataset = LlibresDataset("Libros_dataset/Ratings.csv", "Libros_dataset/Users.csv")
    else:
        print("Tipus de dades no vàlid.")
        return

    try:
        dataset.carregar_dades() #Intentem carregar les dades del conjunt de dades seleccionat, que pot generar un error si els fitxers no es troben o no tenen el format esperat
    except FileNotFoundError as e:
        print("Error: no s'ha trobat el fitxer")
        return

    usuaris = dataset.obtenir_usuaris() #Obtenim la llista d'usuaris disponibles al conjunt de dades, que són les claus del diccionari de valoracions per usuari. Si aquesta llista està buida, mostrem un missatge indicant que no hi ha dades disponibles i sortim del programa
    if not usuaris:
        print("No hi ha dades disponibles.")
        return

    print(f"Usuaris disponibles: {", ".join(usuaris[:10])}...") #Mostrem només els primers 10 usuaris disponibles per no saturar la sortida, ja que pot haver-hi molts usuaris al conjunt de dades
    usuari_id = input("Introdueix l'ID de l'usuari: ").strip()

    if usuari_id not in usuaris: #Si l'usuari_id introduït no està a la llista d'usuaris disponibles, mostrem un missatge indicant que l'usuari no és vàlid i sortim del programa
        print("Usuari no vàlid.")
        return

    tipus_recomana = input("Tipus de recomanador (simple(s)/col·laboratiu(c)): ").strip().lower()
    if tipus_recomana == "simple" or tipus_recomana == "s":
        min_vots = input("Nombre mínim de valoracions (per defecte 3, apretar enter): ").strip()
        try:
            min_vots = int(min_vots) if min_vots else 3 #Si l'usuari introdueix un valor per al mínim de valoracions, intentem convertir-lo a enter
            #Si l'usuari no introdueix res, utilitzem el valor per defecte de 3
            #Si l'usuari introdueix un valor que no es pot convertir a enter, també utilitzem el valor per defecte de 3
        except ValueError:
            min_vots = 3
        recomanador = RecomanadorSimple(dataset, min_vots)
    elif tipus_recomana == "col·laboratiu" or tipus_recomana == "c":
        k_veins = input("Nombre de veïns més similars (defecte 2): ").strip()
        try:
            k_veins = int(k_veins) if k_veins else 2 #Si l'usuari introdueix un valor per al nombre de veins més similars, intentem convertir-lo a enter
            #Si l'usuari no introdueix res, utilitzem el valor per defecte de 2
            #Si l'usuari introdueix un valor que no es pot convertir a enter, també utilitzem el valor per defecte de 2
        except ValueError:
            k_veins = 2
        recomanador = RecomanadorCollaboratiu(dataset, k_veins) #Creem una instància del recomanador col·laboratiu amb el conjunt de dades carregat i el nombre de veins més similars especificat per l'usuari
    else:
        print("Tipus de recomanador no vàlid.")
        return
    limit = input("Nombre de recomanacions (defecte 5): ").strip() #Preguntem a l'usuari quantes recomanacions vol mostrar, seria el parametre k de la formula, que per defecte és 5.
    try:
        limit = int(limit) if limit else 5 #Si l'usuari introdueix un valor per al nombre de recomanacions, intentem convertir-lo a enter
        #Si l'usuari no introdueix res, utilitzem el valor per defecte de 5
        #Si l'usuari introdueix un valor que no es pot convertir a enter, també utilitzem el valor per defecte de 5
    except ValueError:
        limit = 5
    recomanicions = recomanador.recomana(usuari_id, limit)#Obtenim les recomanacions per a l'usuari_id utilitzant el recomanador seleccionat, que es basa en el tipus de recomanador i els paràmetres especificats per l'usuari
    mostrar_recomanacions(recomanicions)

if __name__ == '__main__':
    main()
