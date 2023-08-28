import re
import json
import pandas as pd
import numpy as np
import unicodedata
import math as mt
import mysql.connector as sql

user     = 'buydepa'
password = 'GWc42X887heD'
host     = 'buydepa-market.cy47rcxrw2g5.us-east-1.rds.amazonaws.com'
schema   = 'market'

#-----------------------------------------------------------------------------#
# Forecat ANN
#-----------------------------------------------------------------------------#
#def datamodelo(filename):
#    salida = pd.read_pickle(filename,compression='gzip')
#    return salida

def datamodelo(tiponegocio):
    if 'venta' in tiponegocio.lower() or 'sell' in tiponegocio.lower():
        negoccio = 'sell'
    if 'arriendo' in tiponegocio.lower() or 'rent' in tiponegocio.lower():
        negoccio = 'rent'
        
    db_connection = sql.connect(user=user, password=password, host=host, database=schema)
    data          = pd.read_sql(f"""SELECT salida FROM market.model_result_colombia_ann WHERE mpio_ccdgo='11001' AND tipoinmueble='Apartamento' AND tiponegocio='{negoccio}' """, con=db_connection)
    db_connection.close()
    
    salida  = json.loads(data['salida'].iloc[0])
    return salida

def pricingforecast(salida,inputvar):

    delta         = 0
    #salida       = datamodelo(tiponegocio)
    options       = salida['options']
    varlist       = salida['varlist']
    coef          = salida['coef']
    minmax        = salida['minmax']
    variables     = pd.DataFrame(0, index=np.arange(1), columns=varlist)
    
    for i in inputvar:
        value = inputvar[i]
        idd   = [z==elimina_tildes(i) for z in varlist]
        if sum(idd)==0:
            try:
                idd = [re.findall(elimina_tildes(i)+'#'+str(int(value)), z)!=[] for z in varlist]
            except:
                try:
                    idd = [re.findall(elimina_tildes(i)+'#'+elimina_tildes(value), z)!=[] for z in varlist]
                except:
                    pass
            value = 1                   
        if sum(idd)>0:
            row                = [j for j, x in enumerate(idd) if x]
            varname            = varlist[row[0]]
            variables[varname] = value
            
    # Transform MinMax
    a = variables.iloc[0]
    a = a[a!=0]
    for i in a.index:
        mini         = minmax[i]['min']
        maxi         = minmax[i]['max']
        variables[i] = (variables[i]-mini)/(maxi-mini)
        
    x     = variables.values
    value = ForecastFun(coef,x.T,options)
    if options['ytrans']=='log':
        value = np.exp(value)
        
    value         = value*(1-delta)
    valorestimado = np.round(value, int(-(mt.floor(mt.log10(value)) - 2))) 
    valuem2       = value/inputvar['areaconstruida']
    valortotal = np.round(value, int(-(mt.floor(mt.log10(value)) - 2))) 
    valuem2    = valortotal/inputvar['areaconstruida']
    return {'valorestimado': valorestimado[0][0], 'valorestimado_mt2':valuem2[0][0]}

def ForecastFun(coef,x,options):

    hiddenlayers = options['hiddenlayers']
    lambdavalue  = options['lambdavalue']
    biasunit     = options['biasunit']
    tipofun      = options['tipofun']
    numvar       = x.shape[0]
    nodos        = [numvar]
    for i in hiddenlayers:
        nodos.append(i)
    nodos.append(1)
        
    k          = len(nodos)
    suma       = 0
    theta      = [[] for i in range(k-1)]
    lambdac    = [[] for i in range(k-1)]
    lambdavect = np.nan
    for i in range(k-1):
        theta[i]   = np.reshape(coef[0:(nodos[i]+suma)*nodos[i+1]], (nodos[i]+suma, nodos[i+1]), order='F').T
        lambdac[i] =lambdavalue*np.ones(theta[i].shape)
        coef       = coef[(nodos[i]+suma)*nodos[i+1]:]
        if biasunit=='on':
            suma = 1
            lambdac[i][:,0] = 0
        [fil,col]  = lambdac[i].shape
        lambdavect = np.c_[lambdavect,np.reshape(lambdac[i],(fil*col,1)).T ]
        
    lambdac = lambdavect[:,1:].T
        
    # Forward Propagation
    a    = [[] for i in range(k)]
    z    = [[] for i in range(k)]
    g    = [[] for i in range(k)]
    a[0] = x
    numN = x.shape[1]
    for i in range(k-1):
        z[i+1]      = np.dot(theta[i],a[i])
        [ai,g[i+1]] = ANNFun(z[i+1],tipofun)
        if ((i+1)!=(k-1)) & (biasunit=='on'):
            a[i+1] = np.vstack((np.ones((1,numN)),ai))
        else:
            a[i+1] = ai
    return a[-1]

def ANNFun(z, tipofun):
    z = np.asarray(z)
    if tipofun=='lineal':
        f = z
        g = 1
    if tipofun=='logistica':
        f = 1/(1+mt.exp(-z))
        g = f*(1-f)
    if tipofun=='exp':
        f = np.exp(z)
        g = np.exp(z)
    if tipofun=='cuadratica':
        f = z + 0.5*(z*z)
        g = 1 + z
    if tipofun=='cubica':
        f = z + 0.5*(z*z)+(1/3.0)*(z*z*z)
        g = 1 + z + z*z
    return [f,g]

def elimina_tildes(s):
    s = s.replace(' ','').lower().strip()
    return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))