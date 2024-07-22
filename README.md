# Nomura AI Challenge 2024 Backend

To run the server, install the requirements via `pip install -r requirements.txt` and call `python run.py`.

[Known issue on macOS](https://stackoverflow.com/questions/69818376/localhost5000-unavailable-in-macos-v12-monterey)

Testing agent in handle_user_prompt enpoint:

e.g.

```
curl -X POST http://localhost:5000/api/handle_user_prompt \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Please schedule a meeting with Nicholas"}'
```
