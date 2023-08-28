import pandas as pd
import pickle

# x = forecastlist['venta']

def pricing_ponderador(x):
    result      = None
    p           = pd.DataFrame(x)
    listamodels = list(p['model'].unique())
    
    # D:\Dropbox\Empresa\Buydepa\COLOMBIA\PRICING MODEL\build_ponderaciones_models
    pickle_file_path = "data/ponderacion_modelos.pkl"
    with open(pickle_file_path, "rb") as f:
        ponderadores = pickle.load(f)
    
    for i in ponderadores:
        if set(listamodels) == set(i['lista']):
            w = pd.DataFrame(i)
            w.rename(columns={'lista':'model'},inplace=True)
            p = p.merge(w,on='model',validate='1:1')
            p['forecast'] = p['value']*p['ponderacion']
            result = p['forecast'].sum()
            break
    return result