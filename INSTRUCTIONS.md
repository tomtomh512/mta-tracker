python -m venv venv

venv\Scripts\activate

source venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload

