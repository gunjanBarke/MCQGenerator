# test_env.py
from dotenv import load_dotenv
import os
load_dotenv()
print(os.getenv("GROQ_API_KEY"))   # should print your key