import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import io
import time

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title='Radar B2B', page_icon='🤖', layout='centered')

st.title("Radar de Competencia B2B")
st.write("Esta herramienta despliega un bot invisible para extraer el catálogo y los precios de la competencia en tiempo real.")

# --- 2. EL MOTOR DEL BOT (Funciones) ---
def ejecutar_scarper(paginas_maximas=2):
    titulos = []
    precios = []
    
    opciones = Options()
    opciones.add_argument("--headless")
    opciones.add_argument("--disable-gpu")
    opciones.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=opciones)
    
    try:
        driver.get('https://books.toscrape.com/')
        paginas_leidas = 0
        
        while paginas_leidas < paginas_maximas:
            articulos = driver.find_elements(By.CLASS_NAME, 'product_pod')
            
            for articulo in articulos:
                try:
                    titulo = articulo.find_element(By.CSS_SELECTOR, 'h3 > a').get_attribute('title')
                    precio = articulo.find_element(By.CLASS_NAME, 'price_color').text
                    titulos.append(titulo)
                    precios.append(precio)

                except Exception as e:
                    titulos.append(None)
                    precios.append(None)
                    print(f"Error al leer un artículo: {e}")
            
            try:
                boton_siguiente = driver.find_element(By.CSS_SELECTOR, 'li.next > a')
                boton_siguiente.click()
                time.sleep(1)
                paginas_leidas += 1

            except:
                break
                
    finally:
        driver.quit()
        
    return pd.DataFrame({'Nombre del Producto': titulos, 'Precio Competencia': precios})

# --- 3. LA INTERFAZ DE USUARIO (Front-End) ---
num_paginas = st.slider('¿Cuántas páginas quieres rastrear?', min_value=1, max_value=5, value=2)

if st.button('Iniciar Rastreo Automático', type='primary'):
    with st.spinner(f'Rastreando {num_paginas} páginas. Por favor, espera...'):
        df_resultado = ejecutar_scarper(paginas_maximas=num_paginas)

        st.success('Datos extraídos con éxito')

        st.dataframe(df_resultado, width='stretch')

        buffer = io.BytesIO()

        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_resultado.to_excel(writer, index=False, sheet_name='Scraping', header=False, startrow=1)

            workbook = writer.book
            worksheet = writer.sheets['Scraping']
            
            estilo_encabezado = workbook.add_format({
                'bold': True, 'font_color': 'white', 'bg_color': '#0F4C81', 
                'border': 1, 'align': 'center'
            })
            estilo_datos = workbook.add_format({
                'align': 'center', 'valign': 'vcenter', 'text_wrap': True
            })
            
            for col_num, nombre_columna in enumerate(df_resultado.columns):
                worksheet.write(0, col_num, nombre_columna, estilo_encabezado)
                longitud_maxima = max(df_resultado[nombre_columna].astype('str').map(len).max(), len(nombre_columna)) + 2
                anchura_final = min(longitud_maxima, 50)
                worksheet.set_column(col_num, col_num, anchura_final, estilo_datos)
            
        st.download_button(
            label='Descargar Informe',
            data=buffer.getvalue(),
            file_name='Reporte_Precios.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )