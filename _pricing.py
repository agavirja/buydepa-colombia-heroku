import streamlit as st
import folium
import pandas as pd
import numpy as np
import pickle
import streamlit.components.v1 as components

from bs4 import BeautifulSoup
from shapely import wkt
from streamlit_folium import st_folium
from datetime import datetime
from scripts.getdata import conjuntos_direcciones,getdatanivel1,getdatanivel2,getdatanivel3,getdatanivel4,getdatanivel6,getdatacatastro,obtener_coordenadas,getlatlng,getinfochip,formatofecha,getscacodigo,getdataradio
from scripts.coddir import coddir
from scripts.ANNtest import pricingforecast
from scripts.pricing_ponderador import pricing_ponderador
from scripts.circle_polygon import circle_polygon

url = "https://buydepa-colombia.streamlit.app/"

def roundnumbers(x):
    thresholds = [1000000000, 100000000, 1000000, 100000, 10000]
    increments = [1000000, 100000, 10000, 1000, 100]
    
    for threshold, increment in zip(thresholds, increments):
        if x >= threshold:
            return (x + increment // 2) // increment * increment
    return x

def convert_df(df):
   return df.to_csv(index=False).encode('utf-8')

def main():
    formato = {
                'show':False,
               }
    for key,value in formato.items():
        if key not in st.session_state: 
            st.session_state[key] = value
 
    col1, col2, col3  = st.columns([1,1,2])
    with col1:
        pais           = st.selectbox('País',options=['Colombia'])
        direccion      = st.text_input('Dirección',value='')
        areaconstruida = st.number_input('Área construida',step=1)
        banos          = st.selectbox('Baños',options=[1,2,3,4,5,6],index=1)
        estrato        = st.selectbox('Estrato',options=[1,2,3,4,5,6],index=2)

    with col2:
        ciudad         = st.selectbox('País',options=['Bogota'])
        tipoinmueble   = st.selectbox('Tipo de inmueble',options=['Apartamento','Casa'])
        habitaciones   = st.selectbox('Habitaciones',options=[1,2,3,4,5,6],index=2)
        garajes        = st.selectbox('Garajes',options=[0,1,2,3,4],index=1)
        antiguedad     = st.selectbox('Antiguedad',options=range(0,41))
 
    inputvar = {
                'pais':pais,
                'ciudad':ciudad,
                'direccion':direccion, 
                'tipoinmueble':tipoinmueble, 
                'areaconstruida': areaconstruida, 
                'habitaciones': habitaciones, 
                'banos': banos, 
                'garajes': garajes,
                'estrato': estrato, 
                'antiguedad':antiguedad, 
                'metros': 500
                    }
    
    col1b,col2b,col3b = st.columns([1,1,2])
    with col1b:
        st.write('')
        st.write('')
        if st.button('Calcular'):
            st.session_state.show = True
    
    if st.session_state.show:
                    
        forecast_venta,forecast_arriendo,forecastlist,latitud,longitud,dataconjunto,datapredios,datalote,datamarketventa,datamarketarriendo,datagaleria,dataventazona,dataarriendozona = getforecast(inputvar)

        with col3:
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
              <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-icons.css" rel="stylesheet" />
              <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-svg.css" rel="stylesheet" />
              <link id="pagestyle" href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/soft-ui-dashboard.css?v=1.0.7" rel="stylesheet" />
            </head>
            <body>
            <div class="container-fluid py-1">
              <div class="card" style="margin-bottom:20px">
                <div class="card-body p-4">
                  <div class="row">
                    <div class="col-xl-6 col-sm-0 mb-xl-4 mb-0">
                      <h3 class="font-weight-bolder mb-0" style="text-align: center;font-size: 3rem;">${roundnumbers(forecast_venta):,.0f}</h3>
                    </div>
                    <div class="col-xl-6 col-sm-0 mb-xl-4 mb-0" style="margin-top:30px;">
                      <h3 class="font-weight-bolder mb-0" style="text-align: center;font-size: 1.5rem;">${roundnumbers(forecast_venta/areaconstruida):,.0f}<span style="font-size: 0.8rem; color: grey;margin-left:10px;">mt<sup>2</sup></span></h3>
                    </div>                  
                  </div>
                  <h3 class="font-weight-bolder mb-0" style="text-align: center;font-size: 1.2rem;color:grey;">Precio de venta</h3>
                </div>
              </div>
            </div>
            
            <div class="container-fluid py-1">
              <div class="card" style="margin-bottom:20px">
                <div class="card-body p-4">
                  <div class="row">
                    <div class="col-xl-6 col-sm-0 mb-xl-4 mb-0">
                      <h3 class="font-weight-bolder mb-0" style="text-align: center;font-size: 3rem;">${roundnumbers(forecast_arriendo):,.0f}</h3>
                    </div>
                    <div class="col-xl-6 col-sm-0 mb-xl-4 mb-0" style="margin-top:30px;">
                      <h3 class="font-weight-bolder mb-0" style="text-align: center;font-size: 1.5rem;">${roundnumbers(forecast_arriendo/areaconstruida):,.0f}<span style="font-size: 0.8rem; color: grey;margin-left:10px;">mt<sup>2</sup></span></h3>
                    </div>                  
                  </div>
                  <h3 class="font-weight-bolder mb-0" style="text-align: center;font-size: 1.2rem;color:grey;">Precio de arriendo</h3>
                </div>
              </div>
            </div>
            </body>
            </html>
            """
            texto = BeautifulSoup(html, 'html.parser')
            st.markdown(texto, unsafe_allow_html=True)
    
    
        texto = """
        <!DOCTYPE html>
        <html>
          <head>
          <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-icons.css" rel="stylesheet"/>
          <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-svg.css" rel="stylesheet"/>
          <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/soft-ui-dashboard.css?v=1.0.7" id="pagestyle" rel="stylesheet"/>
          </head>
          <body>
          <div style="margin-top:100px;">
          </div>
          </body>
        </html>
        """
        texto = BeautifulSoup(texto, 'html.parser')
        st.markdown(texto, unsafe_allow_html=True)
        
        col1w, col2w, col3w, col4w = st.columns(4)
        with col1w:
            filtro = st.selectbox('Filtro por:', options=['Sin filtrar','Menor precio','Mayor precio','Menor área','Mayor área','Menor habitaciones','Mayor habitaciones'])
        
        with col2w:
            tiponegocio = st.selectbox('Tipo de negocio',options=['Venta','Arriendo'])
                            
        texto = """
        <!DOCTYPE html>
        <html>
          <head>
          <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-icons.css" rel="stylesheet"/>
          <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-svg.css" rel="stylesheet"/>
          <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/soft-ui-dashboard.css?v=1.0.7" id="pagestyle" rel="stylesheet"/>
          </head>
          <body>
          <div style="margin-bottom:100px;">
          </div>
          </body>
        </html>
        """
        texto = BeautifulSoup(texto, 'html.parser')
        st.markdown(texto, unsafe_allow_html=True)
          
        col1,col2 = st.columns([2,3])
        css_format = """
            <style>
              .mypropertys {
                width: 100%;
                height: 1000px;
                overflow-y: scroll;
                text-align: center;
                display: inline-block;
                margin: 0px auto;
              }
              .property-image {
                width: 100%;
            	   height: 250px;
            	   overflow: hidden; 
                margin-bottom: 10px;
              }
              .price-info {
                font-family: 'Roboto', sans-serif;
                font-size: 20px;
                margin-bottom: 2px;
                text-align: center;
              }
              .caracteristicas-info {
                font-family: 'Roboto', sans-serif;
                font-size: 12px;
                margin-bottom: 2px;
                text-align: center;
              }
              img{
                max-width: 100%;
                width: 100%;
                height:100%;
                object-fit: cover;
                margin-bottom: 10px; 
              }
            </style>
        """
        img_style = '''
        <style>               
            .property-image{
              flex: 1;
            }
            img{
                width:200px;
                height:120px;
                object-fit: cover;
                margin-bottom: 2px; 
            }
        </style>
        '''
        
        if tiponegocio.lower()=='venta':
            datashow = dataventazona.copy()
        if tiponegocio.lower()=='arriendo':
            datashow = dataarriendozona.copy()
            
        if filtro=='Menor precio':
            datashow = datashow.sort_values(by=['valor'],ascending=True)
        if filtro=='Mayor precio':
            datashow = datashow.sort_values(by=['valor'],ascending=False)
        if filtro=='Menor área':
            datashow = datashow.sort_values(by=['areaconstruida'],ascending=True)
        if filtro=='Mayor área':
            datashow = datashow.sort_values(by=['areaconstruida'],ascending=False)
        if filtro=='Menor habitaciones':
            datashow = datashow.sort_values(by=['habitaciones'],ascending=True)
        if filtro=='Mayor habitaciones':
            datashow = datashow.sort_values(by=['habitaciones'],ascending=False)

        with col3w:
            st.write('')
            st.write('')
            csv = convert_df(datashow)     
            st.download_button(
               "Descargar los datos",
               csv,
               "info_ofertas.csv",
               "text/csv",
               key='info_ofertas'
            )  
                
        m        = folium.Map(location=[latitud, longitud], zoom_start=16,tiles="cartodbpositron")
        imagenes = ''
        for i, inmueble in datashow.iterrows():
        
            if isinstance(inmueble['imagen_principal'], str) and len(inmueble['imagen_principal'])>20: imagen_principal =  inmueble['imagen_principal']
            else: imagen_principal = "https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/sin_imagen.png"
            caracteristicas = f'<strong>{inmueble["areaconstruida"]}</strong> mt<sup>2</sup> | <strong>{int(inmueble["habitaciones"])}</strong> hab | <strong>{int(inmueble["banos"])}</strong> baños | <strong>{int(inmueble["garajes"])}</strong> pq'
            url_export      = f"{url}/Ficha?code={inmueble['code']}&tiponegocio={tiponegocio}&tipoinmueble={tipoinmueble}"
            
            if pd.isnull(inmueble['direccion']): direccionlabel = '<p class="caracteristicas-info">&nbsp</p>'
            else: direccionlabel = f'''<p class="caracteristicas-info">Dirección: {inmueble['direccion'][0:35]}</p>'''
            
            imagenes += f'''
            <div class="col-xl-4 col-sm-6 mb-xl-2 mb-2">
              <div class="card h-100">
                <div class="card-body p-3">
                  <a href="{url_export}" target="_blank">
                    <div class="property-image">
                      <img src="{imagen_principal}" alt="property image" onerror="this.src='https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/sin_imagen.png';">
                    </div>
                  </a>
                  <p class="price-info"><b>${inmueble['valor']:,.0f}</b></h3>
                  {direccionlabel}
                  <p class="caracteristicas-info">{caracteristicas}</p>
                </div>
              </div>
            </div>            
            '''
            string_popup = f'''
            <!DOCTYPE html>
            <html>
              <head>
                {img_style}
              </head>
              <body>
                  <div>
                  <a href="{url_export}" target="_blank">
                  <div class="property-image">
                      <img src="{imagen_principal}"  alt="property image" onerror="this.src='https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/sin_imagen.png';">
                  </div>
                  </a>
                  <b> Direccion: {inmueble['direccion']}</b><br>
                  <b> Precio: ${inmueble['valor']:,.0f}</b><br>
                  <b> Área: {inmueble['areaconstruida']}</b><br>
                  <b> Habitaciones: {int(inmueble['habitaciones'])}</b><br>
                  <b> Baños: {int(inmueble['banos'])}</b><br>
                  <b> Garajes: {int(inmueble['garajes'])}</b><br>
                  </div>
              </body>
            </html>
            '''
            folium.Marker(location=[inmueble["latitud"], inmueble["longitud"]], popup=string_popup).add_to(m)
    
        with col1:
            polygon = circle_polygon(inputvar['metros'],latitud,longitud)
            folium.GeoJson(polygon).add_to(m)              
            st_map = st_folium(m,width=720,height=1000)
            
        texto = f"""
            <!DOCTYPE html>
            <html>
              <head>
              <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-icons.css" rel="stylesheet"/>
              <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-svg.css" rel="stylesheet"/>
              <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/soft-ui-dashboard.css?v=1.0.7" id="pagestyle" rel="stylesheet"/>
              {css_format}
              </head>
              <body>
              <div class="mypropertys">
              <div class="container-fluid py-4">
                <div class="row">
                {imagenes}
                </div>
              </div>
              </div>
              </body>
            </html>
            """
        with col2:
            texto = BeautifulSoup(texto, 'html.parser')
            st.markdown(texto, unsafe_allow_html=True)
        
            
    components.html(
        """
    <script>
    const elements = window.parent.document.querySelectorAll('.stButton button')
    elements[0].style.backgroundColor = 'lightblue';
    elements[0].style.fontWeight = 'bold';
    elements[0].style.width = '100%';
    </script>
    """
    )


def getforecast(inputvar):
    
    tipoinmueble = inputvar['tipoinmueble']
    forecastlist = {'venta': [],'arriendo': []}
    
    fcoddir,scacodigo = ['']*2
    if 'direccion' in inputvar:
        fcoddir = coddir(inputvar['direccion'])
    
    latitud,longitud = [None]*2
    datamarketventa,datamarketarriendo,datagaleria,databarrio,barriopricing,barriocaracterizacion,barriovalorizacion,dataventazona,dataarriendozona = [pd.DataFrame()]*9
    
    if fcoddir!='':
        dataconjunto,datapredios,datalote              = getdatanivel1(fcoddir)
        datamarketventa,datamarketarriendo,datagaleria = getdatanivel3(fcoddir)
        
        if dataconjunto.empty is False:
            if 'scacodigo' in dataconjunto:
                scacodigo = dataconjunto['scacodigo'].iloc[0]
            if 'vetustez_median' in dataconjunto: 
                try: inputvar['antiguedad'] = datetime.now().year-dataconjunto['vetustez_median'].iloc[0]
                except: pass
            if 'estrato' in dataconjunto:
                if dataconjunto['estrato'].iloc[0]>=1 and dataconjunto['estrato'].iloc[0]<=6:
                    inputvar['estrato'] = dataconjunto['estrato'].iloc[0]
                
        if datalote.empty is False:
            poly             = wkt.loads(datalote["wkt"].iloc[0])
            latitud,longitud = [poly.centroid.y,poly.centroid.x]
        else:
            latitud, longitud = obtener_coordenadas(dataconjunto, datamarketventa, datamarketarriendo)
    
    if latitud is None or longitud is None:
        latitud, longitud = getlatlng(inputvar['direccion'])
             
    if latitud is not None and longitud is not None:
        inputvar['latitud']  = latitud
        inputvar['longitud'] = longitud
        dataventazona,dataarriendozona  = getdataradio(inputvar)

    if scacodigo=='' and latitud is not None and longitud is not None:
        scacodigo = getscacodigo(latitud,longitud)

    #-------------------------------------------------------------------------#
    # Tiempo de construido
    if 'antiguedad' in inputvar and inputvar['antiguedad']>=0:
        if inputvar['antiguedad']<=1:
            inputvar['tiempodeconstruido'] = 'Menos de 1 año'
        elif inputvar['antiguedad']>1 and inputvar['antiguedad']<=8:
            inputvar['tiempodeconstruido'] = '1 a 8 años'
        elif inputvar['antiguedad']>8 and inputvar['antiguedad']<=15:
            inputvar['tiempodeconstruido'] = '9 a 15 años'
        elif inputvar['antiguedad']>15 and inputvar['antiguedad']<=30:
            inputvar['tiempodeconstruido'] = '16 a 30 años'
        else: inputvar['tiempodeconstruido'] = 'más de 30 años'


    if scacodigo is not None and scacodigo!='':
        
        barriopricing,barriocaracterizacion,barriovalorizacion = getdatanivel6(scacodigo)
        
        #---------------------------------------------------------------------#
        # Codificacion       
        pickle_file_path = "data/colombia_bogota_scacodigo.pkl"
        with open(pickle_file_path, "rb") as f:
            barrio_codigo = pickle.load(f)
            
        pickle_file_path = "data/colombia_bogota_tiempoconstruido.pkl"
        with open(pickle_file_path, "rb") as f:
            tiempodeconstruido_codigo = pickle.load(f)
            
        pickle_file_path = "data/colombia_bogota_variables.pkl"
        with open(pickle_file_path, "rb") as f:
            variables = pickle.load(f)
    
        inputvar['scacodigo']          = barrio_codigo.transform([scacodigo])[0]
        inputvar['tiempodeconstruido'] = tiempodeconstruido_codigo.transform([inputvar['tiempodeconstruido']])[0] 
         
        #---------------------------------------------------------------------#
        # Modelo XGboosting
        for tiponegocio in ['Venta','Arriendo']:
            
            pickle_file_path = f"data/xgboosting_{tiponegocio.lower()}_{tipoinmueble.lower()}.pkl"
            with open(pickle_file_path, 'rb') as file:
                model = pickle.load(file)
            
            datamodel      = pd.DataFrame([inputvar])
            datamodel      = datamodel[variables]
            prediccion_log = model.predict(datamodel)
            prediccion     = np.exp(prediccion_log)
            forecastlist[tiponegocio.lower()].append({'model':'forecast_xgboosting','value':prediccion[0]})
    
        #---------------------------------------------------------------------#
        # Modelo ANN
        for tiponegocio in ['Venta','Arriendo']:

            pickle_file_path = f"data/ANN_bogota_{tiponegocio.lower()}_{tipoinmueble.lower()}"
            model            = pd.read_pickle(pickle_file_path,compression='gzip')
            salida           = model['salida'].iloc[0]
            forecastlist[tiponegocio.lower()].append({'model':'forecast_model','value':pricingforecast(salida,inputvar)['valorestimado']})
        
        #---------------------------------------------------------------------#
        if barriopricing.empty is False:
            for tiponegocio in ['Venta','Arriendo']:
                
                # Forecast: Valor por mt2 del barrio
                datapaso = barriopricing[(barriopricing['tipo']=='barrio') & (barriopricing['obs']>=10) & (barriopricing['tiponegocio']==tiponegocio) ]
                if datapaso.empty is False and 'areaconstruida' in inputvar and inputvar['areaconstruida']>0:
                    precioforecast = datapaso['valormt2'].iloc[0]*inputvar['areaconstruida']
                    forecastlist[tiponegocio.lower()].append({'model':'forecast_barrio','value':precioforecast})
    
                # Forecast: Valor por mt2 del barrio, con mismas habitaciones, baños y garajes
                if 'habitaciones' in inputvar and 'banos' in inputvar and 'garajes' in inputvar:
                    datapaso = barriopricing[(barriopricing['tipo']=='complemento') & (barriopricing['tiponegocio']==tiponegocio) & (barriopricing['obs']>=10) & (barriopricing['habitaciones']==inputvar['habitaciones'])  & (barriopricing['banos']==inputvar['banos'])  & (barriopricing['garajes']==inputvar['garajes']) ]
                    if datapaso.empty is False:
                        precioforecast = datapaso['valormt2'].iloc[0]*inputvar['areaconstruida']
                        forecastlist[tiponegocio.lower()].append({'model':'forecast_barrio_complemento','value':precioforecast})
                 
    #-------------------------------------------------------------------------#
    # Forecast: datos del mismo conjunto
    if datamarketventa.empty is False and 'areaconstruida' in inputvar and inputvar['areaconstruida']>0: 
        forecastlist['venta'].append({'model':'forecast_edificio_similiar','value':datamarketventa['valormt2'].median()*inputvar['areaconstruida']})
        areamin = inputvar['areaconstruida']*0.85
        areamax = inputvar['areaconstruida']*1.15
        idd     = ((datamarketventa['areaconstruida']>=areamin) & (datamarketventa['areaconstruida']<=areamax)) & (datamarketventa['habitaciones']==inputvar['habitaciones'])
        if sum(idd)>4:
            forecastlist['venta'].append({'model':'forecast_edificio','value':datamarketventa[idd]['valormt2'].median()*inputvar['areaconstruida']})
        
    if datamarketarriendo.empty is False and 'areaconstruida' in inputvar and inputvar['areaconstruida']>0: 
        forecastlist['arriendo'].append({'model':'forecast_edificio_similiar','value':datamarketarriendo['valormt2'].median()*inputvar['areaconstruida']})
        areamin = inputvar['areaconstruida']*0.85
        areamax = inputvar['areaconstruida']*1.15
        idd     = ((datamarketarriendo['areaconstruida']>=areamin) & (datamarketarriendo['areaconstruida']<=areamax)) & (datamarketarriendo['habitaciones']==inputvar['habitaciones'])
        if sum(idd)>5:
            forecastlist['arriendo'].append({'model':'forecast_edificio','value':datamarketarriendo[idd]['valormt2'].median()*inputvar['areaconstruida']})
    
    #-------------------------------------------------------------------------#
    # Forecast: datos de inmuebles similares misma zona
    if dataventazona.empty is False  and 'areaconstruida' in inputvar and inputvar['areaconstruida']>0:
        forecastlist['venta'].append({'model':'forecast_zona','value':dataventazona['valormt2'].median()*inputvar['areaconstruida']})
    
    if dataarriendozona.empty is False  and 'areaconstruida' in inputvar and inputvar['areaconstruida']>0:
        forecastlist['arriendo'].append({'model':'forecast_zona','value':dataarriendozona['valormt2'].median()*inputvar['areaconstruida']})
  
    #-------------------------------------------------------------------------#
    # Resultados
    forecast_venta    = pricing_ponderador(forecastlist['venta'])
    forecast_arriendo = pricing_ponderador(forecastlist['arriendo'])
    
    return forecast_venta,forecast_arriendo,forecastlist,latitud,longitud,dataconjunto,datapredios,datalote,datamarketventa,datamarketarriendo,datagaleria,dataventazona,dataarriendozona
    