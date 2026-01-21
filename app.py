from flask import Flask, render_template, request, jsonify
import pandas as pd
import os

app = Flask(__name__)

df = None
PREVIEW_LIMIT = 200


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    global df

    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"})

    try:
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

    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print("Created by Tharun, Contact- 8688963486")
    app.run(host="0.0.0.0", port=port)
