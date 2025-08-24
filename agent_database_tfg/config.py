from dotenv import load_dotenv
import os

load_dotenv() 
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY")
DATABASE_PATH = os.getenv("DATABASE_PATH") 

MODEL_ID1 = "gemini/gemini-1.5-flash-latest" 
MODEL_ID = "gemini/gemini-2.5-flash-preview-05-20" 

