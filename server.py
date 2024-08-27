from flask import Flask
from routes.availability import availability_bp

app = Flask(__name__)

# Register blueprints
app.register_blueprint(availability_bp)

if __name__ == '__main__':
    app.run(debug=True)