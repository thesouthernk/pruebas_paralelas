import streamlit as st
import requests
import time
import uuid
import openai
from openai import OpenAI
import os
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ------------------------------------------------------------------------------
# Funciones auxiliares
# ------------------------------------------------------------------------------

def generate_unique_id():
    """Genera un ID único para identificar la conversación."""
    return str(uuid.uuid4())

def send_message(unique_id, message, bot_id, endpoint, channel, test_mode):
    """Envía un mensaje al endpoint y devuelve la respuesta."""
    payload = {
        "data": {
            "identificador": unique_id,
            "bot": bot_id,
            "mensaje": message,
            "tipo": "text",
        },
        "canal": channel,
        "test": test_mode,
    }
    logs = []

    try:
        t1 = datetime.datetime.now()
        response = requests.post(endpoint, json=payload, timeout=360)
        t2 = datetime.datetime.now()

        request_time = f"Request time: {t2 - t1}"
        logs.append(request_time)

        response.raise_for_status()
        response_data = response.json()

        # Verificar si la respuesta es una lista o un dict
        if isinstance(response_data, list):
            return response_data[0], logs
        elif isinstance(response_data, dict):
            return response_data, logs
        else:
            msg = f"Formato de respuesta inesperado: {response_data}"
            logs.append(msg)
            return {"error": msg}, logs

    except requests.exceptions.RequestException as e:
        error_msg = f"Error al enviar el mensaje: {e}"
        logs.append(error_msg)
        return {"error": str(e)}, logs

def get_id_chat(ip, bot_id):
    """Obtiene el ID del chat basado en la IP y el bot_id."""
    url_ip = f"https://backend.krino.ai/chat/get_chat_by_ip/{ip}_{bot_id}"
    try:
        response = requests.get(url_ip, headers={"token": "B7hEAPKxhWGY9DKu3zbCNDYNsC4n"})
        response.raise_for_status()
        chat_id = response.json().get('id', None)
        return chat_id
    except requests.exceptions.RequestException as e:
        return None

def simulate_customer_message(message_history, dynamic_prompt, client):
    """
    Genera el siguiente mensaje basado en la conversación previa usando GPT.
    """
    prompt = f"""{dynamic_prompt}

Genera el siguiente mensaje basado en la conversación previa:
"""
    # Creamos una copia para no mutar el original
    temp_history = [
        {"role": "assistant", "content": prompt}
    ] + message_history

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=temp_history,
        temperature=0.2
    )
    return response.choices[0].message.content

def run_conversation(initial_prompt, base_prompt, bot_id, endpoint, channel, test_mode, client):
    """
    Ejecuta una conversación de prueba con el bot, retorna los logs generados.
    """
    logs = []
    unique_id = generate_unique_id()
    logs.append(f"ID de la conversación: {unique_id}")

    # Historial inicial
    message_history = [
        {"role": "user", "content": initial_prompt}
    ]

    chat_obtained = False

    # Realizamos 4 turnos de conversación
    for i in range(rounds_number):
        logs.append(f"\n--- Turno {i + 1} ---")

        user_message = message_history[-1]["content"]
        bot_response, send_msg_logs = send_message(unique_id, user_message, bot_id, endpoint, channel, test_mode)
        logs.extend(send_msg_logs)  # Incorporamos los logs del send_message

        if not chat_obtained:
            chat_id = get_id_chat(unique_id, bot_id)
            logs.append(f"Chat ID obtenido: {chat_id}")
            chat_obtained = True

        if "error" in bot_response:
            logs.append(f"Error recibido: {bot_response['error']}")
            break

        bot_message = bot_response.get("sentence", "Sin respuesta.")
        logs.append(f"Bot: {bot_message}")
        message_history.append({"role": "user", "content": bot_message})

        # Generamos el siguiente mensaje del cliente
        next_message = simulate_customer_message(message_history, base_prompt, client)
        logs.append(f"Próximo mensaje del cliente: {next_message}")
        message_history.append({"role": "assistant", "content": next_message})

    return "\n".join(logs)

def run_parallel_tests(prompts, base_prompt, bot_id, endpoint, channel, test_mode, client, max_workers=5):
    """
    Ejecuta varias conversaciones en paralelo y retorna la lista de logs de cada conversación.
    """
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(
                run_conversation, 
                prompt, 
                base_prompt, 
                bot_id, 
                endpoint, 
                channel, 
                test_mode, 
                client
            )
            for prompt in prompts
        ]
        for future in as_completed(futures):
            results.append(future.result())
    return results

# ------------------------------------------------------------------------------
# Interfaz de Streamlit
# ------------------------------------------------------------------------------

st.title("Pruebas de Conversaciones en Paralelo")

# Lectura de la API Key (opcional, para GPT) desde la interfaz
st.sidebar.header("Configuración")
OPENAI_API_KEY = st.sidebar.text_input("OpenAI API Key", type="password")

if OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
    client = OpenAI()
else:
    st.warning("Ingresa tu OpenAI API Key para poder usar la generación de mensajes con GPT.")
    client = None

# Parámetros para la conexión con el Bot
bot_id = st.sidebar.number_input("Bot ID", value=873, step=1)
rounds_number = st.sidebar.number_input("Número de rondas de interacción", value=6, step=1)
endpoint = st.sidebar.text_input("Endpoint URL", value="https://motor-ai.calmsmoke-f5ed124e.eastus2.azurecontainerapps.io/web/web")
channel = st.sidebar.text_input("Canal (Channel)", value="WEB")
test_mode = st.sidebar.checkbox("Test Mode", value=True)

# Prompt base (dinámico)
base_prompt = st.text_area(
    "Prompt base para la generación del siguiente mensaje",
    value="Genera un mensaje de prueba basado en el historial de la conversación."
)

st.markdown("---")
st.subheader("Prompts para pruebas")

# Sesión para almacenar la lista de prompts
if "prompts" not in st.session_state:
    st.session_state.prompts = [
        "Este es un ejemplo de prompt 1",
        "Este es un ejemplo de prompt 2",
        "Este es un ejemplo de prompt 3"
    ]

# Muestra los prompts actuales con opción para remover
st.write("Prompts registrados:")
to_remove = None
for idx, p in enumerate(st.session_state.prompts, 1):
    col1, col2 = st.columns([4,1])
    with col1:
        st.text(p)
    with col2:
        # Botón para eliminar este prompt
        if st.button(f"Eliminar {idx}", key=f"remove_{idx}"):
            # Verifica que no sea el último prompt
            if len(st.session_state.prompts) > 1:
                to_remove = idx - 1  # índice real en la lista
            else:
                st.warning("No se puede eliminar el último prompt (mínimo 1).")

# Si se presionó eliminar alguno, se realiza la operación y se recarga la página
if to_remove is not None:
    st.session_state.prompts.pop(to_remove)
    st.experimental_rerun()

# Cuadro de texto para agregar nuevos prompts
new_prompt = st.text_area("Agrega un nuevo prompt aquí")

if st.button("Añadir prompt"):
    if new_prompt.strip():
        st.session_state.prompts.append(new_prompt.strip())
        st.success("¡Prompt agregado!")
    else:
        st.warning("El prompt está vacío. Por favor ingresa texto.")
    st.experimental_rerun()

# Botón para ejecutar las pruebas
if st.button("Ejecutar pruebas en paralelo"):
    if not client:
        st.error("Necesitas ingresar una OpenAI API Key para generar mensajes de prueba.")
    else:
        st.info("Iniciando pruebas en paralelo, por favor espera...")

        # Ejecutar conversaciones
        results = run_parallel_tests(
            prompts=st.session_state.prompts,
            base_prompt=base_prompt,
            bot_id=bot_id,
            endpoint=endpoint,
            channel=channel,
            test_mode=test_mode,
            client=client,
            max_workers=5
        )

        # Mostrar resultados
        for i, log_result in enumerate(results, start=1):
            st.markdown(f"### Conversación {i}")
            st.text(log_result)
