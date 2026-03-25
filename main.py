min_vots = 200
num_vots = 600
avg_item = float
avg_global = float

def score(num_vots,min_vots,avg_item,avg_global):

  nota = ((num_vots/(num_vots+min_vots))*avg_item)+((num_vots/(num_vots+min_vots))*avg_global)
  return nota
def prediccio(min_vots):
