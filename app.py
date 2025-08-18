from flask import Flask, render_template, request

app = Flask(__name__)

# Temporary menu data (later we'll move to a database)
MENU = [
    {"id": 1, "name": "Cheeseburger", "price": 8.99},
    {"id": 2, "name": "Margherita Pizza", "price": 12.50},
    {"id": 3, "name": "Caesar Salad", "price": 7.25},
    {"id": 4, "name": "Spaghetti Bolognese", "price": 11.00},
    {"id": 5, "name": "Coke", "price": 2.50},
    {"id": 6, "name": "Iced Tea", "price": 2.75},
    {"id": 7, "name": "Mix Combo Small", "price": 75.00}
]

@app.route("/")
def index():
    table_no = request.args.get("table", "")  # optional ?table=5
    return render_template("index.html", menu=MENU, table_no=table_no)

if __name__ == "__main__":
    app.run(debug=True)
