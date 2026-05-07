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
    # 本地環境:讀取檔案
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    # 雲端環境:從環境變數讀取 JSON 字串
    firebase_config = os.getenv('FIREBASE_CONFIG')
    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)

firebase_admin.initialize_app(cred)
db = firestore.client()
app = Flask(__name__)

@app.route("/")
def index():
    link = "<h1>我的Python網頁</h1>"
    link += "<a href=/mis>課程</a><br><hr>"
    link += "<a href=/today>今天日期時間</a><br><hr>"
    link += "<a href=/me>我的網頁</a><br><hr>"
    link += "<a href=/welcome?u=ycc&d=靜宜資管&c=資訊管理導論>Get傳值</a><br><hr>"
    link += "<a href=/account>POST傳值</a><br><hr>"
    link += "<a href=/count>次方與根號計算</a><br><hr>"
    link += "<a href=/read>讀取Firestore資料</a><br><hr>"
    link += "<a href=/search>找老師</a><br><hr>"
    link += "<a href=/teacher>爬老師課程</a><br><hr>"
    link += "<a href=/spiderMovie>爬蟲存進資料庫</a><br><hr>"
    link += "<a href=/movie>查詢電影</a><br><hr>"
    link += "<a href=/road>台中市被撞排行榜</a><br><hr>"
    link += "<a href=/weather>隨機欺負沒帶雨傘的人</a><br><hr>"
    return link

@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><a href=/>返回首頁</a>"

@app.route("/today")
def today():
    now = datetime.now()
    return render_template("today.html", datetime=str(now))

@app.route("/me")
def me():
    now = datetime.now()
    return render_template("MIS2B411316337.html", datetime=str(now))

@app.route("/welcome", methods=["GET"])
def welcome():
    user = request.values.get("u")
    d = request.values.get("d")
    c = request.values.get("c")
    return render_template("welcome.html", name=user, dep=d, course=c)

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        result = "您輸入的帳號是:" + user + "; 密碼為:" + pwd
        return result
    else:
        return render_template("account.html")

@app.route("/count")
def count():
    return render_template("count.html")

@app.route("/read")
def read():
    Result = ""
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
        result = "錯誤:" + str(e)

    return result + "<br><a href=/>返回首頁</a>"


@app.route("/spiderMovie")
def spiderMovie():
    url = "https://www.atmovies.com.tw/movie/next/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = "utf-8"
        sp = BeautifulSoup(resp.text, "html.parser")
        items = sp.select(".filmListAllX li")

        # 先清掉舊資料
        movies_ref = db.collection("movies")
        for old in movies_ref.stream():
            old.reference.delete()

        all_movies = []
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for idx, item in enumerate(items, start=1):
            img_tag = item.find("img")
            a_tag = item.find("a")
            if not img_tag or not a_tag:
                continue

            name = img_tag.get("alt", "").strip()
            href = a_tag.get("href", "")
            src = img_tag.get("src", "")

            # 抓上映日期
            date_text = ""
            date_tag = item.select_one(".runtime")
            if date_tag:
                date_text = date_tag.get_text(strip=True)
            else:
                full_text = item.get_text(" ", strip=True)
                if "上映日期" in full_text:
                    date_text = full_text.split("上映日期")[-1].strip(":: ")[:20]
                else:
                    date_text = full_text[-15:]

            movie_data = {
                "id": idx,
                "name": name,
                "img": src if src.startswith("http") else "https:" + src,
                "url": "https://www.atmovies.com.tw" + href,
                "release_date": date_text,
                "updated_at": now_str
            }

            movies_ref.document(str(idx)).set(movie_data)
            all_movies.append(movie_data)

        count = len(all_movies)

        # 存 meta 資訊
        db.collection("meta").document("spider_info").set({
            "last_updated": now_str,
            "total": count
        })

        # 用 template 顯示結果(含全部電影列表)
        return render_template(
            "spider_result.html",
            last_updated=now_str,
            total=count,
            results=all_movies
        )

    except Exception as e:
        return f"錯誤:{str(e)}<br><a href=/>返回首頁</a>"
    
@app.route("/movie", methods=["GET", "POST"])
def movie():
    keyword = ""
    results = []

    # 讀取更新資訊
    meta_doc = db.collection("meta").document("spider_info").get()
    if meta_doc.exists:
        meta = meta_doc.to_dict()
        last_updated = meta.get("last_updated", "尚未爬取")
        total = meta.get("total", 0)
    else:
        last_updated = "尚未爬取"
        total = 0

    # 從資料庫讀全部電影
    movies_ref = db.collection("movies")
    docs = movies_ref.stream()
    all_movies = [doc.to_dict() for doc in docs]
    all_movies.sort(key=lambda m: m.get("id", 0))

    if request.method == "POST":
        keyword = request.form.get("keyword", "").strip()
        if keyword:
            results = [m for m in all_movies if keyword in m.get("name", "")]
        else:
            results = all_movies   # POST 但留空 → 全部

    return render_template(
        "movie.html",
        keyword=keyword,
        results=results,
        last_updated=last_updated,
        total=total
    )

import urllib3
import requests, json

# 關閉 SSL 警告(因為政府網站憑證有問題)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import urllib3
import requests, json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@app.route("/road")
def road():
    R = "<h1>台中市被撞排行榜_by陳若綺</h1><br>"
    url = "https://datacenter.taichung.gov.tw/swagger/OpenData/a1b899c0-511f-4e3d-b22b-814982a97e41"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        Data = requests.get(url, headers=headers, timeout=10, verify=False)
        JsonData = Data.json()
    except Exception as e:
        return f"<h1>抓取失敗</h1><p>{e}</p><pre>{Data.text[:500] if 'Data' in dir() else ''}</pre>"
    
    for item in JsonData:
        R += f"{item['路口名稱']} 原因:{item['主要肇因']} 共 {item['總件數']} 件<br>"
    
    return R

from flask import request

@app.route("/weather", methods=["GET", "POST"])
def weather():
    # 表單頁面
    form = """
    <h1>縣市天氣查詢</h1>
    <form method="POST">
        <input type="text" name="city" placeholder="例如:臺中市" required>
        <button type="submit">查詢</button>
    </form>
    <p>支援格式:臺北市、新北市、臺中市、臺南市、高雄市、桃園市、基隆市、新竹市、嘉義市、新竹縣、苗栗縣、彰化縣、南投縣、雲林縣、嘉義縣、屏東縣、宜蘭縣、花蓮縣、臺東縣、澎湖縣、金門縣、連江縣</p>
    """
    
    if request.method == "GET":
        return form
    
    # POST: 處理查詢
    city = request.form.get("city", "").strip()
    
    # 自動把「台」轉成「臺」(API 用的是正體字)
    city = city.replace("台", "臺")
    
    # 中央氣象署 API(這是公開的授權碼,建議自己申請)
    auth = "CWA-A397F196-58FF-447A-AF7A-67A4290AFC35"  # 換成你自己的
    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"
    params = {
        "Authorization": auth,
        "locationName": city
    }
    
    try:
        resp = requests.get(url, params=params, timeout=10, verify=False)  # ← 加 verify=False
        data = resp.json()
    except Exception as e:
        return form + f"<p style='color:red'>抓取失敗:{e}</p>"
    
    # 檢查有沒有資料
    locations = data.get("records", {}).get("location", [])
    if not locations:
        return form + f"<p style='color:red'>找不到「{city}」的資料,請檢查縣市名稱</p>"
    
    loc = locations[0]
    R = f"<h1>{loc['locationName']} 天氣預報</h1>"
    
    # 把資料整理成字典: {要素名稱: [時段資料]}
    elements = {e["elementName"]: e["time"] for e in loc["weatherElement"]}
    
    # 三個時段(每段 12 小時)
    R += "<table border='1' cellpadding='8' style='border-collapse:collapse'>"
    R += "<tr><th>時段</th><th>天氣</th><th>溫度</th><th>降雨機率</th><th>舒適度</th></tr>"
    
    for i in range(len(elements["Wx"])):
        start = elements["Wx"][i]["startTime"]
        end = elements["Wx"][i]["endTime"]
        wx = elements["Wx"][i]["parameter"]["parameterName"]
        pop = elements["PoP"][i]["parameter"]["parameterName"]
        min_t = elements["MinT"][i]["parameter"]["parameterName"]
        max_t = elements["MaxT"][i]["parameter"]["parameterName"]
        ci = elements["CI"][i]["parameter"]["parameterName"]
        
        R += f"<tr><td>{start}<br>~{end}</td><td>{wx}</td><td>{min_t}~{max_t}°C</td><td>{pop}%</td><td>{ci}</td></tr>"
    
    R += "</table>"
    R += '<br><a href="/weather">重新查詢</a>'
    return R

if __name__ == "__main__":
    app.run(debug=True)