from flask import Flask

app = Flask(__name__)

@app.route("/")
def forside():
    return "<h1>Hei, verden!</h1><p>Min forste Flask-app!</p>"

if __name__ == "__main__":
    app.run(debug=True)