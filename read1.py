#根據文件id讀取一筆資料：read.py 
import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

doc_ref = db.document("py/bJSXv5WeyXEAwo4dtVe5")
doc = doc_ref.get()
result=doc.to_dict()
print(f"姓名:{result['name']}的研究室在{result['lab']}電子郵件為{result['mail']}")
#result = doc.to_dict()
#print("文件內容為：{}".format(result))
#print("教師姓名："+result.get("name"))
#print("教師郵件：" + result["mail"])
