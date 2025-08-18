from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "👋 Table Order System is alive!"

if __name__ == "__main__":
    app.run(debug=True)