import streamlit as st
import pandas as pd
import hashlib
import time
from datetime import datetime
from sqlalchemy import create_engine

if 'layout' not in st.session_state: 
    st.session_state.layout = "centered"
   
st.set_page_config(layout=st.session_state.layout)

url = "https://buydepa-colombia.streamlit.app/"


#st.set_page_config(layout="wide",initial_sidebar_state="collapsed")


# streamlit run D:\Dropbox\Empresa\Buydepa\PROYECTOS\APPCOLOMBIA\app.py
# https://streamlit.io/
# pipreqs --encoding utf-8 "D:\Dropbox\Empresa\Buydepa\PROYECTOS\APPCOLOMBIA"

#-----------------------------------------------------------------------------#
# El secrets esta en formato .toml en la siguiente carpeta:
# st.secrets -> C:\Users\LENOVO T14.streamlit\secrets.toml
#-----------------------------------------------------------------------------#

#st.write(str(st.__path__))
#st.write(str(st.secrets._file_path))
#st.write(str(st.secrets.get))

user     = st.secrets["user_appraisal"]
password = st.secrets["password_appraisal"]
host     = st.secrets["host_appraisal"]
schema   = st.secrets["schema_appraisal"]

def encriptar_contrasena(contrasena_plana):
    token = hashlib.md5()
    token.update(contrasena_plana.encode('utf-8'))
    contrasena_plana = token.hexdigest()
    return contrasena_plana

def verificar_contrasena(email, contrasena):
    engine = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')
    df     =  pd.read_sql_query(f"""SELECT password  FROM {schema}.users WHERE email='{email}';""" , engine)
    engine.dispose()
    if df.empty:
        return False
    contrasenastock = df['password'].iloc[0]
    contrasenanew   = encriptar_contrasena(contrasena)
    if contrasenanew==contrasenastock:
        return True
    else:
        return False

def user_register(data):
    engine   = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')
    df       =  pd.read_sql_query(f"""SELECT * FROM {schema}.users WHERE email='{email}';""" , engine)
    if df.empty:
        try:
            data.to_sql('users', engine, if_exists='append', index=False, chunksize=1)
            response = 'Usuario registrado exitosamente'
            success  = True
        except:
            response = 'Por favor volver a registrarse'
            success  = False
    else:
        response = 'Usuario ya está registrado'
        success  = False
    engine.dispose()
    return response,success
        
def datos_usuario(email):
    engine = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')
    df     =  pd.read_sql_query(f"""SELECT email,nombre,telefono,logo,token  FROM {schema}.users WHERE email='{email}';""" , engine)
    engine.dispose()
    if df.empty is False:
        for i in ['email','nombre','telefono','logo','token']:
            st.session_state[i] = df[i].iloc[0]
            
def button_login():
    st.session_state.login  = True
    st.session_state.signin = False

def button_signin():
    st.session_state.login  = False
    st.session_state.signin = True
    
formato = {
            'login':True,
            'signin':False,
            'access':False,
            'token':''
           }

for key,value in formato.items():
    if key not in st.session_state: 
        st.session_state[key] = value
        
if st.session_state.access is False:
    col1, col2 = st.columns([5,1])
    if st.session_state.login:
        with col2:
            st.button('Sign in',on_click=button_signin)
            
    if st.session_state.signin:
        with col2:
            st.button('Log in ',on_click=button_login)
    
if st.session_state.login:
    placeholder = st.empty()
    with placeholder.form("login form"):
        st.markdown("#### Log in")
        email      = st.text_input("Email")
        contrasena = st.text_input("Password", type="password")
        submit     = st.form_submit_button("Login")
    
    if submit:
        with st.spinner('loading'):
            if verificar_contrasena(email, contrasena):
                datos_usuario(email)
                st.session_state.access = True
                st.session_state.login  = False
                st.session_state.signin = False
                st.session_state.layout = "wide"
                st.experimental_rerun()
            else:
                st.error("Error en la contraseña o email")

    
if st.session_state.signin:
    placeholder = st.empty()
    with placeholder.form("signin form"):
        st.markdown("#### Registro")
        email    = st.text_input("Email").strip()
        contrasena = st.text_input("Password", type="password").strip()
        contrasena = encriptar_contrasena(contrasena)
        nombre   = st.text_input("Nombre Completo").strip().title()
        telefono = st.text_input("Celular",max_chars =10).strip()
        
        token = hashlib.md5()
        token.update(email.encode('utf-8'))
        token = token.hexdigest()
        
        submit = st.form_submit_button("Registrarse")
        if submit:
            registro         = pd.DataFrame([{'email':email,'nombre':nombre,'telefono':telefono,'password':contrasena,'token':token,'fecha':datetime.now().strftime('%Y-%m-%d')}])
            response,success = user_register(registro)
            if success:
                placeholder = st.empty()
                with st.spinner('Proceso'):
                    st.success(response)
                    time.sleep(2)
                    st.session_state.login  = True
                    st.session_state.signin = False
                    st.session_state.layout = "wide"
                    st.experimental_rerun()
            else:
                st.error(response)

                
if st.session_state.access:
    style = """
    <style>
      .grid-container {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 20px;
        justify-content: center;
      }
    
      .grid-item {
        text-align: center;
        margin-right: 20px;
      }
    </style>    
    """
    html = f"""
    {style}
    <div class="grid-container">
      <div class="grid-item">
        <a href="{url}/Buscador_de_inmuebles?token={st.session_state.token}">
          <img src="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/buydepa/listings_map.png" width="400" height="300">
        </a>
        <p>Buscador de inmuebles</p>
      </div>
      <div class="grid-item">
        <a href="{url}/Analisis_del_edificio?token={st.session_state.token}">
          <img src="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/buydepa/building_pic.png" width="400" height="300">
        </a>
        <p>Análisis por Edificio</p>
      </div>
      <div class="grid-item">
        <a href="{url}/Analisis_de_precio?token={st.session_state.token}">
          <img src="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/buydepa/ficha_pic.png" width="400" height="300">
        </a>
        <p>Análisis del inmueble</p>
      </div>
      <div class="grid-item">
        <a href="{url}/Ficha_del_inmueble">
          <img src="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/buydepa/ficha_pic.png" width="400" height="300">
        </a>
        <p>Ficha del inmueble</p>
      </div>
    </div>    
    """
    st.markdown(html, unsafe_allow_html=True)