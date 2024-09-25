from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup
import requests
import os
import base64
import re

def sanitize_filename(filename):
    return re.sub(r'[\/:*?"<>|]', '', filename)

def remove_after_year(text):
    years = ["2015", "2016", "2017"]
    for year in years:
        if year in text:
            return text.split(year)[0].strip()
    return text

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')

driver = webdriver.Chrome(options=chrome_options)

# 블로그 ID 및 카테고리 설정
blog_id = "0114734366"
parent_category_no = 9
current_page = 3 
last_page = 5

# 로컬 저장을 위한 디렉터리 생성
if not os.path.exists("blog_posts"):
    os.makedirs("blog_posts")

if not os.path.exists("local_pages"):
    os.makedirs("local_pages")

while current_page <= last_page:
    page_url = f"https://blog.naver.com/PostList.naver?from=postList&blogId={blog_id}&parentCategoryNo={parent_category_no}&currentPage={current_page}"
    driver.get(page_url)
    time.sleep(2)

    page_html = driver.page_source
    page_soup = BeautifulSoup(page_html, 'html.parser')



    # 게시물 URL 추출
    post_links = page_soup.find_all('a', href=True)
    post_urls = []
    for link in post_links:
        href = link.get('href')
        if href and href.startswith("/PostView.naver"):
            full_url = "https://blog.naver.com" + href
            post_urls.append(full_url)

    print(f"{current_page} 페이지에서 {len(post_urls)}개의 게시물 URL을 추출했습니다.")

    for idx, post_url in enumerate(post_urls):
        try:
            driver.get(post_url)
            time.sleep(2)
            post_html = driver.page_source
            post_soup = BeautifulSoup(post_html, 'html.parser')
            
            post_title = post_soup.find("title").get_text(strip=True) if post_soup.find("title") else f"post_{idx + 1}"
            post_title = sanitize_filename(post_title)

            post_image_folder = f"blog_posts/{post_title}_images"
            if not os.path.exists(post_image_folder):
                os.makedirs(post_image_folder)

            post_images = post_soup.find_all('img')
            for img_idx, img_tag in enumerate(post_images):
                img_url = img_tag.get('src')
                if img_url and img_url.startswith('http'):
                    try:
                        response = requests.get(img_url)
                        response.raise_for_status()
                        img_data = response.content
                        img_filename = f"{post_image_folder}/image_{img_idx + 1}.jpg"
                        with open(img_filename, 'wb') as img_file:
                            img_file.write(img_data)
                        img_filename = img_filename.replace("blog_posts/", "")
                        img_tag['src'] = img_filename
                    except requests.exceptions.RequestException as e:
                        print(f"이미지 다운로드 실패: {img_url} - {e}")
                        continue

            with open(f"blog_posts/{post_title}.html", "w", encoding="utf-8") as file:
                file.write(str(post_soup))

            

            print(f"{post_title} 게시물을 성공적으로 저장했습니다.")

        except Exception as e:
            print(f"게시물 크롤링 중 오류 발생: {post_url} - {e}")


            

    for idx, link in enumerate(page_soup.find_all('a', href=True)):
        if "PostView.naver" in link['href']:
            link_final = sanitize_filename(link.get_text(strip=True))
            link_final = remove_after_year(link_final)
        
            link['href'] = f"../blog_posts/{link_final}  네이버 블로그.html"  # 로컬 파일 경로로 변경
            
    for a_tag in page_soup.find_all('a', class_='page'):
        page_number = a_tag.text.strip()
        new_href = f"page_{page_number}.html"
        a_tag['href'] = new_href

    # 현재 페이지의 HTML을 local_pages 폴더에 저장
    page_filename = f"local_pages/page_{current_page}.html"
    with open(page_filename, "w", encoding="utf-8") as file:
        file.write(str(page_soup))
    print(f"페이지 {current_page}가 로컬에 저장되었습니다.")

    

    current_page += 1

print("모든 페이지의 게시물 크롤링이 완료되었습니다.")

driver.quit()
