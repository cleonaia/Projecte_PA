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
