1. Create virtual environment:
   python -m venv .venv

2. Activate it:
   - On Linux/macOS: source .venv/bin/activate
   - On Windows: .venv\Scripts\activate

3. Install requirements:
   pip install -r requirements.txt

4. Apply migrations:
   python manage.py migrate

5. Create superuser:
   python manage.py createsuperuser

6. Run the server:
   python manage.py runserver
