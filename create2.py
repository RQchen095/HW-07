import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

doc = {
  "name": "張伊傑",
  "mail": "chang200601@gmail.com",
  "lab": 887
}

doc_ref = db.collection("靜宜資管").document("ycc")
doc_ref.set(doc)
