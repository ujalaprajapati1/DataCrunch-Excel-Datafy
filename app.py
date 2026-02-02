import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "super_secret_key"

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"csv", "xlsx"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files.get("file")

    if not file or file.filename == "":
        return redirect(url_for("index"))

    if not allowed_file(file.filename):
        return redirect(url_for("index"))

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(file_path)

    session["uploaded_file"] = file_path
    session.pop("selected_column", None)

    return redirect(url_for("dashboard"))


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    file_path = session.get("uploaded_file")

    if not file_path:
        return render_template("dashboard.html", error="No file uploaded")

    # Read file
    try:
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
    except Exception:
        return render_template("dashboard.html", error="Unable to read file")

    if df.empty:
        return render_template("dashboard.html", error="Dataset is empty")

    # Preview table (first 10 rows)
    table_html = df.head(10).to_html(
        classes="table",
        index=False,
        border=0
    )

    # Detect numeric columns
    numeric_columns = df.select_dtypes(include="number").columns.tolist()

    if not numeric_columns:
        return render_template(
            "dashboard.html",
            table=table_html,
            error="No numeric columns found"
        )

    # Stats column selection (for cards)
    if request.method == "POST" and "column" in request.form:
        selected_column = request.form.get("column")
        session["selected_column"] = selected_column
    else:
        selected_column = session.get("selected_column", numeric_columns[0])

    if selected_column not in numeric_columns:
        selected_column = numeric_columns[0]

    col_data = df[selected_column].dropna()

    stats = {
        "mean": round(col_data.mean(), 2),
        "median": round(col_data.median(), 2),
        "min": round(col_data.min(), 2),
        "max": round(col_data.max(), 2),
    }

    # 🔥 FULL DATA FOR CHART (IMPORTANT)
    full_data = df[numeric_columns].dropna().to_dict(orient="records")

    return render_template(
        "dashboard.html",
        table=table_html,
        numeric_columns=numeric_columns,
        selected_column=selected_column,
        stats=stats,
        full_data=full_data
    )


if __name__ == "__main__":
    app.run(debug=True)
