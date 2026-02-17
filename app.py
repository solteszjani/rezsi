from flask import Flask, render_template, request, send_file
import sqlite3
import datetime
from fpdf import FPDF
import os  # Render porthoz

app = Flask(__name__)
DATABASE = "database.db"

# Rezsi limitek és árak
WATER_LIMIT = 5       # m3
GAS_LIMIT = 144       # m3
ELECTRIC_LIMIT = 210  # kWh

WATER_PRICE_LIMIT = 600
WATER_PRICE_NORMAL = 800
GAS_PRICE_LIMIT = 102
GAS_PRICE_NORMAL = 747
ELECTRIC_PRICE_LIMIT = 36
ELECTRIC_PRICE_NORMAL = 70

BASE_FEE_WATER = 500
BASE_FEE_GAS = 800
BASE_FEE_ELECTRIC = 900


def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS water_bills(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        previous REAL,
        current REAL,
        usage REAL,
        total REAL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS gas_bills(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        previous REAL,
        current REAL,
        usage REAL,
        total REAL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS electric_bills(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        previous REAL,
        current REAL,
        usage REAL,
        total REAL
    )""")
    conn.commit()
    conn.close()


init_db()


def calculate_limit_detailed(amount, limit, price_limit, price_normal, base_fee):
    if amount <= limit:
        discounted_usage = amount
        normal_usage = 0
    else:
        discounted_usage = limit
        normal_usage = amount - limit
    discounted_cost = discounted_usage * price_limit
    normal_cost = normal_usage * price_normal
    total = discounted_cost + normal_cost + base_fee
    return {
        "usage": amount,
        "discounted_usage": discounted_usage,
        "normal_usage": normal_usage,
        "price_limit": price_limit,
        "price_normal": price_normal,
        "discounted_cost": discounted_cost,
        "normal_cost": normal_cost,
        "base_fee": base_fee,
        "total": total
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/water")
def water():
    return render_template("water.html")


@app.route("/gas")
def gas():
    return render_template("gas.html")


@app.route("/electric")
def electric():
    return render_template("electric.html")


@app.route("/calculate_water", methods=["POST"])
def calculate_water():
    prev = request.form.get("previous")
    curr = request.form.get("current")

    if not prev or not curr:
        return render_template("error.html", message="Kérjük, adjon meg minden adatot a számításhoz!")

    try:
        prev = float(prev)
        curr = float(curr)
    except ValueError:
        return render_template("error.html", message="Az adatoknak számoknak kell lenniük!")

    usage = curr - prev
    data = calculate_limit_detailed(
        usage, WATER_LIMIT, WATER_PRICE_LIMIT, WATER_PRICE_NORMAL, BASE_FEE_WATER)

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    date = datetime.datetime.now().strftime("%Y-%m")
    c.execute("INSERT INTO water_bills(date, previous, current, usage, total) VALUES(?,?,?,?,?)",
              (date, prev, curr, usage, data["total"]))
    conn.commit()
    conn.close()

    return render_template("result_water.html", data=data)


@app.route("/calculate_gas", methods=["POST"])
def calculate_gas():
    prev = request.form.get("previous")
    curr = request.form.get("current")

    if not prev or not curr:
        return render_template("error.html", message="Kérjük, adjon meg minden adatot a számításhoz!")

    try:
        prev = float(prev)
        curr = float(curr)
    except ValueError:
        return render_template("error.html", message="Az adatoknak számoknak kell lenniük!")

    usage = curr - prev
    data = calculate_limit_detailed(
        usage, GAS_LIMIT, GAS_PRICE_LIMIT, GAS_PRICE_NORMAL, BASE_FEE_GAS)

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    date = datetime.datetime.now().strftime("%Y-%m")
    c.execute("INSERT INTO gas_bills(date, previous, current, usage, total) VALUES(?,?,?,?,?)",
              (date, prev, curr, usage, data["total"]))
    conn.commit()
    conn.close()

    return render_template("result_gas.html", data=data)


@app.route("/calculate_electric", methods=["POST"])
def calculate_electric():
    prev = request.form.get("previous")
    curr = request.form.get("current")

    if not prev or not curr:
        return render_template("error.html", message="Kérjük, adjon meg minden adatot a számításhoz!")

    try:
        prev = float(prev)
        curr = float(curr)
    except ValueError:
        return render_template("error.html", message="Az adatoknak számoknak kell lenniük!")

    usage = curr - prev
    data = calculate_limit_detailed(
        usage, ELECTRIC_LIMIT, ELECTRIC_PRICE_LIMIT, ELECTRIC_PRICE_NORMAL, BASE_FEE_ELECTRIC)

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    date = datetime.datetime.now().strftime("%Y-%m")
    c.execute("INSERT INTO electric_bills(date, previous, current, usage, total) VALUES(?,?,?,?,?)",
              (date, prev, curr, usage, data["total"]))
    conn.commit()
    conn.close()

    return render_template("result_electric.html", data=data)


@app.route("/pdf/<type>/<int:id>")
def pdf(type, id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute(f"SELECT * FROM {type}_bills WHERE id=?", (id,))
    bill = c.fetchone()
    conn.close()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, f"{type.upper()} számla", ln=True)
    pdf.cell(200, 10, f"Fogyasztás: {bill[4]}", ln=True)
    pdf.cell(200, 10, f"Összesen: {bill[5]} Ft", ln=True)

    filename = f"{type}_{id}.pdf"
    pdf.output(filename)
    return send_file(filename, as_attachment=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render adja a portot
    app.run(host="0.0.0.0", port=port)
