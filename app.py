from flask import Flask, render_template, request, jsonify
import pandas as pd
from rapidfuzz import fuzz
import os

app = Flask(__name__)

df = None
PREVIEW_LIMIT = 200


# ---------- UTIL ----------
def normalize(text):
    return str(text).lower().strip()


def exact_word_match(q_word, cell_text):
    q = normalize(q_word)
    words = normalize(cell_text).split()
    return q in words


def fuzzy_word_match(q_word, cell_text, threshold):
    q = normalize(q_word)
    words = normalize(cell_text).split()
    for w in words:
        if fuzz.partial_ratio(q, w) >= threshold:
            return True
    return False


def row_matches(query_words, row_cells, threshold):
    for qw in query_words:
        found = False
        for cell in row_cells:
            if threshold == 100:
                if exact_word_match(qw, cell):
                    found = True
            else:
                if fuzzy_word_match(qw, cell, threshold):
                    found = True
            if found:
                break
        if not found:
            return False
    return True


# ---------- ROUTES ----------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    global df

    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"})

    if file.filename.lower().endswith(".csv"):
        df = pd.read_csv(file, dtype=str)
    else:
        df = pd.read_excel(file, dtype=str)

    df.fillna("", inplace=True)

    preview = df.head(PREVIEW_LIMIT).to_dict(orient="records")

    return jsonify({
        "total": len(df),
        "preview": preview
    })


@app.route("/search", methods=["POST"])
def search():
    global df
    if df is None:
        return jsonify({"count": 0, "rows": []})

    data = request.json
    query = data.get("query", "").strip()
    relation = data.get("relation", "").strip()
    threshold = int(data.get("threshold", 70))

    if not query:
        return jsonify({"count": 0, "rows": []})

    name_words = normalize(query).split()
    rel_words = normalize(relation).split() if relation else []

    results = []

    for _, row in df.iterrows():
        row_cells = [str(v) for v in row.values]

        if not row_matches(name_words, row_cells, threshold):
            continue

        if rel_words and not row_matches(rel_words, row_cells, threshold):
            continue

        results.append(row.to_dict())

    return jsonify({
        "count": len(results),
        "rows": results
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print("Created by Tharun, Contact- 8688963486")
    app.run(host="0.0.0.0", port=port)
