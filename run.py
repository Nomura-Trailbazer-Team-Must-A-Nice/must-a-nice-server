from application.app import create_app
from dotenv import load_dotenv
from config import BaseConfig

config = BaseConfig

load_dotenv()

app, _ = create_app(config)
if __name__ == '__main__':
    app.run(debug=True)
