# Flight Report → Structured Extractor (Streamlit)

Sube una imagen del **Flight Departure Report** y extrae automáticamente los campos al formato requerido. Soporta **OpenAI**, **Gemini** o un **OCR local** (experimental).

## ⚠️ Supuestos importantes (léelos)
- No se infieren datos faltantes: si el campo no aparece o es ilegible → **'----'**.
- Los modelos multimodales suelen leer manuscrita con errores si la imagen es borrosa. Sube fotos con buena luz y contraste.
- Si necesitas cumplimiento/privacidad estricta, considera el OCR local o un proveedor con región y retención controladas.

## ▶️ Cómo ejecutar
```bash
python -m venv .venv && source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
# opcional: exporta variables de entorno
export OPENAI_API_KEY="sk-..."
export GEMINI_API_KEY="..."

streamlit run streamlit_app.py
```

Las llaves también se pueden introducir en la UI.

## 📤 Salidas
- **Pantalla**: bloque en el formato solicitado + JSON
- **Descargas**: `resultado.json` y `resultado.txt`

## 🧠 Prompting
El sistema instruye a la LLM a devolver **estrictamente JSON** con las claves en español y a usar `'----'` en faltantes. Las horas deben estar en formato `HH:MM` 24h. 

## 🔧 Estructura esperada
```json
{
  "Datos Básicos": { "Fecha de vuelo": "", "Origen": "", "Destino": "", "Número de vuelo": "" },
  "Tiempos": { "STD": "", "ATD": "", "Salida de Tripulacion": "", "Cantidad de Agentes Groomers": "", "Groomers In": "", "Groomers Out": "", "Crew at Gate": "", "OK to Board": "", "Flight Secure": "", "Cierre de Puerta": "", "Push Back": "" },
  "Información de Customs": { "Customs In": "", "Customs Out": "" },
  "Información de Pasajeros": { "Total Pax": "", "PAX C": "", "PAX Y": "", "Infantes": "" },
  "Información por Demoras": { "Delay": "", "Delay Code": "" },
  "Silla de ruedas": { "Sillas Vuelo Llegada (AV626)": "", "Agentes Vuelo Llegada (AV626)": "", "Sillas Vuelo Salida (AV627)": "", "Agentes Vuelo Salida (AV627)": "" },
  "Información de Gate y Carrusel": { "Gate": "", "Carrousel": "" },
  "Información de Gate Bag": { "Gate Bag": "" },
  "Comentarios": { "Comentarios": "" }
}
```

## 🧪 Pruebas rápidas
- Carga la imagen de ejemplo de tu operación y verifica que los campos ausentes salgan como `'----'`.
- Si el modelo devuelve texto fuera de JSON, el parser intenta recuperar el primer objeto `{...}` válido.

## 🔒 Privacidad
- OpenAI/Gemini: revisa sus políticas y configura control de retención si aplica.
- OCR local: no sale de tu máquina, pero la precisión es inferior.

---
Contribuciones: ajusta regex del OCR local o añade validaciones/pydantic si quieres más control.
