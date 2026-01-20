from flask import Flask, render_template, request, jsonify
import pandas as pd
from rapidfuzz import fuzz

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


def words_match(q_words, row_cells, threshold):
    """
    All query words must match somewhere in the row
    Returns (bool, matched_words_set)
    """
    matched = set()

    for qw in q_words:
        found = False
        for cell in row_cells:
            for w in normalize(cell).split():
                if threshold == 100:
                    ok = (qw == w)
                else:
                    ok = fuzz.partial_ratio(qw, w) >= threshold

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

    return jsonify({
        "total": len(df),
        "preview": preview
    })


@app.route("/search", methods=["POST"])
def search():
    global df
    if df is None:
        return jsonify([])

    data = request.json
    name_query = data.get("query", "").strip()
    relation_query = data.get("relation", "").strip()
    threshold = int(data.get("threshold", 70))

    if not name_query:
        return jsonify([])

    name_words = normalize(name_query).split()
    relation_words = normalize(relation_query).split() if relation_query else []

    results = []

    for _, row in df.iterrows():
        row_cells = [str(v) for v in row.values]

        # ---- NAME MATCH ----
        ok_name, matched_words = words_match(name_words, row_cells, threshold)
        if not ok_name:
            continue

        # ---- RELATION MATCH (OPTIONAL) ----
        if relation_words:
            ok_rel, rel_matched = words_match(relation_words, row_cells, threshold)
            if not ok_rel:
                continue
            matched_words |= rel_matched

        r = row.to_dict()
        r["_matched"] = list(matched_words)
        results.append(r)

    return jsonify(results)


import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print("Created by Tharun, Contact- 8688963486")
    app.run(host="0.0.0.0", port=port)
