import streamlit as st
import folium
import pandas as pd
import json

from bs4 import BeautifulSoup
from shapely.geometry import mapping
from shapely import wkt
from streamlit_folium import st_folium
from datetime import datetime, timedelta
from scripts.getdata import conjuntos_direcciones,getdatanivel1,getdatanivel2,getdatanivel3,getdatanivel4,getdatanivel5,getdatanivel6,getscacodigo,getdatacatastro,obtener_coordenadas,getlatlng,getinfochip,formatofecha
from scripts.coddir import coddir

# streamlit run D:\Dropbox\Empresa\Buydepa\PROYECTOS\proceso\appcolombia\Home.py
# https://streamlit.io/
# pipreqs --encoding utf-8 "D:\Dropbox\Empresa\Buydepa\PROYECTOS\proceso\appcolombia"
# st.secrets -> C:\Users\LENOVO T14.streamlit\secrets.toml
# st.write(str(st.__path__))
# st.write(str(st.secrets._file_path))
# st.write(str(st.secrets.get))

url = "https://buydepa-colombia.streamlit.app/"

# https://oficinavirtual.shd.gov.co/ConsultaPagos/ConsultaPagos.html

def change_ed_nombre():
    datafilter = conjuntos_direcciones()
    if st.session_state.ed_nombre!='':
        datafilter = datafilter[datafilter['nombre_conjunto']==st.session_state.ed_nombre]
        idd        = (datafilter['new_dir'].isnull()) | (datafilter['new_dir']=='')
        if sum(~idd)>0:
            st.session_state.options_ed_dir = datafilter[~idd]['new_dir'].unique()
            st.session_state.ed_dir = st.session_state.options_ed_dir[0]
            st.session_state.options_ed_dir = list(sorted(st.session_state.options_ed_dir))
            
    if st.session_state.ed_nombre=='':
        idd             = (datafilter['new_dir'].isnull()) | (datafilter['new_dir']=='')
        st.session_state.options_ed_dir = datafilter[~idd]['new_dir'].unique()
        st.session_state.options_ed_dir = ['']+list(sorted(st.session_state.options_ed_dir)) 
        st.session_state.ed_dir = ''
       
def convert_df(df):
   return df.to_csv(index=False).encode('utf-8')


def change_ed_dir():
    datafilter                         = conjuntos_direcciones()
    idd                                = (datafilter['nombre_conjunto'].isnull()) | (datafilter['nombre_conjunto']=='')
    st.session_state.options_ed_nombre = ['']+list(sorted(datafilter[~idd]['nombre_conjunto'].unique()))
    if st.session_state.ed_dir!='':
        datafilter = datafilter[datafilter['new_dir']==st.session_state.ed_dir]
        idd        = (datafilter['nombre_conjunto'].isnull()) | (datafilter['nombre_conjunto']=='')
        if sum(~idd)>0:
            st.session_state.ed_nombre = datafilter[~idd]['nombre_conjunto'].iloc[0]
    
    
def main():

    formato = {
                'coddir':'',
                'ed_nombre':'',
                'ed_dir':'',
               }
    
    for key,value in formato.items():
        if key not in st.session_state: 
            st.session_state[key] = value
         
    datadirconj = conjuntos_direcciones()
    if 'options_ed_nombre' not in st.session_state:
        idd             = (datadirconj['nombre_conjunto'].isnull()) | (datadirconj['nombre_conjunto']=='')
        st.session_state.options_ed_nombre = datadirconj[~idd]['nombre_conjunto'].unique()
        st.session_state.options_ed_nombre = ['']+list(sorted(st.session_state.options_ed_nombre))
    
    if 'options_ed_dir' not in st.session_state:
        idd             = (datadirconj['new_dir'].isnull()) | (datadirconj['new_dir']=='')
        st.session_state.options_ed_dir = datadirconj[~idd]['new_dir'].unique()
        st.session_state.options_ed_dir = ['']+list(sorted(st.session_state.options_ed_dir))
    
    col1, col2, col3, col4 = st.columns([1,1,2,1])
    with col1:
        st.selectbox('Nombre del edificio',key='ed_nombre',options=st.session_state.options_ed_nombre,on_change=change_ed_nombre)
    
    with col2:
        st.selectbox('Dirección',key='ed_dir',options=st.session_state.options_ed_dir,on_change=change_ed_dir)
        
    with col3:
        direccion = st.text_input('Editar o escribir dirección',value=st.session_state.ed_dir)
        
    with col4:
        st.write('')
        st.write('')
        if st.button('Buscar'):
            if direccion!='': 
                st.session_state.coddir    = coddir(direccion)
                #st.session_state.ed_dir    = ''
                #st.session_state.ed_nombre = ''
                del st.session_state['options_ed_dir']
                del st.session_state['options_ed_nombre']
                st.experimental_rerun()


    if st.session_state.coddir!='':

        #-------------------------------------------------------------------------#
        # DATA
        #-------------------------------------------------------------------------#
        dataconjunto,datapredios,datalote              = getdatanivel1(st.session_state.coddir)
        dataprocesos                                   = getdatanivel2(st.session_state.coddir,datapredios)
        datamarketventa,datamarketarriendo,datagaleria = getdatanivel3(st.session_state.coddir)
        datarecorrido                                  = getdatanivel4(st.session_state.coddir)

        latitud, longitud = obtener_coordenadas(dataconjunto, datamarketventa, datamarketarriendo)
        if latitud is None or longitud is None:
            latitud, longitud = getlatlng(direccion)
            
        databarrio,barriopricing,barriocaracterizacion,barriovalorizacion = getdatanivel5(latitud,longitud)
    
        scacodigo = ''
        if dataconjunto.empty is False:
            if 'scacodigo' in dataconjunto:
                scacodigo = dataconjunto['scacodigo'].iloc[0]


        if scacodigo=='' and latitud is not None and longitud is not None:
            scacodigo = getscacodigo(latitud,longitud)
    
        if scacodigo!='':
            barriopricing,barriocaracterizacion,barriovalorizacion = getdatanivel6(scacodigo)
            
    
        if dataconjunto.empty is False or datapredios.empty is False or datalote.empty is False or dataprocesos.empty is False or datamarketventa.empty is False or datamarketarriendo.empty is False or datagaleria.empty is False or datarecorrido.empty is False or databarrio.empty is False or barriopricing.empty is False or barriocaracterizacion.empty is False or barriovalorizacion.empty is False:
            #-------------------------------------------------------------------------#
            # DATA
            #-------------------------------------------------------------------------#    
            if dataconjunto.empty is False:
                html = """
                <!DOCTYPE html>
                <html>
                <style>
                    .space {
                        height: 60px;
                    }
                </style>
                <body>
                <div class="space"></div>
                </body>
                </html>
                """
                texto = BeautifulSoup(html, 'html.parser')
                st.markdown(texto, unsafe_allow_html=True) 
                    
                col1, col2 = st.columns([2,3])
                
                with col1:
                    formato = {
                        'locnombre': 'Localidad',
                        'barrio': 'Barrio',
                        'direccion': 'Dirección',
                        'nombre_conjunto': 'Edificio',
                        'vetustez_max': 'Antiguedad',
                        'estrato': 'Estrato',
                        'maxpiso': 'Pisos',
                        'unidades': '# unidades'
                    }
                    
            
                    cajones_por_fila = 1
                    paso      = ''
                    html_paso = ''
                    index     = 0
                    # Generar las cajas en el diseño
                    for key,value in formato.items():
                        if key in dataconjunto and (dataconjunto[key].iloc[0] is not None or dataconjunto[key].iloc[0]!=''):
                            tamanoletra = '1.5rem'
                            if len(str(dataconjunto[key].iloc[0]))>20:
                                tamanoletra = '1.2rem'
                                
                            # Crear el bloque HTML correspondiente a cada iteración
                            bloque_html = f"""
                            <div class="col-xl-6 col-sm-6 mb-xl-0 mb-2">
                              <div class="card">
                                <div class="card-body p-3">
                                  <div class="row">
                                    <div class="numbers">
                                      <h3 class="font-weight-bolder mb-0" style="text-align: center;font-size: {tamanoletra};">{dataconjunto[key].iloc[0]}</h3>
                                      <p class="mb-0 text-capitalize" style="font-weight: 300;font-size: 1rem;text-align: center;">{value}</p>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>
                            """
                            
                            # Agregar el bloque al paso actual
                            paso += bloque_html
                            
                            # Si hemos completado dos iteraciones, anadir el paso a un contenedor
                            if (index + 1) % (cajones_por_fila * 2) == 0 or index == len(formato) - 1:
                                html_paso += f"""
                                <div class="container-fluid py-1">
                                  <div class="row">
                                    {paso}
                                  </div>
                                </div>"""
                                paso = ''
                            index += 1
                            
                    html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                      <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-icons.css" rel="stylesheet" />
                      <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-svg.css" rel="stylesheet" />
                      <link id="pagestyle" href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/soft-ui-dashboard.css?v=1.0.7" rel="stylesheet" />
                    </head>
                    <body>
                    {html_paso}
                    </body>
                    </html>        
                    """
                    
                    texto = BeautifulSoup(html, 'html.parser')
                    st.markdown(texto, unsafe_allow_html=True)
            
                with col2:
                    html = """
                    <!DOCTYPE html>
                    <html>
                    <style>
                        .space {
                            height: 20px;
                        }
                    </style>
                    <body>
                    <div class="space"></div>
                    </body>
                    </html>
                    """
                    texto = BeautifulSoup(html, 'html.parser')
                    st.markdown(texto, unsafe_allow_html=True)  
                    if datalote.empty is False:
                        with col2:
                            geojson_data = mapping(wkt.loads(datalote["wkt"].iloc[0]))
                            poly         = wkt.loads(datalote["wkt"].iloc[0])
                            m            = folium.Map(location=[poly.centroid.y, poly.centroid.x], zoom_start=18,tiles="cartodbpositron")
                            folium.GeoJson(geojson_data).add_to(m)
                            st_map = st_folium(m,width=800,height=450)
                 
            #-------------------------------------------------------------------------#
            # INMUEBLES VENDIDOS
            #-------------------------------------------------------------------------#  
            snr_lastyears     = ""
            snr_lastyear      = ""
            snr_valorxmt2     = ""
            snr_tabla         = ""
            dataprocesosdocid = dataprocesos.copy()
            if dataprocesos.empty is False:
                dataprocesos = dataprocesos[dataprocesos['codigo'].isin(['0125','125','0168','168'])]
                
            if dataprocesos.empty is False:
                # Venta de inmuebles ultimos 4 anos
                snr_lastyears = f"""
                <div class="col-xl-4 col-sm-6 mb-xl-0 mb-2">
                  <div class="card-body p-3">
                    <div class="row">
                      <div class="numbers">
                        <h3 class="font-weight-bolder mb-0" style="text-align: center; font-size: 1.5rem;">{len(dataprocesos)}</h3>
                        <p class="mb-0 text" style="font-weight: 300; font-size: 1rem; text-align: center;">Ventas en los últimos 4 años</p>
                      </div>
                    </div>
                  </div>
                </div>
                """
                
                # Venta de inmuebles ultimo ano
                one_year_ago = datetime.now() - timedelta(days=365)
                snr_lastyear = ""
                try:
                    idd = dataprocesos['Fecha']>=one_year_ago
                except:
                    idd = dataprocesos['fecha_documento_publico']>=one_year_ago
                if sum(idd)>0:
                    snr_lastyear  = f"""
                    <div class="col-xl-4 col-sm-6 mb-xl-0 mb-2">
                      <div class="card-body p-3">
                        <div class="row">
                          <div class="numbers">
                            <h3 class="font-weight-bolder mb-0" style="text-align: center; font-size: 1.5rem;">{sum(idd)}</h3>
                            <p class="mb-0 text" style="font-weight: 300; font-size: 1rem; text-align: center;">Ventas en el último año</p>
                          </div>
                        </div>
                      </div>
                    </div>
                    """ 
                    
                # Precio promedio por mt2
                df = dataprocesos[dataprocesos['nombre']=='COMPRAVENTA']
                snr_valorxmt2 = ""
                if df.empty is False:
                    df['valormt2']   = df['cuantia']/df['areaconstruida']
                    valormt2building = df['valormt2'].median()
                    snr_valorxmt2   = f"""
                    <div class="col-xl-4 col-sm-6 mb-xl-0 mb-2">
                      <div class="card-body p-3">
                        <div class="row">
                          <div class="numbers">
                            <h3 class="font-weight-bolder mb-0" style="text-align: center; font-size: 1.5rem;">${valormt2building:,.0f}</h3>
                            <p class="mb-0 text" style="font-weight: 300; font-size: 1rem; text-align: center;">Valor de venta por mt2</p>
                          </div>
                        </div>
                      </div>
                    </div>
                    """ 
    
                # Tabla
                datatable            = dataprocesos[['direccion', 'areaconstruida', 'fecha_documento_publico', 'cuantia']].copy()
                datatable['cuantia'] = datatable['cuantia'].apply(lambda x: f'${x:,.0f}')
                datatable['fecha_documento_publico'] = datatable['fecha_documento_publico'].apply(lambda x: x.strftime('%Y-%m-%d'))
                datatable.rename(columns={'direccion': 'Predio','areaconstruida':'Area construida', 'nombre': 'Tipo de proceso', 'tarifa': 'Tarifa', 'cuantia': 'Valor', 'tipo_documento_publico': 'Tipo', 'numero_documento_publico': '# documento', 'fecha_documento_publico': 'Fecha', 'oficina': 'Oficina registro', 'entidad': 'Notaria'},inplace=True)
                
                html_tabla = ""
                for _,i in datatable.iterrows():
                    html_tabla += f""" 
                    <tr>
                      <td class="align-middle text-center text-sm" style="border-top:none; border-left:none;border-right:none;border-bottom: 1px solid #ccc;">
                        <h6 class="mb-0 text-sm">{i['Predio']}</h6>
                      </td>
                      <td class="align-middle text-center text-sm" style="border-top:none; border-left:none;border-right:none;border-bottom: 1px solid #ccc;">
                        <h6 class="mb-0 text-sm" style="font-size: 18px;">{i['Area construida']}</h6>
                      </td>
                      <td class="align-middle text-center text-sm" style="border-top:none; border-left:none;border-right:none;border-bottom: 1px solid #ccc;">
                        <h6 class="mb-0 text-sm">{i['Fecha']}</h6>
                      </td>
                      <td class="align-middle text-center text-sm" style="border-top:none; border-left:none;border-right:none;border-bottom: 1px solid #ccc;">
                        <h6 class="mb-0 text-sm">{i['Valor']}</h6>
                      </td>                      
                    </tr>     
                    """
                snr_tabla = f"""
                <div class="snr-table">
                    <table class="table align-items-center mb-0">
                      <thead>
                        <tr style="margin-bottom: 0px;">
                          <th class="align-middle text-center" style="border-top:none; border-left:none;border-right:none;border-bottom: 1px solid #ccc;">Predio</th>
                          <th class="align-middle text-center" style="border-top:none; border-left:none;border-right:none;border-bottom: 1px solid #ccc;">Area construida</th>
                          <th class="align-middle text-center" style="border-top:none; border-left:none;border-right:none;border-bottom: 1px solid #ccc;">Fecha</th>
                          <th class="align-middle text-center" style="border-top:none; border-left:none;border-right:none;border-bottom: 1px solid #ccc;">Valor</th>
                        </tr>
                      </thead>
                      <tbody>
                      {html_tabla}
                      </tbody>
                    </table>
                </div>
                """
    
            #-------------------------------------------------------------------------#
            # INFO CATASTRAL
            #-------------------------------------------------------------------------#  
            catastro_avaluomt2  = ""
            catastro_predialmt2 = ""
            catastro_tabla      = ""
            if datapredios.empty is False:
    
                html_tabla        = ""
                datapredios       = datapredios.sort_values(by='predirecc',ascending=True)
                chip              = tuple(datapredios['prechip'].to_list())
                datamatriculachip = getinfochip(chip)
                if datamatriculachip.empty is False:
                    datamatriculachip.rename(columns={'chip':'prechip'},inplace=True)
                    datapredios        = datapredios.merge(datamatriculachip,on='prechip',how='left',validate='1:1')
                    datavalorcatastral = datapredios[(datapredios['preaconst']>20) & (datapredios['valorAutoavaluo']>0)]
                    if datavalorcatastral.empty is False:
                        datavalorcatastral['avaluo_valormt2']  = datavalorcatastral['valorAutoavaluo']/datavalorcatastral['preaconst']
                        datavalorcatastral['predial_valormt2'] = datavalorcatastral['valorImpuesto']/datavalorcatastral['preaconst']
                        
                        catastro_avaluomt2 = f"""
                        <div class="col-xl-6 col-sm-6 mb-xl-0 mb-2">
                          <div class="card-body p-3">
                            <div class="row">
                              <div class="numbers">
                                <h3 class="font-weight-bolder mb-0" style="text-align: center; font-size: 1.5rem;">${datavalorcatastral['avaluo_valormt2'].median():,.0f}</h3>
                                <p class="mb-0 text" style="font-weight: 300; font-size: 1rem; text-align: center;">Avalúo catastral por mt2</p>
                              </div>
                            </div>
                          </div>
                        </div>
                        """
                        catastro_predialmt2 = f"""
                        <div class="col-xl-6 col-sm-6 mb-xl-0 mb-2">
                          <div class="card-body p-3">
                            <div class="row">
                              <div class="numbers">
                                <h3 class="font-weight-bolder mb-0" style="text-align: center; font-size: 1.5rem;">${datavalorcatastral['predial_valormt2'].median():,.0f}</h3>
                                <p class="mb-0 text" style="font-weight: 300; font-size: 1rem; text-align: center;">Impuesto predial por mt2</p>
                              </div>
                            </div>
                          </div>
                        </div>
                        """                    
                
                for _,i in datapredios.iterrows():
                    html_tabla += f""" 
                    <tr>
                      <td class="align-middle text-center text-sm" style="border-top:none; border-left:none;border-right:none;border-bottom: 1px solid #ccc;">
                        <h6 class="mb-0 text-sm">{i['predirecc']}</h6>
                      </td>
                      <td class="align-middle text-center text-sm" style="border-top:none; border-left:none;border-right:none;border-bottom: 1px solid #ccc;">
                        <h6 class="mb-0 text-sm">{i['preaconst']}</h6>
                      </td>
                      <td class="align-middle text-center text-sm" style="border-top:none; border-left:none;border-right:none;border-bottom: 1px solid #ccc;">
                        <h6 class="mb-0 text-sm">{i['prechip']}</h6>
                      </td>
                      <td class="align-middle text-center text-sm" style="border-top:none; border-left:none;border-right:none;border-bottom: 1px solid #ccc;">
                        <h6 class="mb-0 text-sm">{i['precedcata']}</h6>
                      </td>                      
                    </tr>     
                    """
                catastro_tabla = f"""
                <div class="catastro-table">
                    <table class="table align-items-center mb-0">
                      <thead>
                        <tr style="margin-bottom: 0px;">
                          <th class="align-middle text-center" style="border-top:none; border-left:none;border-right:none;border-bottom: 1px solid #ccc;">Predio</th>
                          <th class="align-middle text-center" style="border-top:none; border-left:none;border-right:none;border-bottom: 1px solid #ccc;">Area construida</th>
                          <th class="align-middle text-center" style="border-top:none; border-left:none;border-right:none;border-bottom: 1px solid #ccc;">Chip</th>
                          <th class="align-middle text-center" style="border-top:none; border-left:none;border-right:none;border-bottom: 1px solid #ccc;">Cedula Catastral</th>
                        </tr>
                      </thead>
                      <tbody>
                      {html_tabla}
                      </tbody>
                    </table>
                </div>
                """      
            #-------------------------------------------------------------------------#
            # PRESENTACION DE SNR E INFO CATASTRAL
            #-------------------------------------------------------------------------#
            if snr_lastyears!="" or snr_lastyear!= "" or snr_valorxmt2!= "" or snr_tabla!= "" or catastro_avaluomt2 != "" or catastro_predialmt2!= "" or catastro_tabla!= "":
                style = """
                <style>
                    .snr-table {
                      overflow-x: auto;
                      overflow-y: auto; 
                      max-width: 100%; 
                      max-height: 250px; 
                    }    
                    .catastro-table {
                      max-height: 250px; 
                      overflow-y: auto; 
                    }
                </style>
                """
                html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                  <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-icons.css" rel="stylesheet">
                  <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-svg.css" rel="stylesheet">
                  <link id="pagestyle" href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/soft-ui-dashboard.css?v=1.0.7" rel="stylesheet">
                  {style}
                </head>
                <body>
                  <div class="container-fluid py-4">
                    <div class="row">
                    
                      <div class="col-xl-6 col-sm-6 mb-xl-0 mb-2">
                        <div class="card h-100">
                          <div class="card-body p-3">
                            <div class="container-fluid py-4">
                              <div class="row" style="margin-bottom: -30px;">
                                <div class="card-body p-3">
                                  <div class="row">
                                    <div class="numbers">
                                      <h3 class="font-weight-bolder mb-0" style="text-align: center; font-size: 1.5rem;border-bottom: 0.5px solid #ccc; padding-bottom: 8px;">Historial de inmuebles vendidos</h3>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>                
                            <div class="container-fluid py-4">
                              <div class="row">
                                {snr_lastyears}
                                {snr_lastyear}
                                {snr_valorxmt2}
                                {snr_tabla}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      <div class="col-xl-6 col-sm-6 mb-xl-0 mb-2">
                        <div class="card h-100">
                          <div class="card-body p-3">
                            <div class="container-fluid py-4">
                              <div class="row" style="margin-bottom: -30px;">
                                <div class="card-body p-3">
                                  <div class="row">
                                    <div class="numbers">
                                      <h3 class="font-weight-bolder mb-0" style="text-align: center; font-size: 1.5rem;border-bottom: 0.5px solid #ccc; padding-bottom: 8px;">Informacion Catastral</h3>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>                
                            <div class="container-fluid py-4">
                              <div class="row">
                                {catastro_avaluomt2}
                                {catastro_predialmt2}
                                {catastro_tabla}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                      
                    </div>
                  </div>
                </body>
                </html>
                """     
                texto = BeautifulSoup(html, 'html.parser')
                st.markdown(texto, unsafe_allow_html=True)
            
            #-------------------------------------------------------------------------#
            # SELECCION DE INMUEBLE CATASTRO
            #-------------------------------------------------------------------------#  
            
            datavigencia    = pd.DataFrame()
            datapropietario = pd.DataFrame()
            datainfopredio  = pd.DataFrame()
            datasnrprocesos = pd.DataFrame()
            select_dir      = ''
            if datapredios.empty is False:
                col1, col2 , col3 = st.columns([1,1,2])
                with col1: 
                    opciones   = [''] + list(datapredios['predirecc'].unique())
                    select_dir = st.selectbox('Obtener mas información de cada predio (Dirección)', options=opciones)
                    if select_dir!='':
                        datainfopredio = datapredios[datapredios['predirecc']==select_dir]
                        chip           = datapredios[datapredios['predirecc']==select_dir]['prechip'].iloc[0]
                        datavigencia, datapropietario = getdatacatastro(chip)
                        datasnrprocesos = dataprocesosdocid[dataprocesosdocid['direccion']==select_dir]
                if datapropietario.empty is False:
                    try:
                        conteo = 1
                        for i in json.loads(datapropietario['email'].iloc[0]):
                            datapropietario[f'email{conteo}'] = i['direccion']
                            conteo += 1
                    except: pass
                    try:
                        conteo = 1
                        for i in json.loads(datapropietario['telefonos'].iloc[0]):
                            datapropietario[f'telefono{conteo}'] = i['numero']
                            conteo += 1
                    except: pass               
                    variables = [x for x in ['email','telefonos'] if x in datapropietario]
                    if variables!=[]:
                        datapropietario.drop(columns=variables,inplace=True)
    
                    csv = convert_df(datapropietario)     
                    with col2:
                        st.write("")
                        st.write("")
                    with col2:
                        st.download_button(
                           "Descargar información de propietario",
                           csv,
                           "info_predio.csv",
                           "text/csv",
                           key='info_predio_download'
                        )  
                    
    
            col1, col2 = st.columns([2,1])
            tabla_descripcion = ""
            impuestos_tabla   = ""
            if datainfopredio.empty is False:
                formato = [{'name':'Dirección','value':'predirecc','type':'str'},
                           {'name':'Área construida','value':'preaconst','type':'str'},
                           {'name':'Chip','value':'prechip','type':'str'},
                           {'name':'Matricula Inmobiliaria','value':'numeroMatriculaInmobiliaria','type':'str'},
                           {'name':'Cédula catastral','value':'precedcata','type':'str'},
                           {'name':'Avalúo catastral','value':'valorAutoavaluo','type':'money'},
                           {'name':'Impuesto predial','value':'valorImpuesto','type':'money'}
                           ]
                
                html_tabla = ""
                for i in formato:
                    htmlpaso = ""
                    if i['value'] in datainfopredio:
                        if i['type']=='money':
                            htmlpaso += f"""
                            <td class="align-middle text-center text-sm" style="border: none;padding: 8px;">
                              <h6 class="mb-0 text-sm">{i["name"]}</h6>
                            </td>
                            <td class="align-middle text-center text-sm" style="border: none;padding: 8px;">
                              <h6 class="mb-0 text-sm">${datainfopredio[i['value']].iloc[0]:,.0f}</h6>
                            </td>         
                            """
                        else: 
                            htmlpaso += f"""
                            <td class="align-middle text-center text-sm" style="border: none;padding: 8px;">
                              <h6 class="mb-0 text-sm">{i["name"]}</h6>
                            </td>
                            <td class="align-middle text-center text-sm" style="border: none;padding: 8px;">
                              <h6 class="mb-0 text-sm">{datainfopredio[i['value']].iloc[0]}</h6>
                            </td>             
                            """
                        html_tabla += f"""
                            <tr>
                                {htmlpaso}
                            </tr>
                        """
                tabla_descripcion = f"""
                <div>
                    <table class="table align-items-center mb-0">
                      <tbody>
                      {html_tabla}
                      </tbody>
                    </table>
                </div>
                """  
                        
            if datavigencia.empty is False:
                try:
                    datavigencia['fechaPresentacion'] = pd.to_datetime(datavigencia['fechaPresentacion'],errors='coerce')
                    datavigencia['fechaPresentacion'] = datavigencia['fechaPresentacion'].apply(lambda x: formatofecha(x))
                except: pass
            
                html_tabla = ""
                for _,i in datavigencia.iterrows():
                    html_tabla += f""" 
                    <tr>
                      <td class="align-middle text-center text-sm" style="border: none;padding: 8px;">
                        <h6 class="mb-0 text-sm">{i['vigencia']}</h6>
                      </td>
                      <td class="align-middle text-center text-sm" style="border: none;padding: 8px;">
                        <h6 class="mb-0 text-sm">{i['fechaPresentacion']}</h6>
                      </td>
                    """                  
                    if i['indPago'] is not None or pd.notna(i['indPago']):
                        html_tabla += f"""
                          <td class="align-middle text-center text-sm" style="border: none;padding: 8px;">
                            <h6 class="mb-0 text-sm">{i['indPago']}</h6>
                          </td>
                        """
                    else:
                        html_tabla += """
                          <td class="align-middle text-center text-sm" style="border: none;padding: 8px;">
                            <h6 class="mb-0 text-sm"></h6>
                          </td>
                        """
                    if i['idSoporteTributario'] is not None or pd.notna(i['idSoporteTributario']):
                        html_tabla += f"""
                          <td class="align-middle text-center text-sm" style="border: none;padding: 8px;">
                            <a href="https://oficinavirtual.shd.gov.co/barcode/certificacion?idSoporte={i['idSoporteTributario']}" target="_blank">
                              <img src="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/publicimg/pdf.png" alt="link" width="20" height="20">
                            </a>                    
                          </td>                      
                        </tr>     
                        """
                    else:
                        html_tabla += """
                          <td class="align-middle text-center text-sm" style="border: none;padding: 8px;">
                            <h6 class="mb-0 text-sm"></h6>
                          </td>
                        """
                impuestos_tabla = f"""
                <div class="impuesto-table">
                    <table class="table align-items-center mb-0">
                      <thead>
                        <tr style="margin-bottom: 0px;">
                          <th class="align-middle text-center" style="border-top:none; border-left:none;border-right:none;border-bottom: 1px solid #ccc;">Vigencia</th>
                          <th class="align-middle text-center" style="border-top:none; border-left:none;border-right:none;border-bottom: 1px solid #ccc;">Fecha</th>
                          <th class="align-middle text-center" style="border-top:none; border-left:none;border-right:none;border-bottom: 1px solid #ccc;">Indicador</th>
                          <th class="align-middle text-center" style="border-top:none; border-left:none;border-right:none;border-bottom: 1px solid #ccc;">Link</th>
                        </tr>
                      </thead>
                      <tbody>
                      {html_tabla}
                      </tbody>
                    </table>
                </div>
                """
                
                # Grafica avaluo catastral
                v = datavigencia.drop_duplicates(subset=['vigencia'],keep='first')
                v = v.groupby('vigencia').agg({'valorAutoavaluo':'first','valorImpuesto':'first'}).reset_index()
                
                html_chart = f'''
                const labels1 = {v['vigencia'].to_list()};
                const data1 = {v['valorAutoavaluo'].to_list()};
                const ctx1 = document.getElementById('chart1').getContext('2d');
                new Chart(ctx1, {{
                    type: 'bar',
                    data: {{
                        labels: labels1,
                        datasets: [{{
                            label: 'Avalúo Catastral',
                            data: data1,
                            backgroundColor: 'rgba(54, 162, 235, 0.4)',
                            borderWidth: 0
                        }}]
                    }},
                    options: {{
                        scales: {{
                            x: {{
                                grid: {{
                                    display: false
                                }}
                            }},
                            y: {{
                                beginAtZero: true,
                                ticks: {{
                                    callback: function(value) {{
                                        return '$' + value;
                                    }}
                                }}
                            }}
                        }},
                        plugins: {{
                            tooltip: {{
                                callbacks: {{
                                    label: function(context) {{
                                        return '$' + context.parsed.y;
                                    }}
                                }}
                            }}
                        }}
                    }}
                }});
                '''
                html_chart = BeautifulSoup(html_chart, 'html.parser')                  
                
            if select_dir!='':  
    
                style = """
                <style>
                    .impuesto-table {
                      overflow-x: auto;
                      overflow-y: auto; 
                      max-width: 100%; 
                      max-height: 400px; 
                    }
                    .chart-container {
                      display: flex;
                      justify-content: center;
                      align-items: center;
                      height: 100%;
                      width: 100%; 
                      margin-top:100px;
                    }
                    body {
                        font-family: Arial, sans-serif;
                    }
                    
                    canvas {
                        max-width: 100%;
                        max-height: 100%;
                        max-height: 300px;
                    }
                </style>
                """
                html = f"""
                <!DOCTYPE html>
                <html lang="es">
                <head>
                  <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-icons.css" rel="stylesheet">
                  <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-svg.css" rel="stylesheet">
                  <link id="pagestyle" href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/soft-ui-dashboard.css?v=1.0.7" rel="stylesheet">
                  <meta charset="UTF-8">
                  <meta name="viewport" content="width=device-width, initial-scale=1.0">
                  {style}
                </head>
                <body>
                  <div class="container-fluid py-4" style="margin-bottom: -30px;">
                    <div class="row">
        
                      <div class="col-xl-4 col-sm-6 mb-xl-0 mb-2">
                        <div class="card h-100">
                          <div class="card-body p-3">
                            <div class="container-fluid py-4">
                              <div class="row" style="margin-bottom: -30px;">
                                <div class="card-body p-3">
                                  <div class="row">
                                    <div class="numbers">
                                      <h3 class="font-weight-bolder mb-0" style="text-align: center; font-size: 1.5rem;border-bottom: 0.5px solid #ccc; padding-bottom: 8px;">Información general</h3>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>                       
                            <div class="container-fluid py-4">
                              <div class="row">
                                {tabla_descripcion}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      <div class="col-xl-4 col-sm-6 mb-xl-0 mb-2">
                        <div class="card h-100">
                          <div class="card-body p-3">  
                            <div class="container-fluid py-4">
                              <div class="row" style="margin-bottom: -30px;">
                                <div class="card-body p-3">
                                  <div class="row">
                                    <div class="numbers">
                                      <h3 class="font-weight-bolder mb-0" style="text-align: center; font-size: 1.5rem;border-bottom: 0.5px solid #ccc; padding-bottom: 8px;">Prediales</h3>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>                       
                            <div class="container-fluid py-4">
                              <div class="row">
                                {impuestos_tabla}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      <div class="col-xl-4 col-sm-6 mb-xl-0 mb-2">
                        <div class="card h-100">
                          <div class="card-body p-3">  
                            <div class="container-fluid py-4">
                              <div class="row" style="margin-bottom: -30px;">
                                <div class="card-body p-3">
                                  <div class="row">
                                    <div class="numbers">  
                                        <div class="chart chart-container">
                                            <canvas id="chart1"></canvas>
                                        </div> 
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>                       
                          </div>
                        </div>
                      </div>
                      
                    </div>
                  </div>
                <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
                <script>
                {html_chart}
                </script>
                </body>
                </html>
                """
                texto = BeautifulSoup(html, 'html.parser')
                st.components.v1.html(html, height=620)
                         
            #-------------------------------------------------------------------------#
            # SELECCION DE INMUEBLE SNR PROCESO
            #-------------------------------------------------------------------------#  
            if datasnrprocesos.empty is False:
                try:
                    datasnrprocesos['fecha_documento_publico'] = pd.to_datetime(datasnrprocesos['fecha_documento_publico'],errors='coerce')
                    datasnrprocesos['fecha_documento_publico'] = datasnrprocesos['fecha_documento_publico'].apply(lambda x: formatofecha(x))
                except: pass
            
                html_tabla = ""
                for _,i in datasnrprocesos.iterrows():
                    html_tabla += f""" 
                    <tr>
                      <td class="align-middle text-center text-sm" style="border: none;padding: 8px;">
                        <h6 class="mb-0 text-sm">{i['nombre']}</h6>
                      </td>
                      <td class="align-middle text-center text-sm" style="border: none;padding: 8px;">
                        <h6 class="mb-0 text-sm">{i['fecha_documento_publico']}</h6>
                      </td>
                      <td class="align-middle text-center text-sm" style="border: none;padding: 8px;">
                        <h6 class="mb-0 text-sm">${i['cuantia']:,.0f} </h6>
                      </td>                  
                      <td class="align-middle text-center text-sm" style="border: none;padding: 8px;">
                        <h6 class="mb-0 text-sm">{i['tipo_documento_publico']}</h6>
                      </td>
                      <td class="align-middle text-center text-sm" style="border: none;padding: 8px;">
                        <h6 class="mb-0 text-sm">{i['numero_documento_publico']}</h6>
                      </td>  
                      <td class="align-middle text-center text-sm" style="border: none;padding: 8px;">
                        <h6 class="mb-0 text-sm">{i['oficina']}</h6>
                      </td>      
                      <td class="align-middle text-center text-sm" style="border: none;padding: 8px;">
                        <h6 class="mb-0 text-sm">{i['entidad']}</h6>
                      </td> 
                      <td class="align-middle text-center text-sm" style="border: none;padding: 8px;">
                        <a href="https://radicacion.supernotariado.gov.co/app/static/ServletFilesViewer?docId={i['docid']}" target="_blank">
                          <img src="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/publicimg/pdf.png" alt="link" width="20" height="20">
                        </a>                    
                      </td> 
                    """                  
    
                procesosnr_tabla = f"""
                <div class="snrproceso-table">
                    <table class="table align-items-center mb-0">
                      <thead>
                        <tr style="margin-bottom: 0px;">
                          <th class="align-middle text-center" style="border-top:none; border-left:none;border-right:none;border-bottom: 1px solid #ccc;">Proceso</th>
                          <th class="align-middle text-center" style="border-top:none; border-left:none;border-right:none;border-bottom: 1px solid #ccc;">Fecha</th>
                          <th class="align-middle text-center" style="border-top:none; border-left:none;border-right:none;border-bottom: 1px solid #ccc;">Cuantía</th>
                          <th class="align-middle text-center" style="border-top:none; border-left:none;border-right:none;border-bottom: 1px solid #ccc;">Tipo</th>
                          <th class="align-middle text-center" style="border-top:none; border-left:none;border-right:none;border-bottom: 1px solid #ccc;">Número</th>
                          <th class="align-middle text-center" style="border-top:none; border-left:none;border-right:none;border-bottom: 1px solid #ccc;">Zona</th>
                          <th class="align-middle text-center" style="border-top:none; border-left:none;border-right:none;border-bottom: 1px solid #ccc;">Notaría</th>
                          <th class="align-middle text-center" style="border-top:none; border-left:none;border-right:none;border-bottom: 1px solid #ccc;">Documento</th>
                        </tr>
                      </thead>
                      <tbody>
                      {html_tabla}
                      </tbody>
                    </table>
                </div>                         
                """
                style = """
                <style>
                    .snrproceso-table {
                      overflow-x: auto;
                      overflow-y: auto; 
                      max-width: 100%; 
                      max-height: 400px; 
                    }    
                </style>
                """
                html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                  <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-icons.css" rel="stylesheet">
                  <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-svg.css" rel="stylesheet">
                  <link id="pagestyle" href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/soft-ui-dashboard.css?v=1.0.7" rel="stylesheet">
                  {style}
                </head>
                <body>
                  <div class="container-fluid py-4">
                    <div class="row">
                      <div class="col-xl-12 col-sm-6 mb-xl-0 mb-2">
                        <div class="card h-100">
                          <div class="card-body p-3">  
                            <div class="container-fluid py-4">
                              <div class="row" style="margin-bottom: -30px;">
                                <div class="card-body p-3">
                                  <div class="row">
                                    <div class="numbers">
                                      <h3 class="font-weight-bolder mb-0" style="text-align: center; font-size: 1.5rem;border-bottom: 0.5px solid #ccc; padding-bottom: 8px;">Información notaría y registro</h3>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>                       
                            <div class="container-fluid py-4">
                              <div class="row">
                                {procesosnr_tabla}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </body>
                </html>
                """
                texto = BeautifulSoup(html, 'html.parser')
                st.markdown(texto, unsafe_allow_html=True)
                
            #-------------------------------------------------------------------------#
            # OFERTA - VENTA
            #-------------------------------------------------------------------------#
            venta_oferta   = ""
            venta_valormt2 = ""
            venta_imagenes = ""        
            if datamarketventa.empty is False:
                
                venta_oferta = f"""
                <div class="col-xl-6 col-sm-6 mb-xl-0 mb-2">
                  <div class="card-body p-3">
                    <div class="row">
                      <div class="numbers">
                        <h3 class="font-weight-bolder mb-0" style="text-align: center; font-size: 1.5rem;">{len(datamarketventa)}</h3>
                        <p class="mb-0 text" style="font-weight: 300; font-size: 1rem; text-align: center;">Oferta de inmuebles</p>
                      </div>
                    </div>
                  </div>
                </div>
                """
                venta_valormt2 = f"""
                <div class="col-xl-6 col-sm-6 mb-xl-0 mb-2">
                  <div class="card-body p-3">
                    <div class="row">
                      <div class="numbers">
                        <h3 class="font-weight-bolder mb-0" style="text-align: center; font-size: 1.5rem;">${datamarketventa["valormt2"].median():,.0f}</h3>
                        <p class="mb-0 text" style="font-weight: 300; font-size: 1rem; text-align: center;">Valor por mt2</p>
                      </div>
                    </div>
                  </div>
                </div>
                """
                venta_imagenes = ''
                for i, inmueble in datamarketventa.iterrows():
                    if isinstance(inmueble['img1'], str) and len(inmueble['img1'])>20: imagen_principal =  inmueble['img1']
                    else: imagen_principal = "https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/sin_imagen.png"
                    
                    try:    garajes_inmueble = f' | <strong>{int(inmueble["garajes"])}</strong> pq'
                    except: garajes_inmueble = ""
                        
                    propertyinfo = f'<strong>{inmueble["areaconstruida"]}</strong> mt<sup>2</sup> | <strong>{int(inmueble["habitaciones"])}</strong> hab | <strong>{int(inmueble["banos"])}</strong> baños {garajes_inmueble}'
                    url_export   = f"{url}/Ficha?code={inmueble['code']}&tiponegocio=Venta&tipoinmueble=Apartamento" 
        
                    if isinstance(inmueble['direccion'], str): direccion = inmueble['direccion'][0:35]
                    else: direccion = '&nbsp'
                    venta_imagenes += f'''    
                      <div class="propiedad">
                        <a href="{url_export}" target="_blank">
                        <div class="imagen">
                          <img src="{imagen_principal}">
                        </div>
                        </a>
                        <div class="caracteristicas">
                          <h3>${inmueble['valorventa']:,.0f}</h3>
                          <p>{direccion}</p>
                          <p>{propertyinfo}</p>
                        </div>
                      </div>
                      '''
    
            #-------------------------------------------------------------------------#
            # OFERTA - ARRIENDO
            #-------------------------------------------------------------------------#
            arriendo_oferta   = ""
            arriendo_valormt2 = ""
            arriendo_imagenes = ""
            if datamarketarriendo.empty is False:
                
                arriendo_oferta = f"""
                <div class="col-xl-6 col-sm-6 mb-xl-0 mb-2">
                  <div class="card-body p-3">
                    <div class="row">
                      <div class="numbers">
                        <h3 class="font-weight-bolder mb-0" style="text-align: center; font-size: 1.5rem;">{len(datamarketarriendo)}</h3>
                        <p class="mb-0 text" style="font-weight: 300; font-size: 1rem; text-align: center;">Oferta de inmuebles</p>
                      </div>
                    </div>
                  </div>
                </div>
                """
                arriendo_valormt2 = f"""
                <div class="col-xl-6 col-sm-6 mb-xl-0 mb-2">
                  <div class="card-body p-3">
                    <div class="row">
                      <div class="numbers">
                        <h3 class="font-weight-bolder mb-0" style="text-align: center; font-size: 1.5rem;">${datamarketarriendo["valormt2"].median():,.0f}</h3>
                        <p class="mb-0 text" style="font-weight: 300; font-size: 1rem; text-align: center;">Valor por mt2</p>
                      </div>
                    </div>
                  </div>
                </div>
                """
                arriendo_imagenes = ''
                for i, inmueble in datamarketarriendo.iterrows():
                    if isinstance(inmueble['img1'], str) and len(inmueble['img1'])>20: imagen_principal =  inmueble['img1']
                    else: imagen_principal = "https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/sin_imagen.png"
                    
                    try:    garajes_inmueble = f' | <strong>{int(inmueble["garajes"])}</strong> pq'
                    except: garajes_inmueble = ""
                        
                    propertyinfo = f'<strong>{inmueble["areaconstruida"]}</strong> mt<sup>2</sup> | <strong>{int(inmueble["habitaciones"])}</strong> hab | <strong>{int(inmueble["banos"])}</strong> baños {garajes_inmueble}'
                    url_export   = f"{url}/Ficha?code={inmueble['code']}&tiponegocio=Arriendo&tipoinmueble=Apartamento" 
        
                    if isinstance(inmueble['direccion'], str): direccion = inmueble['direccion'][0:35]
                    else: direccion = '&nbsp'
                    arriendo_imagenes += f'''    
                      <div class="propiedad">
                        <a href="{url_export}" target="_blank">
                        <div class="imagen">
                          <img src="{imagen_principal}">
                        </div>
                        </a>
                        <div class="caracteristicas">
                          <h3>${inmueble['valorarriendo']:,.0f}</h3>
                          <p>{direccion}</p>
                          <p>{propertyinfo}</p>
                        </div>
                      </div>
                      '''
            if venta_oferta!= "" or venta_valormt2!= "" or venta_imagenes!= "" or arriendo_oferta!= "" or arriendo_valormt2!="" or arriendo_imagenes!= "":  
                style = """
                    <style>
                      .contenedor-propiedades {
                        overflow-x: scroll;
                        white-space: nowrap;
                        margin-bottom: 40px;
                        margin-top: 30px;
                      }
                      .propiedad {
                        display: inline-block;
                        vertical-align: top;
                        margin-right: 20px;
                        text-align: center;
                        width: 300px;
                      }
                      .imagen {
                        height: 200px;
                        margin-bottom: 10px;
                        overflow: hidden;
                      }
                      .imagen img {
                        display: block;
                        height: 100%;
                        width: 100%;
                        object-fit: cover;
                      }
                      .caracteristicas {
                        background-color: #f2f2f2;
                        padding: 4px;
                        text-align: left;
                      }
                      .caracteristicas h3 {
                        font-size: 18px;
                        margin-top: 0;
                      }
        
                    </style>
                """
            
                html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                  <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-icons.css" rel="stylesheet">
                  <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-svg.css" rel="stylesheet">
                  <link id="pagestyle" href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/soft-ui-dashboard.css?v=1.0.7" rel="stylesheet">
                  {style}
                </head>
                <body>
                  <div class="container-fluid py-4">
                    <div class="row">
                    
                      <div class="col-xl-6 col-sm-6 mb-xl-0 mb-2">
                        <div class="card">
                          <div class="card-body p-3">
                            <div class="container-fluid py-4">
                              <div class="row" style="margin-bottom: -10px;">
                                <div class="card-body p-3">
                                  <div class="row">
                                    <div class="numbers">
                                      <h3 class="font-weight-bolder mb-0" style="text-align: center; font-size: 1.5rem;border-bottom: 0.5px solid #ccc; padding-bottom: 8px;">Oferta de inmuebles en Venta</h3>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>                
                            <div class="container-fluid py-2" style="margin-bottom: -30px;">
                              <div class="row">
                                {venta_oferta}
                                {venta_valormt2}
                              </div>
                            </div>
                            <div class="container-fluid py-2">
                              <div class="row">
                                <div class="contenedor-propiedades">
                                    {venta_imagenes}
                                </div>                      
                              </div>
                            </div>                    
                          </div>
                        </div>
                      </div>
                      
        
                      <div class="col-xl-6 col-sm-6 mb-xl-0 mb-2">
                        <div class="card h-100">
                          <div class="card-body p-3">
                            <div class="container-fluid py-4">
                              <div class="row" style="margin-bottom: -10px;">
                                <div class="card-body p-3">
                                  <div class="row">
                                    <div class="numbers">
                                      <h3 class="font-weight-bolder mb-0" style="text-align: center; font-size: 1.5rem;border-bottom: 0.5px solid #ccc; padding-bottom: 8px;">Oferta de inmuebles en Arriendo</h3>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>                
                            <div class="container-fluid py-2" style="margin-bottom: -30px;">
                              <div class="row">
                                {arriendo_oferta}
                                {arriendo_valormt2}
                              </div>
                            </div>
                            <div class="container-fluid py-2">
                              <div class="row">
                                <div class="contenedor-propiedades">
                                    {arriendo_imagenes}
                                </div>                      
                              </div>
                            </div>                    
                          </div>
                        </div>
                      </div>
        
                      
                    </div>
                  </div>
                </body>
                </html>
                """     
                texto = BeautifulSoup(html, 'html.parser')
                st.markdown(texto, unsafe_allow_html=True)            
                
            #-------------------------------------------------------------------------#
            # TELEFONOS
            #-------------------------------------------------------------------------#
            dataphone    = pd.DataFrame()
            dataphonenew = pd.DataFrame()
            variables    = ['fecha_inicial','tiponegocio','tipo_cliente','telefono1','telefono2','telefono3']
            datamarketventa['tiponegocio']    = 'VENTA'
            datamarketarriendo['tiponegocio'] = 'ARRIENDO'
            for i in [datagaleria,datarecorrido,datamarketventa,datamarketarriendo]:
                if i.empty is False:
                    varnew = [w for w in variables if w in list(i)]
                    if varnew!=[]:
                        dataphone = pd.concat([dataphone,i[varnew]])
                        #dataphone = dataphone.append(i[varnew])
                        
            if dataphone.empty is False:
                dataphone['id'] = range(len(dataphone))
                dataphonemelt   = dataphone.melt(id_vars=['id','fecha_inicial', 'tiponegocio',],
                                  value_vars=['telefono1', 'telefono2', 'telefono3'],
                                  var_name='tipo_telefono', value_name='telefono')
                
                dataphonemelt = dataphonemelt[dataphonemelt['telefono'].notnull()]
                dataphonemelt = dataphonemelt.drop_duplicates(subset=['tiponegocio','telefono'])
            
                if dataphone.empty is False:
                    dataphonenew = dataphonemelt.pivot(index='id', columns='tipo_telefono', values='telefono').reset_index()
                    dataphonenew = dataphonenew.merge(dataphone[['fecha_inicial','tiponegocio','id']],on='id',how='left',validate='1:1')
            
            if 'id' in dataphonenew:
                del dataphonenew['id']
                
                
            datamarketexport = pd.concat([datamarketventa,datamarketarriendo])
            col1, col2, col3 = st.columns([1,1,2])
            
            if datamarketexport.empty is False:
                with col1:
                    csv = convert_df(datamarketexport)     
                    st.download_button(
                       "Descargar ofertas en venta y arriendo",
                       csv,
                       "info_ofertas.csv",
                       "text/csv",
                       key='info_ofertas'
                    )  
                        
            if dataphone.empty is False:
                with col2:
                    csv = convert_df(dataphone)     
                    st.download_button(
                       "Descargar teléfonos de ofertas",
                       csv,
                       "info_telefonos.csv",
                       "text/csv",
                       key='info_telefonos'
                    )  
            #-------------------------------------------------------------------------#
            # CARACTERIZACION
            #-------------------------------------------------------------------------#
            barrio_caracterizacion = ""
            if 'barrio' in dataconjunto:
                try: barrio_caracterizacion = dataconjunto['barrio'].iloc[0]
                except: pass
                
            if databarrio.empty is False or barriopricing.empty is False or barriocaracterizacion.empty is False or barriovalorizacion.empty is False:
                html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                  <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-icons.css" rel="stylesheet" />
                  <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-svg.css" rel="stylesheet" />
                  <link id="pagestyle" href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/soft-ui-dashboard.css?v=1.0.7" rel="stylesheet" />
                </head>
                <body>
                <div class="container-fluid py-1" style="margin-bottom: 50px;">
                  <div class="row">
                    <div class="col-xl-12 col-sm-6 mb-xl-0 mb-2">
                      <div class="card">
                        <div class="card-body p-3">
                          <div class="row">
                            <div class="numbers">
                              <h3 class="font-weight-bolder mb-0" style="text-align: center;font-size: 1.5rem;">Cifras de mercado</h3>
                              <p class="mb-0 text-capitalize" style="font-weight: 300;font-size: 1rem;text-align: center;">{barrio_caracterizacion}</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                </body>
                </html>        
                """
                texto = BeautifulSoup(html, 'html.parser')
                st.markdown(texto, unsafe_allow_html=True)
                    
                col1, col2 = st.columns([1,2])
                with col1:
                    market_tiponegocio = st.selectbox('Tipo de negocio',options=['Venta','Arriendo'])
                
            barriopricingmt2 = ""
            barriopricingobs = ""
            valorizacion     = ""
            try:
                iddb = (barriopricing['tiponegocio']==market_tiponegocio) & (barriopricing['tipo']=='barrio')
                barriopricingmt2 = f"${barriopricing[iddb]['valormt2'].iloc[0]:,.0f}"
            except: pass
            try:
                iddb = (barriopricing['tiponegocio']==market_tiponegocio) & (barriopricing['tipo']=='barrio')
                barriopricingobs = f"${barriopricing[iddb]['obs'].iloc[0]:,.0f}"
            except: pass
            try:
                iddv = (barriovalorizacion['tiponegocio']==market_tiponegocio) & (barriovalorizacion['tipo']=='barrio')
                valorizacion = "{:.1%}".format(barriovalorizacion[iddv]['valorizacion'].iloc[0])
            except: pass
        
            if barriopricingmt2!="" or barriopricingobs!="" or valorizacion!="":
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
                  <div class="row">
                    <div class="col-xl-12 col-sm-6 mb-xl-4 mb-2">
                      <div class="card">
                        <div class="card-body p-4">
                          <div class="row">
                            <div class="numbers">
                              <h3 class="font-weight-bolder mb-0" style="text-align: center;font-size: 1.5rem;">{barriopricingmt2}</h3>
                              <p class="mb-0 text" style="font-weight: 300;font-size: 1rem;text-align: center;">Valor por mt2</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="container-fluid py-1">
                  <div class="row">        
                    <div class="col-xl-12 col-sm-6 mb-xl-4 mb-2">
                      <div class="card">
                        <div class="card-body p-4">
                          <div class="row">
                            <div class="numbers">
                              <h3 class="font-weight-bolder mb-0" style="text-align: center;font-size: 1.5rem;">{barriopricingobs}</h3>
                              <p class="mb-0 text" style="font-weight: 300;font-size: 1rem;text-align: center;"># de inmuebles</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="container-fluid py-1">
                  <div class="row">        
                    <div class="col-xl-12 col-sm-6 mb-xl-4 mb-2">
                      <div class="card">
                        <div class="card-body p-4">
                          <div class="row">
                            <div class="numbers">
                              <h3 class="font-weight-bolder mb-0" style="text-align: center;font-size: 1.5rem;">{valorizacion}</h3>
                              <p class="mb-0 text" style="font-weight: 300;font-size: 1rem;text-align: center;">Valorizacion</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>    
            
                </body>
                </html>        
                """
        
                with col1:
                    texto = BeautifulSoup(html, 'html.parser')
                    st.markdown(texto, unsafe_allow_html=True)
                
            conteo = 0
            parametros = [{'variable': 'areaconstruida', 'label': 'Área construida', 'color': 'rgba(75, 192, 192, 0.4)'},
                          {'variable': 'habitaciones', 'label': 'Habitaciones', 'color': 'rgba(255, 99, 132, 0.4)'},
                          {'variable': 'banos', 'label': 'Baños', 'color': 'rgba(54, 162, 235, 0.4)'},
                          {'variable': 'garajes', 'label': 'Garajes', 'color': 'rgba(255, 206, 86, 0.4)'}]
            
            graph = ""
            html_chart = ""
            if barriocaracterizacion.empty is False:
                for i in parametros:
                    conteo += 1
                    df = barriocaracterizacion[(barriocaracterizacion['tiponegocio'] == market_tiponegocio) &
                                               (barriocaracterizacion['tipo'] == i['variable']) &
                                               (barriocaracterizacion['valor'] > 0)]
                    df['porcentaje'] = df['valor'] / df['valor'].sum() * 100
                    try:  df['variable'] = df['variable'].astype(float).astype(int).astype(str)
                    except: pass
                    
                    html_chart += f"""
                    <div class="chart">
                        <canvas id="chart{conteo}"></canvas>
                    </div>            
                    """
                    graph += f'''
                    const labels{conteo} = {df['variable'].to_list()};
                    const data{conteo} = {df['porcentaje'].to_list()};
                    const ctx{conteo} = document.getElementById('chart{conteo}').getContext('2d');
                
                    new Chart(ctx{conteo}, {{
                        type: 'bar',
                        data: {{
                            labels: labels{conteo},
                            datasets: [{{
                                label: '{i['label']}',
                                data: data{conteo},
                                backgroundColor: '{i['color']}',
                                borderWidth: 0
                            }}]
                        }},
                        options: {{
                            scales: {{
                                x: {{
                                    grid: {{
                                        display: false
                                    }}
                                }},
                                y: {{
                                    beginAtZero: true,
                                    ticks: {{
                                        callback: function(value) {{
                                            return value + '%';
                                        }}
                                    }}
                                }}
                            }},
                            plugins: {{
                                tooltip: {{
                                    callbacks: {{
                                        label: function(context) {{
                                            return context.parsed.y + '%';
                                        }}
                                    }}
                                }}
                            }}
                        }}
                    }});
                    '''
                graph = BeautifulSoup(graph, 'html.parser')
                
                style = """
                <style>
                    body {
                        font-family: Arial, sans-serif;
                    }
                    
                    .chart-container {
                        display: grid;
                        grid-template-columns: 1fr 1fr;
                        grid-template-rows: 1fr 1fr;
                        gap: 20px;
                        margin: 0 auto;
                        padding: 20px;
                        overflow: auto; 
                    }
                    
                    canvas {
                        max-width: 100%;
                        max-height: 100%;
                        max-height: 300px;
                    }
                </style>        
                """
                html = f"""
                <!DOCTYPE html>
                <html lang="es">
                <head>
                    <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-icons.css" rel="stylesheet" />
                    <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-svg.css" rel="stylesheet" />
                    <link id="pagestyle" href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/soft-ui-dashboard.css?v=1.0.7" rel="stylesheet" />
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    {style}
                </head>
                <body>
                <div class="container-fluid py-1">
                  <div class="row">
                    <div class="col-xl-12 col-sm-12 mb-xl-0 mb-2">
                      <div class="card">
                        <div class="card-body p-3">
                          <div class="row">
                            <div class="numbers">
                                    
                                <div class="chart-container">   
                                    {html_chart}
                                </div>
                            
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
                    <script>
                    {graph}
                    </script>
                </body>
                </html>
                """
                with col2:
                    st.components.v1.html(html, height=1000)

        else:
            st.error('Edificio o conjunto no encontrando')

        # Javascript    
        html = """
        <!DOCTYPE html>
        <html lang="es">
        <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Lista Desplegable</title>
        </head>
        <body>
        <h1>Lista Desplegable</h1>
        <p>Selecciona una alternativa:</p>
        <select id="opciones">
          <option value="opcion1">Opción 1</option>
          <option value="opcion2">Opción 2</option>
          <option value="opcion3">Opción 3</option>
        </select>
        <p id="resultado"></p>
        <script>
          const select = document.getElementById("opciones");
          const resultado = document.getElementById("resultado");
        
          select.addEventListener("change", () => {
            const seleccion = select.value;
            resultado.textContent = "Has seleccionado: " + seleccion;
          });
        </script>
        </body>
        </html>
        """
        
        #st.title("Lista Desplegable HTML en Streamlit")
        #resultado = st.components.v1.html(html, height=300)
    