# Automatización de Pruebas de Conversación en Paralelo

Este proyecto permite realizar pruebas automatizadas de conversaciones con bots utilizando una interfaz interactiva construida con Streamlit. Los usuarios pueden definir prompts, configurar parámetros de conexión y ejecutar múltiples conversaciones en paralelo, facilitando el análisis y la depuración del comportamiento del bot.

## Características

- Interfaz gráfica intuitiva para definir y gestionar prompts.
- Configuración dinámica de parámetros como `bot_id`, `endpoint`, y `canal`.
- Ejecución de pruebas en paralelo para optimizar el tiempo de análisis.
- Generación de mensajes simulados utilizando la API de OpenAI.
- Registro detallado de logs para cada conversación.

## Requisitos

### Dependencias
Asegúrate de tener instalado Python 3.8 o superior y las siguientes bibliotecas:

- `streamlit`
- `requests`
- `uuid`
- `openai`

Instálalas con el siguiente comando:

```bash
pip install streamlit requests openai


Iniciar la Aplicación Ejecuta el siguiente comando para iniciar la interfaz de usuario de Streamlit:


streamlit run app.py#   p r u e b a s _ p a r a l e l a s  
 