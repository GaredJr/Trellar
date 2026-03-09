from flask import Flask

app = Flask(__name__)

@app.route("/")
def forside():
    return "<h1>Forsiden</h1><p>Velkommen til min nettside!</p>"

@app.route("/om")
def om_oss():
    return "<h1>Om oss</h1><p>Vi er elever som laerer Flask.</p>"

@app.route("/kontakt")
def kontakt():
    return "<h1>Kontakt</h1><p>Send oss en e-post!</p>"

if __name__ == "__main__":
    app.run(debug=True)