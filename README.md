# Campus Help

A unified campus utility platform featuring five modules:

- `lost_found/`: FastAPI backend for reporting lost/found items and AI TF-IDF matching.
- `college_chat/`: Flask + Socket.IO chat app with student registration and admin approval.
- `campus_cab/`: Standalone cab booking page with vehicle listings and WhatsApp booking links.
- `campus_map/`: Interactive SVG map of VIT Bhopal with search, navigation, and location details.
- `static/chatbot.html`: AI Campus Assistant providing instant answers to student queries.

## Project Structure

```text
campus-help/
  campus_cab/
    cab.html
    *.jpeg
  campus_map/
    index.html
    styles.css
    app.js
    buildings-data.js
  college_chat/
    app.py
    chat_data.json
    requirements.txt
    templates/
  lost_found/
    database.py
    matcher.py
    models.py
    router.py
    schemas.py
  static/
    index.html
    lost-found.html
    cab.html
    chat.html
    map.html
    chatbot.html
  app.py
  chatbot.py
  main_integration_example.py
  requirements.txt
  run.bat
  Procfile
```

## Run The Website

Install dependencies from the project root:

```bash
pip install -r requirements.txt
```

Start the unified website:

```bash
python main_integration_example.py
```

Open:

```text
http://127.0.0.1:8000
```

## Direct Module URLs

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/lost-found.html
http://127.0.0.1:8000/cab.html
http://127.0.0.1:8000/chat.html
http://127.0.0.1:8000/map.html
http://127.0.0.1:8000/chatbot.html
```

## Run College Chat Directly

You can still run the chat app by itself from the `college_chat` folder:

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Notes

- `college_chat` remains a separate Flask-SocketIO app so its realtime chat behavior stays intact.
- `static/chat.html` embeds the running chat app inside the unified website.
- Runtime/generated files such as `__pycache__/` and `lost_found.db` are ignored by Git.
