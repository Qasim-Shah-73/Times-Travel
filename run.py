from app import create_app, db
from app.models import User, Hotel, Room

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Hotel': Hotel, 'Room': Room}

if __name__ == "__main__":
    app.run(debug=True)
