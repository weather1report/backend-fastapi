py -m venv .venv

.venv\Scripts\activate.bat

pip install -r requirements.txt

fastapi dev main.py
fastapi run main.py