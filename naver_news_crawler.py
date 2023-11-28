# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup 
import requests 
import re 
import pandas as pd
from datetime import datetime, timedelta
'''
댓글 크롤링(JSON 활용)
네트워크 F5
'''
# 네이버 뉴스 url
RESULT_PATH = '/Users/seohwiwon/Documents/py-crawler/'
    

def get_news_url(date):
    main_url = "https://news.naver.com/main/ranking/popularMemo.naver?date="+date
    #메인 주소에 접속후 랭킹 뉴스 url을 가져옴
    # url 의 형태 document.querySelectorAll("a[href*='https://n.news.naver.com/article']")
    # 중복된 url이 존재하므로 이를 제거해야 함
    response = requests.get(main_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    url_list = soup.select("a[href*='https://n.news.naver.com/article']")
    # 상위 20개의 url만 가져옴
    url_list = url_list[:40]
    # href 속성값을 가져옴
    url_list = [url['href'] for url in url_list]
    # 중복 url 제거
    url_list = list(set(url_list))
    print(date+"일에 "+str(len(url_list))+"개의 기사 url을 수집합니다.")
    return url_list

def contents_cleansing(contents):
    first_cleansing_contents = re.sub('<dl>.*?</a> </div> </dd> <dd>', '', 
                                      str(contents)).strip()  #앞에 필요없는 부분 제거
    second_cleansing_contents = re.sub('<ul class="relation_lst">.*?</dd>', '', 
                                       first_cleansing_contents).strip()#뒤에 필요없는 부분 제거 (새끼 기사)
    third_cleansing_contents = re.sub('<.+?>', '', second_cleansing_contents).strip()
    return third_cleansing_contents
def get_news_content(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    title_text = soup.select('#title_area')[0].text  #대괄호는 0번째 줄을 가져오라는 뜻

        
    #신문사 추출
    source_text = soup.select('.media_end_head_top_logo_img')[0].get('alt')
    
    
    #날짜 추출 
    date = soup.select('.media_end_head_info_datestamp_time')[0].get('data-date-time')
    
    #본문요약본
    contents_lists = soup.select('#dic_area')
    for contents_list in contents_lists:
        contents_text = contents_cleansing(contents_list) #본문요약 정제화
    

    #모든 리스트 딕셔너리형태로 저장
    result= { "title":title_text , "publishedAt":date,  "publisher" : source_text ,"description": contents_text ,"url":url }
    return result  

        
def excel_make(flatList,d_flatList): 
    result= {"comments":flatList, "date":d_flatList}
    df = pd.DataFrame(result)  #df로 변환
    df.to_excel(RESULT_PATH+"comments_results.xlsx",sheet_name='sheet1')


def get_comments(url):
    pattern = r'article/(\d+/\d+)'
    match = re.search(pattern, url)
    oid = match.group(1).split('/')[0]
    aid = match.group(1).split('/')[1]
    # check if oid and aid are valid
    if not oid or not aid:
        print('invalid url')
        return
    page = 1
    header = { 
        "User-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36", 
        "referer":url, 
         
    }
    comment_list = []
    while True :
        c_url = "https://apis.naver.com/commentBox/cbox/web_neo_list_jsonp.json?ticket=news&templateId=default_society&pool=cbox5&_callback=jQuery1707138182064460843_1523512042464&lang=ko&country=&objectId=news"+oid+"%2C"+aid+"&categoryId=&pageSize=20&indexSize=10&groupId=&listType=OBJECT&pageType=more&page="+str(page)+"&refresh=false&sort=FAVORITE"
        r= requests.get(c_url,headers=header)
        content = BeautifulSoup(r.content,"html.parser")
        total_comm=str(content).split('comment":')[1].split(",")[0]
        match=re.findall('"contents":"([^\*]*)","userIdNo"', str(content))
        comment_list += match
        if int(total_comm) <= ((page) * 20): 
            break 
        else :  
            page+=1
    return comment_list

def main():
    start_date = datetime(2023, 8, 14)
    end_date = datetime(2023, 11, 14)
    date_list = []
    c_list = []
    # Loop through the date range
    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date.strftime("%Y%m%d"))
        current_date += timedelta(days=1)
    for date in date_list:
        url_list = get_news_url(date)
        i_c = 0
        for url in url_list:
            print(date+"일의"+str(i_c)+"번째 기사입니다.")
            comments = get_comments(url)
            content = get_news_content(url)
            content.update({"comments":str(comments)})
            content.update({"comments_count":len(comments)})
            # create csv file
            c_list.append(content)
            i_c += 1
    df = pd.DataFrame(c_list)  #df로 변환
    df.to_excel(RESULT_PATH+"comments_results.xlsx",sheet_name='sheet1')


    
main()

