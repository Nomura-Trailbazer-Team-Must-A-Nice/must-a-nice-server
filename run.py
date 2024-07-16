from application.app import create_app
from config import BaseConfig

config = BaseConfig

app, _ = create_app(config)
if __name__ == '__main__':
    app.run(debug=True, port=5000)
