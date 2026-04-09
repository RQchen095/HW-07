import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

doc = {
  "name": "楊子青",
  "mail": "tcyang@pu.edu.tw",
  "lab": 579
}

doc_ref = db.collection("靜宜資管").document("tcyang")
doc_ref.set(doc)
