import pandas as pd

# ========================
# 🔥 FUNCIÓN LIMPIADORA PRO (REEMPLAZA LA ANTERIOR)
# ========================

def limpiar_csv(ruta, columnas):
    df = pd.read_csv(ruta, header=None)

    # Convertir todo a string
    df = df.astype(str)

    # Unir todo (por si viene separado raro)
    df = df.apply(lambda x: ",".join(x), axis=1)

    # Limpiar comillas
    df = df.str.replace('"', '')

    # Separar columnas
    df = df.str.split(",", expand=True)

    # Debug
    print(f"\n📂 {ruta} → columnas detectadas:", df.shape[1])

    # Ajustar columnas si hay error
    if df.shape[1] != len(columnas):
        print("⚠️ Ajustando columnas automáticamente...")
        df = df.iloc[:, :len(columnas)]

    df.columns = columnas

    # ❌ Eliminar cualquier fila que tenga nombres de columnas
    for col in columnas:
        df = df[df[col] != col]

    # Limpiar ; basura
    df = df.replace(";", "", regex=True)

    # Limpiar espacios
    df = df.apply(lambda x: x.str.strip())

    return df



# ========================
# 1. CARGAR DATOS (LIMPIOS)
# ========================

VENTA = limpiar_csv("CVS/VENTA.csv",
                   ["pedido_id", "fecha", "sku", "cantidad", "unit_price"])

INVENTARIO = limpiar_csv("CVS/INVENTARIO.csv",
                         ["sku", "producto", "talla", "color", "marca", "stock", "lead_time"])

COSTOS = limpiar_csv("CVS/COSTOS.csv",
                     ["sku", "costo_producto", "costo_envio", "costo_empaque", "precio_venta"])


# ========================
# 2. VALIDACIÓN DE DATOS
# ========================

print("\n🧪 PRIMERAS FILAS VENTAS:")
print(VENTA.head())

# ========================
# 2. TIPOS DE DATOS
# ========================

VENTA["cantidad"] = VENTA["cantidad"].astype(int)
VENTA["unit_price"] = VENTA["unit_price"].astype(float)

INVENTARIO["stock"] = INVENTARIO["stock"].astype(int)
INVENTARIO["lead_time"] = INVENTARIO["lead_time"].astype(int)

COSTOS["costo_producto"] = COSTOS["costo_producto"].astype(float)
COSTOS["costo_envio"] = COSTOS["costo_envio"].astype(float)
COSTOS["costo_empaque"] = COSTOS["costo_empaque"].astype(float)


# ========================
# 2. VALIDACIÓN DE DATOS
# ========================

print("\n📊 COLUMNAS VENTAS:", VENTA.columns)
print("📦 COLUMNAS INVENTARIO:", INVENTARIO.columns)
print("💸 COLUMNAS COSTOS:", COSTOS.columns)

# Eliminar nulos en ventas
VENTA = VENTA.dropna()

# ========================
# 3. MÉTRICAS
# ========================

VENTA["revenue"] = VENTA["cantidad"] * VENTA["unit_price"]

# ========================
# 4. AGRUPAR
# ========================

ventas_producto = VENTA.groupby("sku").agg({
    "cantidad": "sum",
    "revenue": "sum"
}).reset_index()

ventas_producto.rename(columns={
    "cantidad": "total_vendido"
}, inplace=True)

# ========================
# 5. JOIN
# ========================

df = ventas_producto.merge(INVENTARIO, on="sku", how="left")
df = df.merge(COSTOS, on="sku", how="left")

# Rellenar nulos después del join
df = df.fillna(0)

# ========================
# 6. CÁLCULOS
# ========================

# Evitar división por cero
df["ratio"] = df.apply(
    lambda x: x["total_vendido"] / x["stock"] if x["stock"] > 0 else 0,
    axis=1
)

# Costo unitario total
df["costo_unitario"] = (
    df["costo_producto"] +
    df["costo_envio"] +
    df["costo_empaque"]
)

# Ganancia total
df["ganancia"] = df["revenue"] - (df["costo_unitario"] * df["total_vendido"])

# ========================
# 7. LÓGICA DE NEGOCIO (STOCK)
# ========================

# Suposición: ventas en 30 días
df["demanda_diaria"] = df["total_vendido"] / 30

# Stock de seguridad
df["stock_seguridad"] = df["demanda_diaria"] * df["lead_time"]

# Alerta de stock
df["alerta_stock"] = df["stock"] < df["stock_seguridad"]

# ========================
# 8. ORDENAR Y KPI
# ========================

df = df.sort_values(by="ganancia", ascending=False)

print("\n💰 GANANCIA TOTAL:", df["ganancia"].sum())
print("📦 PRODUCTOS CON ALERTA:", df["alerta_stock"].sum())

print("\n🔥 TOP 10 PRODUCTOS MÁS RENTABLES")
print(df.head(10))

# ========================
# 9. EXPORTAR
# ========================

df.to_csv("reporte_general.csv", index=False)
print("📁 Archivo guardado en Tienda Ropa")

import os
from datetime import datetime
import matplotlib.pyplot as plt

# Crear carpeta
os.makedirs("graficos", exist_ok=True)

# Asegurar que producto sea texto
df["producto"] = df["producto"].astype(str)
df["producto"] = df["producto"].replace("0", "SIN NOMBRE")

fecha = datetime.now().strftime("%Y-%m-%d")

top = df.head(10)

# ========================
# 🔥 GRÁFICO 1: TOP PRODUCTOS
# ========================
plt.figure()
plt.bar(top["producto"], top["ganancia"])
plt.xticks(rotation=45)
plt.title("Top 10 productos más rentables")
plt.tight_layout()
plt.savefig(f"graficos/top_productos_{fecha}.png")
plt.close()

# ========================
# 🔥 GRÁFICO 2: VENTAS VS STOCK
# ========================
plt.figure()
plt.scatter(df["stock"], df["total_vendido"])
plt.xlabel("Stock")
plt.ylabel("Ventas")
plt.title("Ventas vs Stock")
plt.savefig(f"graficos/ventas_stock_{fecha}.png")
plt.close()

# ========================
# 🔥 GRÁFICO 3: RENTABILIDAD
# ========================
plt.figure()
plt.bar(top["producto"], top["ganancia"])
plt.xticks(rotation=45)
plt.title("Rentabilidad por producto")
plt.tight_layout()
plt.savefig(f"graficos/rentabilidad_{fecha}.png")
plt.close()