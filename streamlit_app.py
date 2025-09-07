def build_wpp_report(data: dict) -> str:
    # Construye el reporte en formato texto para WhatsApp, con los * y datos en la misma línea
    lines = []
    # Datos Básicos
    lines.append("🚀 *Datos Básicos*:")
    for k in EXPECTED_KEYS["Datos Básicos"].keys():
        lines.append(f"*{k}:* {data['Datos Básicos'][k]}")
    lines.append("")  # Línea en blanco entre secciones
    
    # Tiempos
    lines.append("⏰ *Tiempos:*")
    for k in EXPECTED_KEYS["Tiempos"].keys():
        lines.append(f"*{k}:* {data['Tiempos'][k]}")
    lines.append("")
    
    # Customs
    lines.append("📋 *Información de Customs:*")
    for k in EXPECTED_KEYS["Información de Customs"].keys():
        lines.append(f"*{k}:* {data['Información de Customs'][k]}")
    lines.append("")
    
    # Pasajeros
    lines.append("👥 *Información de Pasajeros:*")
    for k in EXPECTED_KEYS["Información de Pasajeros"].keys():
        lines.append(f"*{k}:* {data['Información de Pasajeros'][k]}")
    lines.append("")
    
    # Demoras
    lines.append("⏳ *Información por Demoras:*")
    for k in EXPECTED_KEYS["Información por Demoras"].keys():
        lines.append(f"*{k}:* {data['Información por Demoras'][k]}")
    lines.append("")
    
    # Silla de ruedas
    lines.append("♿ *Silla de ruedas:*")
    for k in EXPECTED_KEYS['Silla de ruedas'].keys():
        lines.append(f"*{k}:* {data['Silla de ruedas'][k]}")
    lines.append("")
    
    # Gate y Carrusel
    lines.append("📍 *Información de Gate y Carrusel:*")
    for k in EXPECTED_KEYS['Información de Gate y Carrusel'].keys():
        lines.append(f"*{k}:* {data['Información de Gate y Carrusel'][k]}")
    lines.append("")
    
    # Gate Bag
    lines.append("🧳 *Información de Gate Bag:*")
    lines.append(f"*Gate Bag:* {data['Información de Gate Bag']['Gate Bag']}")
    lines.append("")
    
    # Comentarios
    lines.append("💬 *Comentarios:*")
    lines.append(data['Comentarios']['Comentarios'])
    
    return "\n".join(lines)
#!/usr/bin/env python3

import os
import io
import re
import json

import traceback
from typing import Dict, Any
import sys

import streamlit as st



# Solo Gemini
try:
    import google.generativeai as genai
except Exception:
    genai = None



APP_TITLE = "Flight Report → Structured Extractor"


DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"

EXPECTED_KEYS = {
    "Datos Básicos": {
        "Fecha de vuelo": "----",
        "Origen": "----",
        "Destino": "----",
        "Número de vuelo": "----"
    },
    "Tiempos": {
        "STD": "----",
        "ATD": "----",
        "Salida de Tripulacion": "----",
        "Cantidad de Agentes Groomers": "----",
        "Groomers In": "----",
        "Groomers Out": "----",
        "Crew at Gate": "----",
        "OK to Board": "----",
        "Flight Secure": "----",
        "Cierre de Puerta": "----",
        "Push Back": "----"
    },
    "Información de Customs": {
        "Customs In": "----",
        "Customs Out": "----"
    },
    "Información de Pasajeros": {
        "Total Pax": "----",
        "PAX C": "----",
        "PAX Y": "----",
        "Infantes": "----"
    },
    "Información por Demoras": {
        "Delay": "----",
        "Delay Code": "----"
    },
    "Silla de ruedas": {
        "Sillas Vuelo Llegada (AV626)": "----",
        "Agentes Vuelo Llegada (AV626)": "----",
        "Sillas Vuelo Salida (AV627)": "----",
        "Agentes Vuelo Salida (AV627)": "----"
    },
    "Información de Gate y Carrusel": {
        "Gate": "----",
        "Carrousel": "----"
    },
    "Información de Gate Bag": {
        "Gate Bag": "----"
    },
    "Comentarios": {
        "Comentarios": "----"
    }
}

SYSTEM_PROMPT = """Eres un motor de extracción de datos extremadamente preciso para reportes de vuelo (Flight Departure Report).
Tarea: a partir de una imagen del reporte, devuelve **estrictamente** un JSON con los siguientes campos y **exactamente** estas claves (en español). 
Si un dato no aparece, escribe '----'. 
Formatea las horas en HH:MM 24h y normaliza valores tipo Sillas (ej: '17 WCHR | 00 WCHC').
No infieras datos que no estén legibles; prioriza fidelidad sobre completitud.

Estructura JSON exacta (no agregues ni quites claves):
{
  "Datos Básicos": {
    "Fecha de vuelo": "...",
    "Origen": "...",
    "Destino": "...",
    "Número de vuelo": "..."
  },
  "Tiempos": {
    "STD": "...",
    "ATD": "...",
    "Salida de Tripulacion": "...",
    "Cantidad de Agentes Groomers": "...",
    "Groomers In": "...",
    "Groomers Out": "...",
    "Crew at Gate": "...",
    "OK to Board": "...",
    "Flight Secure": "...",
    "Cierre de Puerta": "...",
    "Push Back": "..."
  },
  "Información de Customs": {
    "Customs In": "...",
    "Customs Out": "..."
  },
  "Información de Pasajeros": {
    "Total Pax": "...",
    "PAX C": "...",
    "PAX Y": "...",
    "Infantes": "..."
  },
  "Información por Demoras": {
    "Delay": "...",
    "Delay Code": "..."
  },
  "Silla de ruedas": {
    "Sillas Vuelo Llegada (AV626)": "...",
    "Agentes Vuelo Llegada (AV626)": "...",
    "Sillas Vuelo Salida (AV627)": "...",
    "Agentes Vuelo Salida (AV627)": "..."
  },
  "Información de Gate y Carrusel": {
    "Gate": "...",
    "Carrousel": "..."
  },
  "Información de Gate Bag": {
    "Gate Bag": "..."
  },
  "Comentarios": {
    "Comentarios": "..."
  }
}

Reglas:
- Usa '----' si falta información o es ilegible.
- Mantén números enteros sin texto adicional (ej.: '140', no '140 pax'), excepto los campos de sillas, que deben seguir 'NN WCHR | NN WCHC' con ceros a la izquierda.
- 'Customs In/Out': devuelve 'No Customs' si explícitamente el reporte indica que no hubo.
- No devuelvas nada que no sea JSON.
"""

def safe_json_extract(text: str) -> Dict[str, Any]:
    # Attempt to extract the first valid JSON object from a string response
    if not text:
        return {}
    # Trim code fences if any
    text = text.strip()
    fence = "```"
    if text.startswith(fence):
        # remove first fence
        text = text.split(fence, 2)
        if len(text) >= 3:
            text = text[1] if text[0].strip() == "" else text[2]
        else:
            text = text[-1]
    # Find first { and last }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start:end+1]
    else:
        candidate = text
    try:
        return json.loads(candidate)
    except Exception:
        # Last resort: replace single quotes and try
        try:
            candidate2 = candidate.replace("'", '"')
            return json.loads(candidate2)
        except Exception:
            return {}

def merge_with_defaults(parsed: Dict[str, Any]) -> Dict[str, Any]:
    # Ensure all keys exist and fill missing with '----'
    out = json.loads(json.dumps(EXPECTED_KEYS))  # deep copy
    for section, fields in out.items():
        if section in parsed and isinstance(parsed[section], dict):
            for key in fields.keys():
                val = parsed[section].get(key, "----")
                # normalize empty/none
                if val is None or (isinstance(val, str) and val.strip() == ""):
                    val = "----"
                out[section][key] = str(val)
    return out

def render_markdown(data: Dict[str, Any]) -> str:
    # Build the exact requested Markdown block
    lines = []
    # Datos básicos
    lines.append("🚀 *Datos Básicos*:")
    for k in EXPECTED_KEYS["Datos Básicos"].keys():
        lines.append(f"\n*{k}:* {data['Datos Básicos'][k]}")
    # Tiempos
    lines.append("\n\n⏰ *Tiempos:*")
    for k in EXPECTED_KEYS["Tiempos"].keys():
        lines.append(f"\n*{k}:* {data['Tiempos'][k]}")
    # Customs
    lines.append("\n\n📋 *Información de Customs:*")
    for k in EXPECTED_KEYS["Información de Customs"].keys():
        lines.append(f"\n*{k}:* {data['Información de Customs'][k]}")
    # Pasajeros
    lines.append("\n\n👥 *Información de Pasajeros:*")
    for k in EXPECTED_KEYS["Información de Pasajeros"].keys():
        lines.append(f"\n*{k}:* {data['Información de Pasajeros'][k]}")
    # Demoras
    lines.append("\n\n⏳ *Información por Demoras:*")
    for k in EXPECTED_KEYS["Información por Demoras"].keys():
        lines.append(f"\n*{k}:* {data['Información por Demoras'][k]}")
    # Sillas
    lines.append("\n\n♿ *Silla de ruedas:*")
    for k in EXPECTED_KEYS["Silla de ruedas"].keys():
        lines.append(f"\n*{k}:* {data['Silla de ruedas'][k]}")
    # Gate/Carrusel
    lines.append("\n\n📍 *Información de Gate y Carrusel:*")
    for k in EXPECTED_KEYS["Información de Gate y Carrusel"].keys():
        lines.append(f"\n*{k}:* {data['Información de Gate y Carrusel'][k]}")
    # Gate Bag
    lines.append("\n\n🧳 *Información de Gate Bag:*")
    for k in EXPECTED_KEYS["Información de Gate Bag"].keys():
        lines.append(f"\n*{k}:* {data['Información de Gate Bag'][k]}")
    # Comentarios
    lines.append("\n\n💬 *Comentarios:*")
    lines.append(f"\n{data['Comentarios']['Comentarios']}")
    lines.append("\n---")
    return "".join(lines)

def build_gemini():
    if genai is None:
        raise RuntimeError("google-generativeai no está instalado.")
    # Intentar obtener la API key de los secrets de Streamlit
    api_key = st.secrets.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        # Si no está en secrets, intentar obtenerla del input en la UI
        api_key = st.session_state.get("gemini_key_override", "").strip()
        if not api_key:
            raise RuntimeError("Falta GEMINI_API_KEY en .streamlit/secrets.toml")
    genai.configure(api_key=api_key)
    model_name = st.session_state.get("gemini_model", DEFAULT_GEMINI_MODEL)
    return genai.GenerativeModel(model_name)

def gemini_extract(img_bytes: bytes) -> Dict[str, Any]:
    model = build_gemini()
    prompt = SYSTEM_PROMPT
    blob = {"mime_type": "image/png", "data": img_bytes}
    try:
        resp = model.generate_content([prompt, blob], generation_config={"temperature": 0})
        text = resp.text
        # Logging de tokens y detalles de la API
        # Los objetos Gemini devuelven usage_metadata si está disponible
        usage = getattr(resp, "usage_metadata", None)
        if usage:
            print("[Gemini API] Tokens usados:", file=sys.stderr)
            print(f"  Prompt tokens: {usage.prompt_token_count}", file=sys.stderr)
            print(f"  Candidates tokens: {usage.candidates_token_count}", file=sys.stderr)
            print(f"  Total tokens: {usage.total_token_count}", file=sys.stderr)
        # Mostrar info de modelo y precios (hardcodeado, puede cambiar)
        print(f"[Gemini API] Modelo: {model.model_name}", file=sys.stderr)
        print("[Gemini API] Precios estimados (sept 2025):", file=sys.stderr)
        print("  gemini-1.5-flash: $0.35/millón input tokens, $1.05/millón output tokens", file=sys.stderr)
        print("  gemini-1.5-pro: $3.50/millón input tokens, $10.50/millón output tokens", file=sys.stderr)
    except Exception as e:
        raise RuntimeError(f"Gemini error: {e}")
    parsed = safe_json_extract(text)
    return merge_with_defaults(parsed)








def main():
    st.set_page_config(page_title=APP_TITLE, page_icon="🛫", layout="centered")
    st.title(APP_TITLE)
    st.caption("Sube una imagen del *Flight Departure Report* y extrae los campos en el formato requerido.")

    with st.expander("Configuración del proveedor", expanded=True):
        # Solo mostrar el campo de API key si no está en secrets
        if not st.secrets.get("GEMINI_API_KEY"):
            st.text_input("GEMINI_API_KEY", type="password", key="gemini_key_override",
                         help="Configura la API key en .streamlit/secrets.toml para no tener que ingresarla aquí")
        st.selectbox("Modelo Gemini", [DEFAULT_GEMINI_MODEL, "gemini-1.5-pro"], key="gemini_model")

    uploaded = st.file_uploader("Sube la imagen (JPG/PNG)", type=["png", "jpg", "jpeg"])

    # Estado para los datos extraídos y editados
    if 'editable_data' not in st.session_state:
        st.session_state['editable_data'] = json.loads(json.dumps(EXPECTED_KEYS))

    cols = st.columns(2)
    with cols[0]:
        run = st.button("Extraer", type="primary", use_container_width=True)
    with cols[1]:
        st.write("")

    if run:
        if not uploaded:
            st.error("Primero sube una imagen.")
            st.stop()
        img_bytes = uploaded.read()
        try:
            data = gemini_extract(img_bytes)
        except Exception as e:
            st.error(f"Error durante la extracción: {e}")
            with st.expander("Traceback"):
                st.code(traceback.format_exc())
            st.stop()
        # Guardar en el estado editable
        st.session_state['editable_data'] = data

    # Mostrar campos editables agrupados por sección
    st.markdown("---")
    editable = st.session_state['editable_data']

    # 🚀 Datos Básicos
    st.markdown("🚀 **Datos Básicos**:")
    with st.container():
        c1, c2 = st.columns(2)
        with c1:
            editable['Datos Básicos']['Fecha de vuelo'] = st.text_input("✈️ Fecha de vuelo", value=editable['Datos Básicos']['Fecha de vuelo'], key="fecha_vuelo")
            editable['Datos Básicos']['Origen'] = st.text_input("🛫 Origen", value=editable['Datos Básicos']['Origen'], key="origen")
        with c2:
            editable['Datos Básicos']['Destino'] = st.text_input("🛬 Destino", value=editable['Datos Básicos']['Destino'], key="destino")
            editable['Datos Básicos']['Número de vuelo'] = st.text_input("# Número de vuelo", value=editable['Datos Básicos']['Número de vuelo'], key="num_vuelo")

    st.markdown("\n⏰ **Tiempos:**")
    with st.container():
        c1, c2 = st.columns(2)
        for i, k in enumerate(EXPECTED_KEYS['Tiempos'].keys()):
            col = c1 if i % 2 == 0 else c2
            editable['Tiempos'][k] = col.text_input(f"{k}", value=editable['Tiempos'][k], key=f"tiempos_{k}")

    st.markdown("\n📋 **Información de Customs:**")
    with st.container():
        c1, c2 = st.columns(2)
        i = 0
        for k in EXPECTED_KEYS['Información de Customs'].keys():
            col = c1 if i % 2 == 0 else c2
            editable['Información de Customs'][k] = col.text_input(f"{k}", value=editable['Información de Customs'][k], key=f"customs_{k}")
            i += 1

    st.markdown("\n👥 **Información de Pasajeros:**")
    with st.container():
        c1, c2 = st.columns(2)
        i = 0
        for k in EXPECTED_KEYS['Información de Pasajeros'].keys():
            col = c1 if i % 2 == 0 else c2
            editable['Información de Pasajeros'][k] = col.text_input(f"{k}", value=editable['Información de Pasajeros'][k], key=f"pax_{k}")
            i += 1

    st.markdown("\n⏳ **Información por Demoras:**")
    with st.container():
        c1, c2 = st.columns(2)
        i = 0
        for k in EXPECTED_KEYS['Información por Demoras'].keys():
            col = c1 if i % 2 == 0 else c2
            editable['Información por Demoras'][k] = col.text_input(f"{k}", value=editable['Información por Demoras'][k], key=f"demoras_{k}")
            i += 1

    st.markdown("\n♿ **Silla de ruedas:**")
    with st.container():
        c1, c2 = st.columns(2)
        i = 0
        for k in EXPECTED_KEYS['Silla de ruedas'].keys():
            col = c1 if i % 2 == 0 else c2
            editable['Silla de ruedas'][k] = col.text_input(f"{k}", value=editable['Silla de ruedas'][k], key=f"silla_{k}")
            i += 1

    st.markdown("\n📍 **Información de Gate y Carrusel:**")
    with st.container():
        c1, c2 = st.columns(2)
        i = 0
        for k in EXPECTED_KEYS['Información de Gate y Carrusel'].keys():
            col = c1 if i % 2 == 0 else c2
            editable['Información de Gate y Carrusel'][k] = col.text_input(f"{k}", value=editable['Información de Gate y Carrusel'][k], key=f"gatecarrusel_{k}")
            i += 1

    st.markdown("\n🧳 **Información de Gate Bag:**")
    editable['Información de Gate Bag']['Gate Bag'] = st.text_input("Gate Bag", value=editable['Información de Gate Bag']['Gate Bag'], key="gatebag")

    st.markdown("\n💬 **Comentarios:**")
    editable['Comentarios']['Comentarios'] = st.text_area("Comentarios", value=editable['Comentarios']['Comentarios'], key="comentarios")



    # Botón para guardar información revisada
    st.markdown("---")
    guardar = st.button("ACTUALIZAR INFORMACION", type="primary", use_container_width=True)
    if guardar:
        # Actualiza el JSON y el reporte de WhatsApp en el estado
        st.session_state['editable_data'] = editable
        st.success("Información revisada guardada correctamente.")

    # Sección para copiar reporte a portapapeles
    st.markdown("---")
    st.subheader("Copiar reporte a Portapapeles para WhatsApp")
    wpp_report = build_wpp_report(st.session_state['editable_data'])
    st.code(wpp_report, language="")
    
    # Botón con JavaScript para copiar al portapapeles
    js_text = wpp_report.replace("\n", "\\n").replace('"', '\\"')
    st.markdown(
        f"""
        <div style="display: flex; justify-content: center; margin-bottom: 1rem;">
            <button 
                onclick="navigator.clipboard.writeText('{js_text}').then(() => {{
                    this.innerHTML = '✅ ¡Copiado!';
                    setTimeout(() => {{
                        this.innerHTML = '📱 Botón de copiar: Esquina superior derecha del cuadro';
                    }}, 2000);
                }})"
                style="background-color: #FF4B4B; color: white; padding: 0.5rem 1rem; 
                border: none; border-radius: 0.5rem; cursor: pointer; font-size: 1rem;
                display: flex; align-items: center; gap: 0.5rem;"
            >
                📱 Botón de copiar: Esquina superior derecha del cuadro
            </button>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Botones de descarga y visualización
    st.markdown("---")
    st.subheader("JSON editable actual")
    st.json(editable)
    st.download_button("Descargar JSON", data=json.dumps(editable, ensure_ascii=False, indent=2), file_name="resultado.json", mime="application/json")

    st.markdown("""**Consejo:** para formularios con escritura manual, las LLMs funcionan mejor si la imagen es nítida, sin sombras y con contraste alto.\nSi un campo no está en el reporte, la salida **debe** ser '----'. No se permite 'inventar' valores.""")

if __name__ == "__main__":
    main()
