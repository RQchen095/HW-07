from flask import Flask, render_template, request
from datetime import datetime
import os
import math

import json
import firebase_admin
from firebase_admin import credentials, firestore

import requests
from bs4 import BeautifulSoup

# 判斷是在 Vercel 還是本地
if os.path.exists('serviceAccountKey.json'):
    # 本地環境：讀取檔案
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    # 雲端環境：從環境變數讀取 JSON 字串
    firebase_config = os.getenv('FIREBASE_CONFIG')
    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)

firebase_admin.initialize_app(cred)
db = firestore.client()
app = Flask(__name__)

@app.route("/")
def index():
    link= "<h1>我的Python網頁</h1>"
    link+="<a href=/mis>課程</a><br><hr>"
    link+="<a href=/today>今天日期時間</a><br><hr>"
    link+="<a href=/me>我的網頁</a><br><hr>"
    link+="<a href=/welcome?u=ycc&d=靜宜資管&c=資訊管理導論>Get傳值</a><br><hr>"
    link+="<a href=/account>POST傳值</a><br><hr>"
    link+="<a href=/count>次方與根號計算</a><br><hr>"    
    link+="<br><a href=/read>讀取Firestore資料</a><br><hr>"
    link+="<a href=/search>找老師</a><br><hr>"    
    link+="<br><a href=/teacher>爬老師課程</a><br><hr>"
    link+="<br><a href=/movie>爬電影</a><br><hr>"
    return link

@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><a href=/>返回首頁</a>"

@app.route("/today")
def today():
    now = datetime.now()
    return render_template("today.html", datetime = str(now))

@app.route("/me")
def me():
    now = datetime.now()
    return render_template("MIS2B411316337.html", datetime = str(now))

@app.route("/welcome", methods=["GET"])
def welcome():
    user = request.values.get("u")
    d= request.values.get("d")
    c= request.values.get("c")   
    return render_template("welcome.html", name=user,dep=d,course=c)

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        result = "您輸入的帳號是：" + user + "; 密碼為：" + pwd 
        return result
    else:
        return render_template("account.html")

@app.route("/count")
def count():
    return render_template("count.html")        

@app.route("/read")
def read():
    Result = ""
    db = firestore.client()
    collection_ref = db.collection("py")    
    docs = collection_ref.get()    
    for doc in docs:         
        Result += str(doc.to_dict()) + "<br>"    
    return Result

@app.route("/search", methods=["GET", "POST"])
def search():
    results = []
    keyword = ""
    if request.method == "POST":
        keyword = request.form.get("keyword", "").strip()
        if keyword:
            collection_ref = db.collection("靜宜資管")
            docs = collection_ref.get()
            for doc in docs:
                teacher = doc.to_dict()
                if keyword in teacher.get("name", ""):
                    results.append(teacher)
    return render_template("search.html", results=results, keyword=keyword)

@app.route("/teacher")
def teacher():
    import requests
    from bs4 import BeautifulSoup

    url = "https://www1.pu.edu.tw/~tcyang/course.html"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    }
   
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        result = ""
        seen = set()
        for a in soup.select("a"):
            href = a.get("href", "")
            name = a.get_text(strip=True)
            if "drive.google.com" in href and href not in seen:
                seen.add(href)
                result += name + href + "<br>"

        if result == "":
            result = "抓不到課程資料"
    except Exception as e:
        result = "錯誤：" + str(e)

    return result + "<br><a href=/>返回首頁</a>"

@app.route("/movie")
def movie():
    url = "https://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url)
    R = ""
    sp = BeautifulSoup(Data.text, "html.parser")
    result=sp.select(".filmListAllX li")
    info = ""
    for item in result:
        R+=item.find("img").get("alt")+"<br>"
        R+="https://www.atmovies.com.tw/movie/next/"+item.find("a").get("href")+"<br>"
        R+="https://www.atmovies.com.tw/movie/next/"+item.find("img").get("src")+"<br><br>"
    return R


if __name__ == "__main__":
    app.run(debug=True)