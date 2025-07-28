from flask import Flask
from app.routes import bp
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'app', 'templates'),
    static_folder=os.path.join(BASE_DIR, 'app', 'static')
)
app.secret_key = 'dev_secret_key'  # À changer en production
app.register_blueprint(bp)

if __name__ == '__main__':
    app.run(debug=True) 