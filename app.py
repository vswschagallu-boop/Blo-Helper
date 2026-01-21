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


def word_match(q_word, cell_text, threshold):
    q = normalize(q_word)
    for w in normalize(cell_text).split():
        if threshold == 100:
            if q == w:
                return True
        else:
            if fuzz.partial_ratio(q, w) >= threshold:
                return True
    return False


def row_match(words, cells, threshold):
    matched = set()
    for qw in words:
        found = False
        for cell in cells:
            for w in normalize(cell).split():
                ok = (qw == w) if threshold == 100 else fuzz.partial_ratio(qw, w) >= threshold
                if ok:
                    matched.add(w)
                    found = True
                    break
            if found:
                break
        if not found:
            return False, set()
    return True, matched


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
    columns = list(df.columns)

    return jsonify({
        "total": len(df),
        "preview": preview,
        "columns": columns
    })


@app.route("/search", methods=["POST"])
def search():
    global df
    if df is None:
        return jsonify({"count": 0, "rows": []})

    data = request.json
    name_text = data.get("name", "").strip()
    rel_text = data.get("relation", "").strip()
    name_col = data.get("name_col", "ALL")
    rel_col = data.get("rel_col", "ALL")
    name_fuzzy = int(data.get("name_fuzzy", 70))
    rel_fuzzy = int(data.get("rel_fuzzy", 70))

    name_words = normalize(name_text).split() if name_text else []
    rel_words = normalize(rel_text).split() if rel_text else []

    results = []

    for _, row in df.iterrows():
        # ---- NAME CELLS ----
        if name_col == "ALL":
            name_cells = [str(v) for v in row.values]
        else:
            name_cells = [str(row.get(name_col, ""))]

        ok_name, matched = row_match(name_words, name_cells, name_fuzzy) if name_words else (True, set())
        if not ok_name:
            continue

        # ---- RELATION CELLS ----
        if rel_words:
            if rel_col == "ALL":
                rel_cells = [str(v) for v in row.values]
            else:
                rel_cells = [str(row.get(rel_col, ""))]

            ok_rel, rel_matched = row_match(rel_words, rel_cells, rel_fuzzy)
            if not ok_rel:
                continue
            matched |= rel_matched

        r = row.to_dict()
        r["_matched"] = list(matched)
        results.append(r)

    return jsonify({
        "count": len(results),
        "rows": results
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print("Created by Tharun, Contact- 8688963486")
    app.run(host="0.0.0.0", port=port)
