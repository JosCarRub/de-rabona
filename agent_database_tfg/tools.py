from smolagents import tool   
from pydantic import BaseModel    
import sqlparse

from sqlalchemy import create_engine, text, exc
import os
from dotenv import load_dotenv

load_dotenv()


DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("La variable de entorno DATABASE_URL no está configurada en el .env del agente.")


try:

    engine = create_engine(DATABASE_URL)
    print(f"✔️ [Tools] Motor de base de datos PostgreSQL conectado a: {engine.url.host}")
except Exception as e:
    raise RuntimeError(f"❌ [Tools] No se pudo crear el motor de la base de datos: {e}")


class ExecuteSQLQueryInput(BaseModel): 
    sql_query: str

class ExecuteSQLQueryOutput(BaseModel):
    results: list | str | None = None
    error: str | None = None

    def to_json(self):
        return self.model_dump_json(exclude_none=True)


def execute_sql_query(inputs: ExecuteSQLQueryInput) -> ExecuteSQLQueryOutput:
    """
    Ejecuta una consulta SQL SELECT en la base de datos PostgreSQL y devuelve los resultados.
    IMPORTANTE: Solo se permiten consultas SELECT.
    La consulta debe ser sintácticamente correcta para PostgreSQL.
    """
    query = inputs.sql_query.strip()
    print(f"🚀 [Tools] Intentando ejecutar SQL en PostgreSQL: {query}")

    parsed = sqlparse.parse(query)
    if not parsed or parsed[0].get_type() != 'SELECT':
        error_msg = "Error de seguridad: Solo se permiten consultas SELECT."
        print(f"🚨 [Tools] {error_msg}")
        return ExecuteSQLQueryOutput(error=error_msg)
    
    try:

        with engine.connect() as connection:
            result = connection.execute(text(query))
            
            if result.returns_rows:
                # _mapping = fila a diccionario
                result_data = [dict(row._mapping) for row in result]
                print(f"✅ [Tools] Resultados de la consulta: {result_data}")
                if not result_data:
                    return ExecuteSQLQueryOutput(results="La consulta se ejecutó correctamente, pero no se encontraron resultados.")
            else:
                result_data = "La consulta se ejecutó correctamente pero no devuelve filas (ej. una operación que no retorna datos)."
                print(f"ℹ️ [Tools] {result_data}")
            
            return ExecuteSQLQueryOutput(results=result_data)
        
    except exc.SQLAlchemyError as e:
        
        error_msg = f"Error de base de datos (SQLAlchemy): {e}"
        print(f"❌ [Tools] {error_msg}")
        return ExecuteSQLQueryOutput(error=error_msg)
    
    except Exception as e:
        error_msg = f"Error inesperado al ejecutar la consulta: {e}"
        print(f"❌ [Tools] {error_msg}")

        return ExecuteSQLQueryOutput(error=error_msg)

if __name__ == "__main__":

    print("\n--- Probando la conexión a PostgreSQL ---")
    
    test_input_valid = ExecuteSQLQueryInput(
        sql_query="SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"
    )
    output_valid = execute_sql_query(test_input_valid)
    print("\n--- Test Consulta Válida (Listar Tablas) ---")
    if output_valid.error:
        print(f"Error: {output_valid.error}")
    else:
        print(f"Resultados: {output_valid.results}")

    test_input_invalid = ExecuteSQLQueryInput(sql_query="DROP TABLE app_user;")
    output_invalid = execute_sql_query(test_input_invalid)
    print("\n--- Test Consulta Inválida (DROP) ---")
    if output_invalid.error:
        print(f"Error: {output_invalid.error}")
    else:
        print(f"Resultados: {output_invalid.results}")

    test_input_syntax_error = ExecuteSQLQueryInput(sql_query="SELEKT * FROM non_existent_table;")
    output_syntax_error = execute_sql_query(test_input_syntax_error)
    print("\n--- Test Consulta con Error de Sintaxis ---")
    if output_syntax_error.error:
        print(f"Error: {output_syntax_error.error}")
    else:
        print(f"Resultados: {output_syntax_error.results}")
