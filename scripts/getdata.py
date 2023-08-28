import re
import json
import streamlit as st
import pandas as pd
import numpy as np
import requests
from sqlalchemy import create_engine
from shapely.geometry import Polygon
from urllib.parse import quote_plus
from fuzzywuzzy import fuzz
from datetime import datetime, timedelta

@st.experimental_memo
def circle_polygon(metros,lat,lng):
    grados   = np.arange(-180, 190, 10)
    Clat     = ((metros/1000.0)/6371.0)*180/np.pi
    Clng     = Clat/np.cos(lat*np.pi/180.0)
    theta    = np.pi*grados/180.0
    longitud = lng + Clng*np.cos(theta)
    latitud  = lat + Clat*np.sin(theta)
    return Polygon([[x, y] for x,y in zip(longitud,latitud)])

@st.experimental_memo
def conjuntos_direcciones():
    user     = st.secrets["user_bigdata"]
    password = st.secrets["password_bigdata"]
    host     = st.secrets["host_bigdata"]
    schema   = st.secrets["schema_bigdata"]
    engine   = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')    
    data     = pd.read_sql_query("""SELECT coddir,direccion,nombre_conjunto FROM bigdata.data_bogota_conjuntos """ , engine)
    
    idd = data['nombre_conjunto'].astype(str).str.contains('"')
    if sum(idd)>0:
        data.loc[idd,'nombre_conjunto'] = data.loc[idd,'nombre_conjunto'].apply(lambda x: x.strip('"'))
    data['via'] = data['direccion'].apply(lambda x: dir2comp(x,0))
    v           = data['via'].value_counts().reset_index()
    v.columns   = ['index','via']
    v           = v[v['via']>50]
    idd         = data['via'].isin(v['index'])
    if sum(~idd)>0:
        data.loc[~idd,'via'] = None
    data['via'] = data['via'].replace(['CL', 'KR', 'TV', 'AK', 'AC', 'DG'],['Calle', 'Carrera', 'Transversal', 'Avenida Carrera', 'Avenida Calle', 'Diagonal'])
    
    data['comp1'] = data['direccion'].apply(lambda x: dir2comp(x,1))
    data['comp2'] = data['direccion'].apply(lambda x: dir2comp(x,2))
    data['comp3'] = data['direccion'].apply(lambda x: dir2comp(x,3))
    idd = (data['via'].notnull()) & (data['comp1'].notnull()) & (data['comp2'].notnull()) & (data['comp3'].notnull())
    data['new_dir'] = None
    data.loc[idd,'new_dir'] = data.loc[idd,'via']+' '+data.loc[idd,'comp1']+' '+data.loc[idd,'comp2']+' '+data.loc[idd,'comp3'] 
    return data

@st.cache(allow_output_mutation=True)
def getlatlng(direccion):
    api_key  = "AIzaSyAgT26vVoJnpjwmkoNaDl1Aj3NezOlSpKs"
    latitud  = None
    longitud = None
    direccion_codificada = quote_plus(direccion)
    url      = f"https://maps.googleapis.com/maps/api/geocode/json?address={direccion_codificada}&key={api_key}"
    response = requests.get(url)
    data     = response.json()

    if data['status'] == 'OK':
        latitud = data['results'][0]['geometry']['location']['lat']
        longitud = data['results'][0]['geometry']['location']['lng']
    return latitud, longitud

@st.cache(allow_output_mutation=True)
def getdatanivel1(fcoddir):
    user     = st.secrets["user_bigdata"]
    password = st.secrets["password_bigdata"]
    host     = st.secrets["host_bigdata"]
    schema   = st.secrets["schema_bigdata"]
    engine   = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')

    dataconjunto = pd.read_sql_query(f"""SELECT * FROM bigdata.data_bogota_conjuntos WHERE coddir='{fcoddir}';""" , engine)
    datapredios  = pd.read_sql_query(f"""SELECT barmanpre as lotcodigo, estrato, piso, predirecc,preaconst,prechip,precedcata FROM bigdata.data_bogota_catastro WHERE coddir='{fcoddir}';""" , engine)
    datalote     = pd.DataFrame()
    if datapredios.empty is False:
        lotcodigo    = datapredios['lotcodigo'].iloc[0]
        datalote     = pd.read_sql_query(f"""SELECT ST_AsText(geometry) as wkt FROM bigdata.data_bogota_lotes WHERE lotcodigo='{lotcodigo}';""" , engine)
    engine.dispose()
    return dataconjunto,datapredios,datalote

@st.cache(allow_output_mutation=True)
def getdatanivel2(fcoddir,datapredios):
    user     = st.secrets["user_bigdata"]
    password = st.secrets["password_bigdata"]
    host     = st.secrets["host_bigdata"]
    schema   = st.secrets["schema_bigdata"]
    engine   = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')

    datadir      = pd.read_sql_query(f"""SELECT direccion, matricula FROM bigdata.snr_matricula_geometry WHERE coddir='{fcoddir}';""" , engine)
    dataprocesos = pd.DataFrame()
    if datadir.empty is False:
        listamat = ', '.join(f'"{i}"' for i in datadir['matricula'].unique().tolist())
        dataids  = pd.read_sql_query(f"""SELECT docid, value as matricula FROM bigdata.snr_data_matricula WHERE value IN ({listamat})""", engine)
        #dataids  = dataids.merge(datadir,on='matricula',how='left',validate='m:1')
        dataids  = dataids.merge(datadir,on='matricula',how='outer')
        if dataids.empty is False:
            docidlist    = ', '.join(f'{i}' for i in dataids['docid'].unique().tolist())  
            #dataprocesos = pd.read_sql_query(f"""SELECT docid,nombre,tarifa,cuantia FROM bigdata.snr_tabla_procesos WHERE docid IN ({docidlist}) AND codigo IN ('125') AND cuantia>0""", engine)
            dataprocesos = pd.read_sql_query(f"""SELECT docid,codigo,nombre,tarifa,cuantia FROM bigdata.snr_tabla_procesos WHERE docid IN ({docidlist})""", engine)
            if dataprocesos.empty is False:
                docidlist = ', '.join(f'{i}' for i in dataprocesos['docid'].unique().tolist())  
                dataids   = dataids[dataids['docid'].isin(dataprocesos['docid'])]
            datacompleta = pd.read_sql_query(f"""SELECT docid,tipo_documento_publico,numero_documento_publico,fecha_documento_publico,oficina,entidad,documento_json FROM bigdata.snr_data_completa WHERE docid IN ({docidlist})""", engine)
            if datacompleta.empty is False:
                datacompleta = replacenull(datacompleta,'fecha_documento_publico','Fecha:')
                if 'documento_json' in datacompleta:
                    datacompleta.drop(columns=['documento_json'],inplace=True)
            if dataprocesos.empty is False:
                dataprocesos = dataprocesos.merge(datacompleta,on='docid',how='left',validate='m:1')
                dataids      = orderbytype(dataids)
                dataprocesos = dataprocesos.merge(dataids,on='docid',how='left',validate='m:1')
                dataprocesos = dataprocesos.sort_values(by=['fecha_documento_publico','codigo'],ascending=[False,True])
                
                try:
                    if datapredios.empty is False:
                        datamerge    = datapredios[['predirecc','preaconst']]
                        datamerge.rename(columns={'predirecc':'direccion','preaconst':'areaconstruida'},inplace=True)
                        datamerge    = datamerge.sort_values(by='areaconstruida',ascending=False)
                        datamerge    = datamerge.drop_duplicates(subset='direccion',keep='first')
                        dataprocesos = dataprocesos.merge(datamerge,on='direccion',how='left',validate='m:1')
                        idd          = dataprocesos['areaconstruida'].isnull()
                        if sum(idd)>0:
                            dataprocesos.loc[idd,'areaconstruida'] = dataprocesos.loc[idd,'direccion'].apply(lambda x: best_match(x,datamerge.copy()))
                        variables    = ['docid','codigo','direccion','areaconstruida','fecha_documento_publico','nombre','tarifa', 'cuantia', 'tipo_documento_publico', 'numero_documento_publico','oficina', 'entidad']
                        variables    = [x for x in variables if x in dataprocesos]
                        dataprocesos = dataprocesos[variables]
                except: pass
    if dataprocesos.empty is False:
        for i in ['fecha_documento_publico','Fecha','Fecha:']:
            if i in dataprocesos:
                try: 
                    dataprocesos[i] = pd.to_datetime(dataprocesos[i],errors='coerce')
                except: pass
                    
    engine.dispose()
    return dataprocesos
    
@st.cache(allow_output_mutation=True)
def getdatanivel3(fcoddir):
    user     = st.secrets["user_market"]
    password = st.secrets["password_market"]
    host     = st.secrets["host_market"]
    schema   = st.secrets["schema_market"]
    engine   = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')
    
    one_year_ago = datetime.now() - timedelta(days=545)
    one_year_ago = one_year_ago.strftime('%Y-%m-%d')
    
    #datamarketventa    = pd.read_sql_query(f"""SELECT direccion,descripcion,url,tipoinmueble,fecha_inicial,areaconstruida,valormt2,rango,habitaciones,banos,garajes,img1,valorventa FROM appraisal.colombia_venta_apartamento_market WHERE coddir='{fcoddir}';""" , engine)
    #datamarketarriendo = pd.read_sql_query(f"""SELECT direccion,descripcion,url,tipoinmueble,fecha_inicial,areaconstruida,valormt2,rango,habitaciones,banos,garajes,img1,valorarriendo FROM appraisal.colombia_arriendo_apartamento_market WHERE coddir='{fcoddir}';""" , engine)
    #datagaleria        = pd.read_sql_query(f"""SELECT * FROM market.data_galeria_usados_bogota WHERE coddir='{fcoddir}';""" , engine)

    datamarketventa    = pd.read_sql_query(f"""SELECT code, fuente,direccion,descripcion,url,tipoinmueble,fecha_inicial,areaconstruida,valormt2,habitaciones,banos,garajes,imagen_principal as img1,telefono1,telefono2,telefono3,valorventa FROM market.data_colombia_bogota_venta_apartamento_market WHERE coddir='{fcoddir}';""" , engine)
    datamarketarriendo = pd.read_sql_query(f"""SELECT code, fuente, direccion,descripcion,url,tipoinmueble,fecha_inicial,areaconstruida,valormt2,habitaciones,banos,garajes,imagen_principal as img1,telefono1,telefono2,telefono3,valorarriendo FROM market.data_colombia_bogota_arriendo_apartamento_market WHERE coddir='{fcoddir}';""" , engine)
    datagaleria        = pd.read_sql_query(f"""SELECT fecha_inicial,tipo_cliente,tipoinmueble,tiponegocio,telefono1,telefono2,telefono3,telefono4 FROM market.data_galeria_usados_bogota WHERE coddir='{fcoddir}'  AND fecha_inicial>='{one_year_ago}' AND available=1""" , engine)
    
    if datamarketventa.empty is False:
        datamarketventa['sorted'] = datamarketventa['fuente'].replace(['FR', 'M2', 'DO', 'GIU', 'CC'],[1,2,3,4,5])
        datamarketventa = datamarketventa.sort_values(by=['url','sorted'], na_position='last')
        datamarketventa = datamarketventa.drop_duplicates(subset=['direccion','valorventa','areaconstruida','habitaciones','banos','garajes'])
        datamarketventa.drop(columns=['fuente','sorted'],inplace=True)
        datamarketventa = datamarketventa.sort_values(by='fecha_inicial',ascending=True)
        
    if datamarketarriendo.empty is False:
        datamarketarriendo['sorted'] = datamarketarriendo['fuente'].replace(['FR', 'M2', 'DO', 'GIU', 'CC'],[1,2,3,4,5])
        datamarketarriendo = datamarketarriendo.sort_values(by=['url','sorted'], na_position='last')
        datamarketarriendo = datamarketarriendo.drop_duplicates(subset=['direccion','valorarriendo','areaconstruida','habitaciones','banos','garajes'])
        datamarketarriendo.drop(columns=['fuente','sorted'],inplace=True)
        datamarketarriendo = datamarketarriendo.sort_values(by='fecha_inicial',ascending=True)

    if datagaleria.empty is False:
        datagaleria['listaphone'] = datagaleria[['telefono1','telefono2','telefono3','telefono4']].apply(lambda x: [w for w in x.to_list() if w is not None] ,axis=1)
        for i in range(1,5):
            datagaleria[f'telefono{i}'] = datagaleria['listaphone'].apply(lambda x: phoneposition(x,i-1))
        del datagaleria['listaphone']
        
    datamarketventa['rango']    = pd.cut(datamarketventa['areaconstruida'],[0,30,40,60,100,150,200,300,np.inf],labels=['0-30','30-40','40-60','60-100','100-150','150-200','200-300','300-max'])
    datamarketarriendo['rango'] = pd.cut(datamarketarriendo['areaconstruida'],[0,30,40,60,100,150,200,300,np.inf],labels=['0-30','30-40','40-60','60-100','100-150','150-200','200-300','300-max'])
    engine.dispose()
    return datamarketventa,datamarketarriendo,datagaleria

@st.cache(allow_output_mutation=True)
def getdatanivel4(fcoddir):
    user     = st.secrets["user_colombia"]
    password = st.secrets["password_colombia"]
    host     = st.secrets["host_colombia"]
    schema   = st.secrets["schema_colombia"]
    engine   = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')
    datarecorrido = pd.read_sql_query(f"""SELECT fecha_recorrido as fecha_inicial, tipo_negocio as tiponegocio, telefono1, telefono2, telefono3 FROM colombia.app_recorredor_stock_ventanas WHERE coddir='{fcoddir}';""" , engine)
    if datarecorrido.empty is False:
        for i in ['telefono1', 'telefono2', 'telefono3']:
            idd = datarecorrido[i]==''
            if sum(idd)>0:
                datarecorrido.loc[idd,i] = None
        datarecorrido['listaphone'] = datarecorrido[['telefono1','telefono2','telefono3']].apply(lambda x: [w for w in x.to_list() if w is not None] ,axis=1)
        for i in range(1,4):
            datarecorrido[f'telefono{i}'] = datarecorrido['listaphone'].apply(lambda x: phoneposition(x,i-1))
        del datarecorrido['listaphone']
        datarecorrido = datarecorrido.dropna(subset=['telefono1'])
    engine.dispose()
    return datarecorrido

@st.cache(allow_output_mutation=True)
def getdatanivel5(latitud,longitud):
    user     = st.secrets["user_appraisal"]
    password = st.secrets["password_appraisal"]
    host     = st.secrets["host_appraisal"]
    schema   = st.secrets["schema_appraisal"]
    engine   = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')
    
    databarrio            = pd.DataFrame()
    barriopricing         = pd.DataFrame()
    barriocaracterizacion = pd.DataFrame()
    barriovalorizacion    = pd.DataFrame()
        
    if latitud is not None or longitud is not None:
        databarrio = pd.read_sql_query(f"""SELECT *,ST_AsText(geometry) as wkt FROM {schema}.barrios WHERE st_contains(geometry,point({longitud},{latitud}))""" , engine)
    
    if databarrio.empty is False:
        codigo             = databarrio['codigo'].iloc[0]
        tablaventa         = 'colombia_venta_apartamento_barrio'
        tablaarriendo      = 'colombia_arriendo_apartamento_barrio'
        databarrioventa    = pd.read_sql_query(f"""SELECT * FROM {schema}.{tablaventa} WHERE codigo='{codigo}'"""  , engine)
        databarrioarriendo = pd.read_sql_query(f"""SELECT * FROM {schema}.{tablaarriendo} WHERE codigo='{codigo}'""" , engine)
        
        barriopricing = pd.DataFrame()
        if databarrioventa.empty is False:
            databarrioventa['tiponegocio'] = 'Venta'
            barriopricing = pd.concat([barriopricing,databarrioventa])
        if databarrioarriendo.empty is False:
            databarrioarriendo['tiponegocio'] = 'Arriendo'
            barriopricing = pd.concat([barriopricing,databarrioarriendo])
        
        if barriopricing.empty is False:
            barriopricing['combinacion'] = None
            idd = barriopricing['tipo']=='barrio'
            if sum(idd)>0:
                barriopricing.loc[idd,'combinacion'] = ''
                
            idd = barriopricing['tipo']=='complemento'
            if sum(idd)>0:
                barriopricing.loc[idd,'combinacion'] = barriopricing.loc[idd,'habitaciones'].astype(int).astype(str)+' H + '+barriopricing.loc[idd,'banos'].astype(int).astype(str)+' B'
    
            idd = barriopricing['tipo']=='complemento_garaje'
            if sum(idd)>0:
                barriopricing.loc[idd,'combinacion'] = barriopricing.loc[idd,'habitaciones'].astype(int).astype(str)+' H + '+barriopricing.loc[idd,'banos'].astype(int).astype(str)+' B + '+barriopricing.loc[idd,'garajes'].astype(int).astype(str)+' G'
            
        tablaventa               = 'colombia_venta_apartamento_valorizacion'
        tablaarriendo            = 'colombia_arriendo_apartamento_valorizacion'
        datavalorizacionventa    = pd.read_sql_query(f"""SELECT * FROM {schema}.{tablaventa} WHERE codigo='{codigo}'"""  , engine)
        datavalorizacionarriendo = pd.read_sql_query(f"""SELECT * FROM {schema}.{tablaarriendo} WHERE codigo='{codigo}'""" , engine)
    
        barriovalorizacion = pd.DataFrame()
        if datavalorizacionventa.empty is False:
            datavalorizacionventa['tiponegocio'] = 'Venta'
            barriovalorizacion = pd.concat([barriovalorizacion,datavalorizacionventa])
        if datavalorizacionarriendo.empty is False:
            datavalorizacionarriendo['tiponegocio'] = 'Arriendo'
            barriovalorizacion = pd.concat([barriovalorizacion,datavalorizacionarriendo])
            
        if barriovalorizacion.empty is False:
            barriovalorizacion['combinacion'] = None
            idd = barriovalorizacion['tipo']=='barrio'
            if sum(idd)>0:
                barriovalorizacion.loc[idd,'combinacion'] = ''
                
            idd = barriovalorizacion['tipo']=='complemento'
            if sum(idd)>0:
                barriovalorizacion.loc[idd,'combinacion'] = barriovalorizacion.loc[idd,'habitaciones'].astype(int).astype(str)+' H + '+barriovalorizacion.loc[idd,'banos'].astype(int).astype(str)+' B'
    
            idd = barriovalorizacion['tipo']=='complemento_garaje'
            if sum(idd)>0:
                barriovalorizacion.loc[idd,'combinacion'] = barriovalorizacion.loc[idd,'habitaciones'].astype(int).astype(str)+' H + '+barriovalorizacion.loc[idd,'banos'].astype(int).astype(str)+' B + '+barriovalorizacion.loc[idd,'garajes'].astype(int).astype(str)+' G'
        
        tablaventa                  = 'colombia_venta_apartamento_caracterizacion'
        tablaarriendo               = 'colombia_arriendo_apartamento_caracterizacion'
        datacaracterizacionventa    = pd.read_sql_query(f"""SELECT variable,valor,tipo FROM {schema}.{tablaventa} WHERE codigo='{codigo}'"""  , engine)
        datacaracterizacionarriendo = pd.read_sql_query(f"""SELECT variable,valor,tipo FROM {schema}.{tablaarriendo} WHERE codigo='{codigo}'""" , engine)
        
        barriocaracterizacion = pd.DataFrame()
        if datacaracterizacionventa.empty is False:
            datacaracterizacionventa['tiponegocio'] = 'Venta'
            barriocaracterizacion = pd.concat([barriocaracterizacion,datacaracterizacionventa])
        if datacaracterizacionarriendo.empty is False:
            datacaracterizacionarriendo['tiponegocio'] = 'Arriendo'
            barriocaracterizacion = pd.concat([barriocaracterizacion,datacaracterizacionarriendo])
            
    engine.dispose()
    return databarrio,barriopricing,barriocaracterizacion,barriovalorizacion

@st.cache(allow_output_mutation=True)
def getdatanivel6(scacodigo):
    user     = st.secrets["user_market"]
    password = st.secrets["password_market"]
    host     = st.secrets["host_market"]
    schema   = st.secrets["schema_market"]
    engine   = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')
    
    barriopricing         = pd.DataFrame()
    barriocaracterizacion = pd.DataFrame()
    barriovalorizacion    = pd.DataFrame()
            
    tablaventa         = 'data_colombia_bogota_venta_apartamento_barrio'
    tablaarriendo      = 'data_colombia_bogota_arriendo_apartamento_barrio'
    databarrioventa    = pd.read_sql_query(f"""SELECT * FROM {schema}.{tablaventa} WHERE scacodigo='{scacodigo}'"""  , engine)
    databarrioarriendo = pd.read_sql_query(f"""SELECT * FROM {schema}.{tablaarriendo} WHERE scacodigo='{scacodigo}'""" , engine)
    
    barriopricing = pd.DataFrame()
    if databarrioventa.empty is False:
        databarrioventa['tiponegocio'] = 'Venta'
        barriopricing = pd.concat([barriopricing,databarrioventa])
    if databarrioarriendo.empty is False:
        databarrioarriendo['tiponegocio'] = 'Arriendo'
        barriopricing = pd.concat([barriopricing,databarrioarriendo])
    
    if barriopricing.empty is False:
        barriopricing['combinacion'] = None
        idd = barriopricing['tipo']=='barrio'
        if sum(idd)>0:
            barriopricing.loc[idd,'combinacion'] = ''
            
        idd = barriopricing['tipo']=='complemento'
        if sum(idd)>0:
            barriopricing.loc[idd,'combinacion'] = barriopricing.loc[idd,'habitaciones'].astype(int).astype(str)+' H + '+barriopricing.loc[idd,'banos'].astype(int).astype(str)+' B'

        idd = barriopricing['tipo']=='complemento_garaje'
        if sum(idd)>0:
            barriopricing.loc[idd,'combinacion'] = barriopricing.loc[idd,'habitaciones'].astype(int).astype(str)+' H + '+barriopricing.loc[idd,'banos'].astype(int).astype(str)+' B + '+barriopricing.loc[idd,'garajes'].astype(int).astype(str)+' G'
        
    tablaventa               = 'data_colombia_bogota_venta_apartamento_valorizacion'
    tablaarriendo            = 'data_colombia_bogota_arriendo_apartamento_valorizacion'
    datavalorizacionventa    = pd.read_sql_query(f"""SELECT * FROM {schema}.{tablaventa} WHERE scacodigo='{scacodigo}'"""  , engine)
    datavalorizacionarriendo = pd.read_sql_query(f"""SELECT * FROM {schema}.{tablaarriendo} WHERE scacodigo='{scacodigo}'""" , engine)

    barriovalorizacion = pd.DataFrame()
    if datavalorizacionventa.empty is False:
        datavalorizacionventa['tiponegocio'] = 'Venta'
        barriovalorizacion = pd.concat([barriovalorizacion,datavalorizacionventa])
    if datavalorizacionarriendo.empty is False:
        datavalorizacionarriendo['tiponegocio'] = 'Arriendo'
        barriovalorizacion = pd.concat([barriovalorizacion,datavalorizacionarriendo])
        
    if barriovalorizacion.empty is False:
        barriovalorizacion['combinacion'] = None
        idd = barriovalorizacion['tipo']=='barrio'
        if sum(idd)>0:
            barriovalorizacion.loc[idd,'combinacion'] = ''
            
        idd = barriovalorizacion['tipo']=='complemento'
        if sum(idd)>0:
            barriovalorizacion.loc[idd,'combinacion'] = barriovalorizacion.loc[idd,'habitaciones'].astype(int).astype(str)+' H + '+barriovalorizacion.loc[idd,'banos'].astype(int).astype(str)+' B'

        idd = barriovalorizacion['tipo']=='complemento_garaje'
        if sum(idd)>0:
            barriovalorizacion.loc[idd,'combinacion'] = barriovalorizacion.loc[idd,'habitaciones'].astype(int).astype(str)+' H + '+barriovalorizacion.loc[idd,'banos'].astype(int).astype(str)+' B + '+barriovalorizacion.loc[idd,'garajes'].astype(int).astype(str)+' G'
    
    tablaventa                  = 'data_colombia_bogota_venta_apartamento_caracterizacion'
    tablaarriendo               = 'data_colombia_bogota_venta_apartamento_caracterizacion'
    datacaracterizacionventa    = pd.read_sql_query(f"""SELECT variable,valor,tipo FROM {schema}.{tablaventa} WHERE scacodigo='{scacodigo}'"""  , engine)
    datacaracterizacionarriendo = pd.read_sql_query(f"""SELECT variable,valor,tipo FROM {schema}.{tablaarriendo} WHERE scacodigo='{scacodigo}'""" , engine)
    
    barriocaracterizacion = pd.DataFrame()
    if datacaracterizacionventa.empty is False:
        datacaracterizacionventa['tiponegocio'] = 'Venta'
        barriocaracterizacion = pd.concat([barriocaracterizacion,datacaracterizacionventa])
    if datacaracterizacionarriendo.empty is False:
        datacaracterizacionarriendo['tiponegocio'] = 'Arriendo'
        barriocaracterizacion = pd.concat([barriocaracterizacion,datacaracterizacionarriendo])
            
    engine.dispose()
    return barriopricing,barriocaracterizacion,barriovalorizacion

@st.cache(allow_output_mutation=True)
def getdataradio(inputvar):
    
    tipoinmueble = 'Apartamento'
    if 'tipoinmueble' in inputvar: 
        tipoinmueble = inputvar['tipoinmueble']
        
    latitud,longitud = [None]*2
    if 'latitud' in inputvar:  latitud = inputvar['latitud']
    if 'longitud' in inputvar: longitud = inputvar['longitud']
    
    metros = 500
    if 'metros' in inputvar:  metros = inputvar['metros']
    
    consulta = ''
    for i in ['habitaciones','banos','garajes']:
        if i in inputvar:
            consulta += f' AND {i}={inputvar[i]}'
    
    if 'areaconstruida' in inputvar and inputvar['areaconstruida']>0:
        areamin = int(inputvar['areaconstruida']*0.85)
        areamax = int(inputvar['areaconstruida']*1.15)
        consulta += f' AND (areaconstruida>={areamin} AND areaconstruida<={areamax})'
    
    if consulta!='':
        consulta = consulta.strip().strip('AND')+' AND '


    user     = st.secrets["user_market"]
    password = st.secrets["password_market"]
    host     = st.secrets["host_market"]
    schema   = st.secrets["schema_market"]
    engine   = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')
    
    tablaventa     = f'data_colombia_bogota_venta_{tipoinmueble.lower()}_market'
    tablaarriendo  = f'data_colombia_bogota_arriendo_{tipoinmueble.lower()}_market'
    dataventa      = pd.read_sql_query(f"""SELECT direccion, url, tiempodeconstruido, areaconstruida, valorventa as valor, habitaciones, banos, garajes, estrato, latitud, longitud, valormt2, code, img1, imagen_principal FROM {schema}.{tablaventa} WHERE {consulta} ST_Distance_Sphere(geometry, POINT({longitud},{latitud}))<={metros}"""  , engine)
    datarriendo    = pd.read_sql_query(f"""SELECT direccion, url, tiempodeconstruido, areaconstruida, valorarriendo as valor, habitaciones, banos, garajes, estrato, latitud, longitud, valormt2, code, img1, imagen_principal FROM {schema}.{tablaarriendo} WHERE {consulta} ST_Distance_Sphere(geometry, POINT({longitud},{latitud}))<={metros}"""  , engine)
    engine.dispose()
    return dataventa,datarriendo

    
@st.cache(allow_output_mutation=True)
def getdatacatastro(chip):
    user     = st.secrets["user_bigdata"]
    password = st.secrets["password_bigdata"]
    host     = st.secrets["host_bigdata"]
    schema   = st.secrets["schema_bigdata"]
    engine   = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')

    data             = pd.read_sql_query(f"""SELECT vigencia, nroIdentificacion,valorAutoavaluo,valorImpuesto,indPago,fechaPresentacion,idSoporteTributario FROM bigdata.data_bogota_catastro_vigencia WHERE chip='{chip}'""" , engine)
    datamatricula    = pd.read_sql_query(f"""SELECT numeroMatriculaInmobiliaria FROM bigdata.data_bogota_catastro_predio WHERE numeroChip='{chip}'""" , engine)
    datapropietarios = pd.DataFrame()
    if datamatricula.empty is False:
        if data.empty:
            data.loc[0,'matricula'] = datamatricula['numeroMatriculaInmobiliaria'].iloc[0]
        else:
            data['matricula'] = datamatricula['numeroMatriculaInmobiliaria'].iloc[0]
    
    try: numdocument = data[data['nroIdentificacion'].notnull()]['nroIdentificacion'].iloc[0]
    except: numdocument = None
    if numdocument is not None and len(numdocument)>3:
        datapropietarios = pd.read_sql_query(f"""SELECT nroIdentificacion,tipoPropietario,matriculaMercantil,tipoDocumento,primerNombre,segundoNombre,primerApellido,segundoApellido,email,telefonos FROM bigdata.data_bogota_catastro_propietario WHERE nroIdentificacion='{numdocument}'""" , engine)
    engine.dispose()
    return data,datapropietarios

@st.cache(allow_output_mutation=True)
def getscacodigo(latitud,longitud):
    user     = st.secrets["user_colombia"]
    password = st.secrets["password_colombia"]
    host     = st.secrets["host_colombia"]
    schema   = st.secrets["schema_colombia"]
    
    scacodigo  = ''
    engine     = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')
    data       = pd.read_sql_query(f"""SELECT scacodigo FROM {schema}.data_bogota_barrio_catastral WHERE st_contains(geometry,point({longitud},{latitud}))""" , engine)
    engine.dispose()
    if data.empty is False:
        scacodigo = data['scacodigo'].iloc[0]
    return scacodigo
        

@st.cache(allow_output_mutation=True)
def getinfochip(chip):
    user     = st.secrets["user_bigdata"]
    password = st.secrets["password_bigdata"]
    host     = st.secrets["host_bigdata"]
    schema   = st.secrets["schema_bigdata"]
    engine   = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')

    data          = pd.read_sql_query(f"""SELECT chip, vigencia, valorAutoavaluo,valorImpuesto FROM bigdata.data_bogota_catastro_vigencia WHERE chip IN {chip}""" , engine)
    datamatricula = pd.read_sql_query(f"""SELECT numeroChip as chip, numeroMatriculaInmobiliaria FROM bigdata.data_bogota_catastro_predio WHERE numeroChip IN {chip}""" , engine)
    if data.empty is False:
        data = data.sort_values(by='vigencia',ascending=False)
        data = data.drop_duplicates(subset='chip')
        if datamatricula.empty is False:
            datamatricula = datamatricula.drop_duplicates(subset='chip')
            data = data.merge(datamatricula,on='chip',how='left',validate='1:1')
    engine.dispose()
    return data

@st.cache(allow_output_mutation=True)
def getdatacomparativo(lat,lng,tiponegocio,tipoinmueble,areamin,areamax,valormin,valormax,habitaciones,banos,garajes,metros=500):
    user     = st.secrets["user_market"]
    password = st.secrets["password_market"]
    host     = st.secrets["host_market"]
    schema   = st.secrets["schema_market"]
    engine   = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')
    tabla    = f'data_colombia_bogota_{tiponegocio.lower()}_{tipoinmueble.lower()}_market'

    if tiponegocio.lower()=='venta':
        query = f"""SELECT direccion,url,areaconstruida,valorventa,valorarriendo,latitud,longitud,code,habitaciones,banos,garajes,imagen_principal as img1 FROM market.{tabla} WHERE (areaconstruida>={areamin} AND areaconstruida<={areamax}) AND (valorventa>={valormin} AND valorventa<={valormax}) AND habitaciones={habitaciones} AND banos={banos} AND garajes={garajes} AND ST_Distance_Sphere(geometry,POINT({lng},{lat}))<={metros}"""
    elif tiponegocio.lower()=='arriendo':
        query = f"""SELECT direccion,url,areaconstruida,valorventa,valorarriendo,latitud,longitud,code,habitaciones,banos,garajes,imagen_principal as img1 FROM market.{tabla} WHERE (areaconstruida>={areamin} AND areaconstruida<={areamax}) AND (valorarriendo>={valormin} AND valorarriendo<={valormax}) AND habitaciones={habitaciones} AND banos={banos} AND garajes={garajes} AND ST_Distance_Sphere(geometry,POINT({lng},{lat}))<={metros}"""
    data  = pd.read_sql_query(query , engine)
    engine.dispose()
    
    if data.empty is False:
        if tiponegocio.lower()=='venta':
            data['valor'] = data['valorventa'].copy()
        elif tiponegocio.lower()=='arriendo':
            data['valor'] = data['valorarriendo'].copy()
            
        data['valormt2'] = data['valor']/data['areaconstruida']
    return data

def dir2comp(x,pos):
    try: 
        x = re.sub(r'(\d+)', r',\1', x)
        componentes = x.split(',')
        componentes = [c.strip() for c in componentes if c.strip() != '']
        return re.sub(r'(\d+)([A-Za-z]+)', r'\1 \2', componentes[pos]) 
    except: return None
    
def replacenull(data,varnull,varreplace):
    idd = data[varnull].isnull()
    if sum(idd)>0:
        data.loc[idd,varnull] = data.loc[idd,'documento_json'].apply(lambda x: getfromjson(x,varreplace))
    return data

def getfromjson(x,varreplace):
    try: 
        x              = json.loads(x)
        selected_items = [(i, item) for i, item in enumerate(x) if item['value'] == varreplace]
        return x[selected_items[0][0]+1]['value']
    except: return None
    
def orderbytype(data):
    order = 1
    data['order'] = None
    for i in ['AP','CA','CS','OF']:
        idd = data['direccion'].str.lower().str.contains(i.lower())
        if sum(idd)>0:
            data.loc[idd,'order'] = order
        order += 1
    data = data.sort_values(by='order',ascending=True)
    return data.groupby('docid').agg({'direccion':'first'}).reset_index()

def best_match(x,datacompare):
    datacompare['ratio'] = datacompare['direccion'].apply(lambda w: fuzz.token_sort_ratio(x, w))
    datacompare          = datacompare[datacompare['ratio']>95]
    if datacompare.empty is False:
        return datacompare['areaconstruida'].iloc[0]
    else: return None
    
def phoneposition(x,pos):
    try: return x[pos]
    except: return None
    
def obtener_coordenadas(*datasets):
    for dataset in datasets:
        latitud, longitud = asignar_coordenadas(dataset)
        if latitud is not None and longitud is not None:
            return latitud, longitud
    return None, None

def asignar_coordenadas(dataset):
    latitud  = None
    longitud = None
    if not dataset.empty and 'latitud' in dataset and 'longitud' in dataset:
        dataset = dataset[(dataset['latitud'].notnull()) & (dataset['longitud'].notnull())]
        if isinstance(dataset['latitud'].iloc[0], float) and isinstance(dataset['longitud'].iloc[0], float):
            latitud  = dataset['latitud'].iloc[0]
            longitud = dataset['longitud'].iloc[0]
    return latitud, longitud

def formatofecha(x):
    try: return x.strftime('%Y-%m-%d')
    except: return ''