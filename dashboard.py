import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
from sqlalchemy import create_engine, text
import os

# Obtener la URL de la base de datos desde las variables de entorno
DATABASE_URL = os.getenv('DATABASE_URL')

# Crear un motor SQLAlchemy
engine = create_engine(DATABASE_URL)

# 📌 Contar los registros en la base de datos para limitar paginación
def get_total_records():
    query = """
    SELECT COUNT(*) FROM biogrid_homosapiens 
    INNER JOIN rcsb_pdb 
    ON LOWER(TRIM(biogrid_homosapiens.official_symbol)) = LOWER(TRIM(rcsb_pdb.macromolecule_name));
    """
    conn = engine.connect()
    try:
        result = conn.execute(text(query)).fetchone()
        total = result[0] if result else 0
        print(f"🔹 Total registros disponibles en el JOIN: {total}")
        return total
    except Exception as e:
        print(f"🚨 Error al contar registros: {e}")
        return 0
    finally:
        conn.close()

TOTAL_RECORDS = get_total_records()
if TOTAL_RECORDS == 0:
    print("🚨 ERROR: El JOIN no encontró coincidencias.")

# 📌 Función para obtener un solo registro con paginación
def fetch_record(offset):
    query = f"""
    SELECT * FROM biogrid_homosapiens 
    INNER JOIN rcsb_pdb 
    ON LOWER(TRIM(biogrid_homosapiens.official_symbol)) = LOWER(TRIM(rcsb_pdb.macromolecule_name))
    LIMIT 1 OFFSET {offset};
    """
    conn = engine.connect()
    try:
        df = pd.read_sql_query(text(query), conn)
        print(f"✅ Datos recuperados en OFFSET {offset}:")
        print(df.head())  # Debug para verificar si hay datos
        return df
    except Exception as e:
        print(f"🚨 Error al obtener registro en OFFSET {offset}: {e}")
        return pd.DataFrame()
    finally:
        conn.close()



