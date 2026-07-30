# Campus Help

A campus utility project with one main website and three current modules:

- `lost_found/`: FastAPI backend for reporting lost/found items and finding possible matches.
- `static/`: Unified website pages.
- `college_chat/`: Flask + Socket.IO chat app with student registration and admin approval.
- `campus_cab/`: Standalone cab booking page with local vehicle images and WhatsApp booking links.

## Project Structure

```text
campus-help/
  campus_cab/
    cab.html
    *.jpeg
  college_chat/
    app.py
    chat_data.json
    requirements.txt
    static/
      socket.io.min.js
    templates/
      admin.html
      base.html
      chat.html
      login.html
      register.html
  lost_found/
    __init__.py
    database.py
    matcher.py
    models.py
    requirements.txt
    router.py
    schemas.py
  static/
    cab.html
    chat.html
    index.html
    lost-found.html
  main_integration_example.py
  requirements.txt
  run.bat
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

This starts the FastAPI website on port `8000`. It also starts the existing College Chat app on port `5000` if it is not already running, then embeds it inside the website at:

```text
http://127.0.0.1:8000/chat.html
```

## Direct Module URLs

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/lost-found.html
http://127.0.0.1:8000/cab.html
http://127.0.0.1:8000/chat.html
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
