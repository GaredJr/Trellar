# Kommandobruk og Referanser
Kommandoer brukt og referanser.

## Python Flask
```
python3 -m venv venv
source venv/bin/activate
```


## Dependencies
```
pip install flask
python -c "import flask; print(flask.__version__)"
```


## References
```
@app.route("/hils/<navn>")
def hils(navn):
    return f"<h1>Hei, {navn}!</h1>"


@app.route("/kvadrat/<int:tall>")
def kvadrat(tall):
    resultat = tall ** 2
    return f"<p>{tall} i annen er {resultat}</p>"
```