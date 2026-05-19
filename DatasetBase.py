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
