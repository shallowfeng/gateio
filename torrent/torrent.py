import requests  
import re  
from bs4 import BeautifulSoup  
        
url="http://www.btanf.com"  
header={  
    "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",  
    "Accept-Encoding":"gzip, deflate",  
    "Accept-Language":"zh-CN,zh;q=0.8",  
    "Cache-Control":"max-age=0",  
    "Connection":"keep-alive",  
    "Content-Length":"65",  
    "Content-Type":"application/x-www-form-urlencoded",  
    "Host":"btkitty.bid",  
    "Origin":url,  
    "Referer":url,  
    "Upgrade-Insecure-Requests":"1",  
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0.14393; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2950.5 Safari/537.36"  
    }  
while True:  
    word=input("输入搜索关键词:")  
    data={  
        "keyword":word,  
        "hidden":"true"  
        }  
    res=requests.post(url,data=data,headers=header)  
    bs=BeautifulSoup(res.text,"lxml")  
    itemInfo=bs.find_all("dd",class_="option")  
    torrent={}  
    for item in itemInfo:  
        magnet=item.find_next("a",href=re.compile("magnet.*")).attrs["href"]  
        name=item.find_previous("a",href=re.compile("http://www.btanf.com/.*\.html")).text
        size=item.find_next(text=re.compile("\u6587\u4ef6\u5927\u5c0f")).find_next("b").text  
        time=item.find_next(text=re.compile("\u6536\u5f55\u65f6\u95f4")).find_next("b").text  
        hot=item.find_next(text=re.compile("\u4eba\u6c14")).find_next("b").text  
        torrent[name]=[name,time,size,hot,magnet]  
  
    for item in torrent:  
        print("名称：",torrent[item][0])  
        print("发布时间：",torrent[item][1])  
        print("大小：",torrent[item][2])  
        print("热度：",torrent[item][3])  
        print("磁力链接：",torrent[item][4],'\n')      