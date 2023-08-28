import streamlit as st

from _listings import main
from scripts.validate_token import validate_token

st.set_page_config(layout="wide",initial_sidebar_state="collapsed")


html = """
<!DOCTYPE html>
<html>
<head>
  <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-icons.css" rel="stylesheet">
  <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-svg.css" rel="stylesheet">
  <link id="pagestyle" href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/soft-ui-dashboard.css?v=1.0.7" rel="stylesheet">
</head>
</html>
"""     
st.markdown(html, unsafe_allow_html=True)

# streamlit run D:\Dropbox\Empresa\Buydepa\PROYECTOS\proceso\appcolombia\Home.py
# https://streamlit.io/
# pipreqs --encoding utf-8 "D:\Dropbox\Empresa\Buydepa\PROYECTOS\proceso\appcolombia"
# st.secrets -> C:\Users\LENOVO T14.streamlit\secrets.toml
# st.write(str(st.__path__))
# st.write(str(st.secrets._file_path))
# st.write(str(st.secrets.get))

args = st.experimental_get_query_params()

if 'access' not in st.session_state: 
    st.session_state.access = False

if 'token' not in st.session_state: 
    st.session_state.token = ''
    
if st.session_state.token=='':
    if 'token' in args: 
        st.session_state.token = args['token'][0]
        st.experimental_rerun()

if st.session_state.token!='':
    validate_token(st.session_state.token)
    
if st.session_state.access or validate_token(st.session_state.token):
    main()
    
else:
    st.error("Inicia sesión o registrate")