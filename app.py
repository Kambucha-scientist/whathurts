from what_hurts import create_app
from what_hurts.extensions import db

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
