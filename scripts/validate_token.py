import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

user     = st.secrets["user_appraisal"]
password = st.secrets["password_appraisal"]
host     = st.secrets["host_appraisal"]
schema   = st.secrets["schema_appraisal"]

@st.cache(allow_output_mutation=True)
def validate_token(token):
    if token=='':
        return False
    else:
        engine   = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')
        df       =  pd.read_sql_query(f"""SELECT * FROM {schema}.users WHERE token='{token}';""" , engine)
        engine.dispose()
        if df.empty:
            return False
        else:
            st.session_state.access = True
            for i in ['email','nombre','telefono','logo','token']:
                st.session_state[i] = df[i].iloc[0] 
            return True