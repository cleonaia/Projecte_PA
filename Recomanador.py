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
