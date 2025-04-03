from flask import Flask, render_template, request, jsonify
import requests
from pymongo import MongoClient
from datetime import datetime  # Asegurar que datetime está importado

app = Flask(__name__)
API_KEY = "49617833-17b6310e26005e88c7f20f06f"
PIXABAY_URL = "https://pixabay.com/api/"

# Conectar a MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["Pixabay"]
collection = db["pix"]

@app.route('/', methods=['GET', 'POST'])
def index():
    query = request.args.get('query', '')
    order = request.args.get('order', 'popular')
    page = int(request.args.get('page', 1))
    images = []
    total_pages = 1
    
    if query:
        response = requests.get(PIXABAY_URL, params={
            "key": API_KEY,
            "q": query,
            "image_type": "photo",
            "page": page,
            "per_page": 30,
            "lang": "es",
            "order": order
        })
        data = response.json()
        images = data.get("hits", [])
        total = data.get("totalHits", 0)
        total_pages = (total // 30) + (1 if total % 30 > 0 else 0)

# POBREZA
    if "pobreza" in query.lower():
        images = [image for image in images if not any(tag in image.get("tags", "").lower() for tag in ["niño", "niña", "infante", "bebé", "child", "kid", "baby"])]


    
    page = min(page, total_pages)
    
# Asegura que la pagina actual no supere el total de paginas
    page = min(page, total_pages)

    # Lógica de paginación
    page_range = 2  # Cantidad de paginas atras y adelabo de la pagina actual
    pagination = []

    # Página inicial
    pagination.append(1)

    # Páginas antes y después de la página actual
    for i in range(page - page_range, page + page_range + 1):
        if i > 1 and i < total_pages:
            pagination.append(i)

    # Páginas finales
    if total_pages > 1:
        pagination.append(total_pages)

    # Eliminar duplicados y ordenar
    pagination = sorted(set(pagination))

    # Agregar los puntos suspensivos si es necesario
    if len(pagination) > 1 and pagination[1] > 2:
        pagination.insert(1, '...')
    if len(pagination) > 2 and pagination[-2] < total_pages - 1:
        pagination.insert(-1, '...')

    # Si no hay imágenes, no mostrar la paginación
    show_pagination = len(images) > 0 or query == '' 

    return render_template('index.html', images=images, query=query, order=order, page=page, total_pages=total_pages, pagination=pagination, show_pagination=show_pagination)

@app.route('/guardar', methods=['POST'])
def guardar():
    try:
        data = request.get_json()
        print(f"📩 Datos recibidos: {data}")  # Verifica los datos en la consola

        if not data or "selected_images" not in data or "query" not in data:
            print("⚠️ Faltan datos en la solicitud")
            return jsonify({"error": "No se seleccionaron imágenes o falta la consulta"}), 400

        query = data["query"]  # La consulta usada para buscar
        selected_images = data["selected_images"]

        for img in selected_images:
            image_data = {
                "url": img["url"],  # Ahora tomamos 'url' correctamente
                "query": query,
                "fecha_guardado": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            collection.insert_one(image_data)
            print(f"✅ Imagen guardada en MongoDB: {image_data}")

        return jsonify({"message": "Imágenes guardadas correctamente", "images": selected_images})

    except Exception as e:
        print(f"❌ Error al procesar la solicitud: {e}")
        return jsonify({"error": "Error en el servidor"}), 500

if __name__ == '__main__':
    app.run(debug=True)