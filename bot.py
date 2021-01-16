import os
import codecs
from bs4 import BeautifulSoup
from konlpy.tag import Okt
import urllib.request
import os, re, json, random
import discord
from discord.ext import commands
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

#네이버 맞춤법 검사 요청에 user-agent 헤더 추가
import requests

dict_file = "chatbot-data.json"
dic = {}


# 마르코프 체인 딕셔너리 만들기 --- (※1)
def make_dic(words):
    tmp = ["@"]
    dic = {}
    for word in words:
        tmp.append(word)
        if len(tmp) < 3: continue
        if len(tmp) > 3: tmp = tmp[1:]
        set_word3(dic, tmp)
        if word == ".":
            tmp = ["@"]
            continue
    return dic
def register_dic(words):
    global dic
    if len(words) == 0: return
    tmp = ["@"]
    for i in words:
        word = i[0]
        if word == "" or word == "\r\n" or word == "\n": continue
        tmp.append(word)
        if len(tmp) < 3: continue
        if len(tmp) > 3: tmp = tmp[1:]
        set_word3(dic, tmp)
        if word == "." or word == "?":
            tmp = ["@"]
            continue
    json.dump(dic, open(dict_file, "w", encoding="utf-8"))
# 딕셔너리에 데이터 등록하기 --- (※2)
def set_word3(dic, s3):
    w1, w2, w3 = s3
    if not w1 in dic: dic[w1] = {}
    if not w2 in dic[w1]: dic[w1][w2] = {}
    if not w3 in dic[w1][w2]: dic[w1][w2][w3] = 0
    dic[w1][w2][w3] += 1
# 문장 만들기 --- (※3)
def make_sentence(head):
    if not head in dic: return ""
    ret = []
    if head != "@": ret.append(head)
    top = dic[head]
    w1 = word_choice(top)
    w2 = word_choice(top[w1])
    ret.append(w1)
    ret.append(w2)
    while True:
        try:
            w3 = word_choice(dic[w1][w2])
            ret.append(w3)
        except:
            w3 = "."
        if w3 == ".": break
        w1, w2 = w2, w3
    ret = "".join(ret)
    # 띄어쓰기
    params = urllib.parse.urlencode({
        "_callback": "",
        "q": ret
    })
    # 네이버 맞춤법 검사기를 사용합니다.
    data = urllib.request.urlopen("https://m.search.naver.com/p/csearch/ocontent/spellchecker.nhn?" + params)
    data = data.read().decode("utf-8")[1:-2]
    data = json.loads(data)
    data = data["message"]["result"]["html"]
    data = soup = BeautifulSoup(data, "html.parser").getText()
    # 리턴
    return data

def word_choice(sel):
    keys = sel.keys()
    return random.choice(list(keys))

def make_reply(text):   
    if not text[-1] in [".","?"]: text += "."
    try:
        okt = Okt()
    except Exception as e:
        print(e)
    words = okt.pos(text)
    register_dic(words)
    for word in words:
        face = word[0]
        if face in dic: 
             return make_sentence(face)
    return make_sentence("@")

def sendEmail():
    try:
        smtp = smtplib.SMTP('smtp.gmail.com', 587)
        smtp.ehlo()     
        smtp.starttls()  
        smtp.login('MAIL (FROM)', 'GOOGLE ACCOUNT APP PASSWORD')
        
        # msg = MIMEText(str(dic))   
        msg = MIMEMultipart("alternative")
        f = codecs.open(dict_file, "r", "utf-8")
        attachment = MIMEText(f.read())
        attachment.add_header('Content-Disposition', 'attachment', filename=dict_file)
        msg.attach(attachment)     
        msg['Subject'] = 'chatbot data json file'
        msg['To'] = 'yumehamakei@gmail.com'
        smtp.sendmail('MAIL (FROM)', 'MAIL (TO)', msg.as_string())
        print("출력완료")
        smtp.quit()
    except Exception as e:
        print(e)


# 문장 읽어 들이기 --- (※4)
if not os.path.exists(dict_file):
    # 토지 텍스트 파일 읽어 들이기
    fp = codecs.open("BEXX0003.txt", "r", encoding="utf-16")
    soup = BeautifulSoup(fp, "html.parser")
    body = soup.select_one("body > text")
    text = body.getText()
    text = text.replace("…", "") # 현재 koNLPy가 …을 구두점으로 잡지 못하는 문제 임시 해결
    # 형태소 분석
    okt = Okt()
    
    malist = okt.pos(text, norm=True)
    words = []
    for word in malist:
        # 구두점 등은 대상에서 제외(단 마침표는 포함)
        if not word[1] in ["Punctuation"]:
            words.append(word[0])
        if word[0] == ".":
            words.append(word[0])
    # 딕셔너리 생성
    dic = make_dic(words)
    json.dump(dic, open(dict_file,"w", encoding="utf-8"))
else:
    dic = json.load(open(dict_file,"r", encoding="utf-8"))   


client = commands.Bot(command_prefix='.')

@client.event
async def on_ready():
    print("Bot is ready.")

@client.event
async def on_message(message):
    msg = message.content
    try:
        if(msg[0:3] == "!! "): 
            msg = msg[3:]
            new_msg = make_reply(msg)
            print(new_msg)
            await message.channel.send(new_msg)     
        elif(msg[0:2] == "!p"):
            pass
        elif(msg[0:1] == "!"):
            await message.channel.send("나 부른 고야? (사용법: !! [보낼 메세지])")       
        elif(msg == "yumehama bot! export json file"): 
            sendEmail()
        else:
            new_msg = make_reply(msg)

    except:
        print()

client.run('BOT_ID')
