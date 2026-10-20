import pandas as pd

# Leer tu parquet actual
df = pd.read_parquet("resumen_ifc_consolidado.parquet")
print(f"Filas originales: {len(df):,}")

# Si quieres conservar solo una muestra representativa o filtrar los modelos principales para aligerar:
# (Por ejemplo, filtramos solo los elementos que tengan al menos un parámetro informado o una muestra de filas)
df_ligero = df.head(50000) # Opcional: limita a 50,000 filas clave para que entre holgado en la RAM gratuita

# Guardar versión ultraligera
df_ligero.to_parquet("resumen_ifc_consolidado.parquet", compression="snappy")
print("¡Parquet optimizado y aligerado con éxito!")