from firebase_functions import https_fn
from firebase_functions.options import set_global_options
from firebase_admin import initialize_app, firestore
from flask import jsonify
import google.cloud.firestore

set_global_options(max_instances=10)

initialize_app()

# ── Guardar dato del sensor ──────────────────
@https_fn.on_request()
def guardar(req: https_fn.Request) -> https_fn.Response:
    # Permitir CORS para que el HTML pueda llamar a esta función
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
    }

    if req.method == "OPTIONS":
        return https_fn.Response("", status=204, headers=headers)

    if req.method != "POST":
        return https_fn.Response("Método no permitido", status=405, headers=headers)

    try:
        data = req.get_json()
        valor = float(data.get("valor"))

        db = firestore.client()
        db.collection("lecturas").add({
            "valor": valor,
            "creado_en": firestore.SERVER_TIMESTAMP
        })

        return https_fn.Response("OK", status=200, headers=headers)
    except Exception as e:
        return https_fn.Response(f"Error: {e}", status=500, headers=headers)


# ── Obtener últimas lecturas ─────────────────
@https_fn.on_request()
def datos(req: https_fn.Request) -> https_fn.Response:
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
    }

    if req.method == "OPTIONS":
        return https_fn.Response("", status=204, headers=headers)

    try:
        db = firestore.client()
        docs = (
            db.collection("lecturas")
            .order_by("creado_en", direction=google.cloud.firestore.Query.DESCENDING)
            .limit(60)
            .stream()
        )

        lecturas = []
        for doc in docs:
            d = doc.to_dict()
            lecturas.append({
                "valor": d.get("valor"),
                "creado_en": d.get("creado_en").isoformat() if d.get("creado_en") else None
            })

        lecturas.reverse()
        import json
        return https_fn.Response(
            json.dumps(lecturas),
            status=200,
            headers={**headers, "Content-Type": "application/json"}
        )
    except Exception as e:
        return https_fn.Response(f"Error: {e}", status=500, headers=headers)