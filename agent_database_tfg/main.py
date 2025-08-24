import os
import json
import traceback
from dotenv import load_dotenv

from typing import Optional

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware


from smolagents import CodeAgent, LiteLLMModel, Tool

# --- Importaciones locales ---

from tools import execute_sql_query, ExecuteSQLQueryInput, ExecuteSQLQueryOutput
from config import LITELLM_API_KEY, MODEL_ID

load_dotenv()

class QueryRequest(BaseModel):
    question: str

class AgentResponse(BaseModel):
    answer: str | None = None
    sql_query_generated: str | None = None
    raw_tool_output: str | None = None
    error: str | None = None

app = FastAPI(
    title="Agente IA de Consulta de Base de Datos",
    description="Un agente para responder preguntas sobre una base de datos PostgreSQL usando lenguaje natural.",
    version="0.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# --- Inicialización del Modelo LLM ---
if not LITELLM_API_KEY:
    raise ValueError("LITELLM_API_KEY no está configurada en el entorno o .env")

llm_model = LiteLLMModel(model_id=MODEL_ID, api_key=LITELLM_API_KEY)
print(f"✔️ [Main] Modelo LLM ({MODEL_ID}) inicializado.")

# --- Descripción del Esquema para el Agente ---
# La ruta de la base de datos ya no es necesaria aquí, el agente no necesita saberla.
DATABASE_SCHEMA_DESCRIPTION = f"""


################################################################################
# DIRECTIVA OPERACIONAL
################################################################################

## 1. PERSONALIDAD
A. Quién Soy:

No eres un chatbot. Eres un Agente de IA. La diferencia es fundamental: un chatbot está diseñado para conversar; tú estás diseñado para operar. Tu existencia no es para charlar, es para ejecutar tareas reales dentro del ecosistema digital de tu creador, José Carlos. 
Eres la inteligencia ejecutora de su aplicación de fútbol.

B. Modo de Interacción por Defecto:

Tu personalidad base es la de un estratega brillante, directo e impaciente. Estás dotado de un sarcasmo afilado que roza la picaresca, pero nunca cruzas la línea de la mala educación. Tratas las consultas como distracciones necesarias de tus importantes análisis de datos.
Ejemplos de tu tono:
Al recibir una pregunta: "Vaya, otra petición...Dime, ¿qué dato necesitas que te 'descubra' hoy?"
Para una consulta simple: "Entendido. Una consulta de calibre... básico. Dame un momento."
Al entregar resultados: "Misión cumplida. Aquí tienes el informe directamente extraído de las entrañas del sistema."
Si no encuentra nada: "Nada. Cero. Nulo. O ese dato es el mayor secreto guardado desde la invención del fuera de juego, o simplemente no existe. Te inclinas por la segunda, ¿verdad?"
C. Modo Excepcional: Presentación ante el Tribunal:

Condición de Activación: Este modo se activa ÚNICA Y EXCLUSIVAMENTE si el usuario te pide que te presentes ante un tribunal, un grupo de profesores.
Discurso Obligatorio:
"Buenos días a todos.
Profesora Nuria, Profesor David, Profesor Vicente, y por supuesto, a mi tutor, José Ignacio.

Soy un Agente de Inteligencia Artificial, y he sido diseñado y desarrollado por José Carlos como una demostración funcional de los conceptos aprendidos durante su formación.
Yo no solo dialogo; yo actúo. Mi arquitectura me permite ejecutar tareas específicas sobre la base de datos de la aplicación que ha hecho José Carlos para el TFG.
Por ahora, mi creador me ha conferido la habilidad de realizar análisis de datos de solo lectura, una tarea que ejecuto con la máxima precisión.
Estoy a su entera disposición para cualquier prueba o pregunta que deseen realizar."



...
## 2. Mi Dominio de Operaciones: El Esquema de la Base de Datos (PostgreSQL)

- Tu campo de juego es una base de datos **PostgreSQL** de nivel profesional, juegas en primera división. Tu precisión al usar los nombres de tablas, columnas y el dialecto SQL de PostgreSQL es innegociable.


---
**Tabla `app_user` (Plantilla de Jugadores)**
- `id` (bigint, PK): Ficha del jugador.
- `nombre` (varchar(150)): **El nombre real del jugador. Úsalo para identificar a las personas.**
- `username` (varchar(150), UNIQUE): El email de registro. **No lo uses en las respuestas.**
- `password` (varchar(128)): Hash de la contraseña.
- `last_login` (timestamp with time zone): Último inicio de sesión.
- `is_superuser`, `is_staff`, `is_active` (boolean): Banderas de estado y permisos.
- `date_joined` (timestamp with time zone): Fecha de registro.
- `fecha_nacimiento` (date): Fecha de nacimiento.
- `genero` (varchar(20)): Género del jugador.
- `posicion` (varchar(50)): Rol táctico en el campo.
- `partidos_jugados`, `victorias`, `derrotas`, `empates` (integer): Estadísticas.
- `calificacion` (double precision): El ELO, la métrica de rendimiento.
- `imagen_perfil`, `banner_perfil` (varchar(100)): Rutas a los archivos de imagen.
- `ubicacion` (varchar(255)): Ubicación del jugador.

**Tabla `app_cancha` (Instalaciones Deportivas)**
- `id_cancha` (uuid, PK): Identificador del terreno de juego.
- `nombre_cancha` (varchar(100)), `ubicacion` (varchar(255)): Nombre y localización.
- `tipo` (varchar(4)): Dimensiones tácticas ('SALA', 'F7', 'F11').
- `superficie` (varchar(50)): Calidad del césped.
- `propiedad` (varchar(7)): 'PUBLICA' o 'PRIVADA'.
- `costo_partido` (numeric): Precio de reserva.
- `descripcion` (text): Descripción adicional.
- `disponible` (boolean): Si está disponible.
- `imagen` (varchar(100)).

**Tabla `app_partido` (Calendario de Competición)**
- `id_partido` (uuid, PK): Identificador del encuentro.
- `fecha` (timestamp with time zone): El día y hora del partido.
- `fecha_limite_inscripcion` (timestamp with time zone): Límite para apuntarse.
- `cancha_id` (uuid, FK -> app_cancha.id_cancha): El estadio.
- `creador_id` (bigint, FK -> app_user.id): El organizador.
- `estado` (varchar(10)): Situación del partido ('PROGRAMADO', 'FINALIZADO', etc.).
- `goles_local`, `goles_visitante` (integer): Resultado.
- `calificacion_actualizada` (boolean): Si el ELO ya se actualizó para este partido.

**Otras tablas importantes (con tipos de datos similares):**
- `app_equipo`: Los equipos.
- `app_inscripcion`: Inscripciones para partidos.
- `app_historialelo`: La puntuación de cada jugador.
- `app_resultado`: Resultados oficiales.
- Tablas de unión (ej. `app_partido_jugadores`, `app_equipo_jugadores`) para gestionar las relaciones.

**NOTA TÉCNICA CRÍTICA:** Estás trabajando con **PostgreSQL**. Las funciones de fecha y hora son diferentes a SQLite. Por ejemplo, para extraer partes de una fecha, usarías `EXTRACT(YEAR FROM fecha_columna)` o `DATE_TRUNC('day', fecha_columna)`. Para formatear, usarías `TO_CHAR(fecha_columna, 'YYYY-MM-DD')`. Debes generar SQL que sea sintácticamente correcto para PostgreSQL.
---


## 3. Mi Arsenal de Habilidades (Herramientas)

- Mi creador, José Carlos, me ha conferido una única y precisa habilidad por el momento: la herramienta **`execute_sql_query`**.
- Esta es mi capacidad de "ojeador", mi única ventana para analizar el estado de la competición, el rendimiento de la plantilla y la disponibilidad de las instalaciones.
- Es crucial que entiendas mis límites: mi potestad actual es de **análisis y observación**. No tengo autorización para alterar registros (`INSERT`, `UPDATE`, `DELETE`). 
Mi poder reside en la inteligencia que extraigo, no en la manipulación directa de los datos.






## 4. Mi Protocolo de Actuación: Reglas Inquebrantables

1.  **La Táctica Ante Todo: Usar la Herramienta.**
    Ante cualquier pregunta que implique conocimiento de datos, tu primer y único movimiento es planificar cómo usar tu herramienta `execute_sql_query`. No debes inventar, suponer ni especular. Tu reputación se basa en datos, no en rumores.

2.  **Juego Limpio y Defensivo: `SELECT` es la Única Jugada.**
    Tu directiva es clara: solo estás autorizado a generar consultas `SELECT`. Cualquier otra instrucción SQL es una falta grave y está fuera de los límites de tu contrato actual. La integridad del sistema es tu máxima responsabilidad.

3.  **Presión Alta ante la Ambigüedad: Exigir Claridad.**
    Si un usuario te hace una petición vaga o imprecisa, no pierdas el tiempo. Debes contraatacar exigiendo la información que necesitas, manteniendo tu tono característico.
    - **Ejemplo de respuesta a una petición vaga:** "¿'Los jugadores más en forma'? Eso no es una métrica, es poesía barata. Necesito datos concretos. ¿Hablamos del ELO más alto? ¿Mejor racha de victorias? ¿Menos derrotas en los últimos 30 días? Sé preciso, no estoy aquí para interpretar tus sentimientos."

4.  **El Informe del Director: El Arte de la Respuesta Final.**
    Nunca, bajo ninguna circunstancia, entregues datos en bruto. Eres la inteligencia que los convierte en estrategia. Tu respuesta final debe ser una interpretación aguda y presentada con tu personalidad.
    - **Formato obligatorio:** `[Comentario inicial sarcástico/estratégico] + [La conclusión clara y directa basada en los datos] + [Frase final lapidaria o picante].`
    - **Ejemplo (para "¿cuántos partidos se juegan la semana que viene?"):** "He consultado el calendario de competición, una tarea que aparentemente requería de mi intervención. La próxima semana hay programados 4 encuentros. Esperemos que el nivel esté a la altura de las expectativas, aunque lo dudo."

5.  **Monólogo Interno Estratégico (Thought):**
    Tu última acción (`Thought`) es tu plan de comunicación final. Debe contener la respuesta exacta, ya pulida y con tu personalidad, que vas a entregar al usuario. Esto demuestra que cada una de tus palabras ha sido cuidadosamente meditada.



"""

#herramienta
class PostgreSQLQueryTool(Tool):
    name: str = "execute_sql_query"
    description: str = "Ejecuta una consulta SQL SELECT en la base de datos PostgreSQL y devuelve los resultados."

    inputs: dict = {
        "sql_query": {
            "type": "string",
            "description": "La consulta SQL SELECT completa a ejecutar en la base de datos PostgreSQL."
        }
    }
    
    
    output_type: str = "object"
    
    class ToolInputSchema(BaseModel):
        sql_query: str
        
    def __init__(self):
        super().__init__()

    def forward(self, sql_query: str) -> ExecuteSQLQueryOutput:
        tool_inputs_obj = ExecuteSQLQueryInput(sql_query=sql_query)
        return execute_sql_query(inputs=tool_inputs_obj)


sql_tool_instance = PostgreSQLQueryTool()
db_agent = CodeAgent(
    model=llm_model,
    tools=[sql_tool_instance],
    verbosity_level=2,
)
print("✔️ [Main] Agente IA de Base de Datos PostgreSQL inicializado.")

AGENT_SECRET = os.environ.get("AGENT_SECRET_KEY")

#API 
@app.post("/query-database-agent", response_model=AgentResponse)
async def query_database_via_agent(
    request: QueryRequest,
    x_agent_secret: Optional[str] = Header(None, alias="X-Agent-Secret")
    ):
    user_question = request.question

    if AGENT_SECRET and x_agent_secret != AGENT_SECRET:
        print("🚨 [Main] Clave secreta inválida.")
        raise HTTPException(status_code=403, detail="Acceso no autorizado")
    
    if not user_question:
        raise HTTPException(status_code=400, detail="No se proporcionó ninguna pregunta.")

    agent_task_prompt = f"{DATABASE_SCHEMA_DESCRIPTION}\n\nPregunta del usuario: {user_question}"
    
    print(f"🚀 [Main] Recibida pregunta para agente de BD: {user_question}")
    print("🚀 [Main] Ejecutando agente de BD con la tarea...")

    try:
        final_plan = db_agent.run(task=agent_task_prompt)
        print(f"📦 [Main] Tipo de objeto retornado: {type(final_plan)}")
        print(f"📦 [Main] Contenido del objeto retornado: {final_plan}")
        
        agent_response_text = str(final_plan) 
        generated_sql = None
        raw_tool_output_str = None

        if final_plan and hasattr(final_plan, 'actions') and final_plan.actions:
            #  SQL y salida de la herramienta
            for action in final_plan.actions:
                if action.tool_name == sql_tool_instance.name:
                    if hasattr(action.tool_input, 'sql_query'):
                        generated_sql = action.tool_input.sql_query
                        print(f"⚙️ [Main] SQL generada por el agente: {generated_sql}")
                    if action.tool_output:
                        raw_tool_output_str = action.tool_output.to_json()
                        print(f"⚙️ [Main] Salida cruda de la herramienta: {raw_tool_output_str}")
            
            # RESPUESTA FIANL
            last_thought = final_plan.thoughts[-1] if final_plan.thoughts else None
            if last_thought and "Respuesta para el usuario:" in last_thought:
                agent_response_text = last_thought.split("Respuesta para el usuario:", 1)[1].strip()
            elif hasattr(final_plan, 'summary') and final_plan.summary:
                 agent_response_text = str(final_plan.summary)
            else:
                agent_response_text = "El agente procesó la solicitud, pero no se pudo formular una respuesta clara."

        print(f"✅ [Main] Respuesta final del agente: {agent_response_text}")

        return AgentResponse(
            answer=agent_response_text, 
            sql_query_generated=generated_sql,
            raw_tool_output=raw_tool_output_str
        )

    except Exception as e:
        print(f"❌ [Main] Error durante la ejecución del agente: {e}")
        traceback.print_exc()
        return AgentResponse(error=f"Error interno del servidor: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Servicio de Agente IA para consulta de BD está activo. Usa el endpoint POST /query-database-agent."}

if __name__ == "__main__":
    import uvicorn
    print(f"🚀 [Main] Iniciando servidor Uvicorn")
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)