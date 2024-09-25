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
    # 파일 이름에서 사용할 수 없는 문자 제거
    return re.sub(r'[\/:*?"<>|]', '', filename)

def remove_after_year(text):
    # 제거할 연도 리스트
    years = ["2015", "2016", "2017"]
    
    # 각 연도를 검사하며 해당 연도가 문자열에 있으면 그 위치 이후의 내용을 잘라냄
    for year in years:
        if year in text:
            return text.split(year)[0].strip()  # 연도와 이후 내용 제거하고 공백 제거
    return text

# Chrome 옵션 설정 (헤드리스 모드로 실행)
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')

# Selenium Manager를 이용하여 자동으로 ChromeDriver 설정
driver = webdriver.Chrome(options=chrome_options)

# 블로그 ID 및 카테고리 설정
blog_id = "0114734366"
parent_category_no = 9

# 모든 페이지 크롤링을 위한 페이지 수 설정
current_page = 1  # 시작 페이지 번호
last_page = 2  # 크롤링할 마지막 페이지 번호 (필요에 따라 변경)

# 게시물 데이터를 저장할 폴더 생성
if not os.path.exists("blog_posts"):
    os.makedirs("blog_posts")

while current_page <= last_page:
    # 페이지별 URL
    url = f"https://blog.naver.com/PostList.naver?from=postList&blogId={blog_id}&parentCategoryNo={parent_category_no}&currentPage={current_page}"
    driver.get(url)

    # 페이지 로딩 대기
    time.sleep(2)

    # 현재 페이지의 HTML 가져오기
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # a 태그 목록을 가져옴
    post_links = soup.find_all('a')

    # 게시물 URL 추출
    post_urls = []
    for link in post_links:
        href = link.get('href')
        if href and href.startswith("/PostView.naver"):
            full_url = "https://blog.naver.com" + href
            post_urls.append(full_url)

    print(f"{current_page} 페이지에서 {len(post_urls)}개의 게시물 URL을 추출했습니다.")

    # 각 게시물의 내용을 크롤링
    for idx, post_url in enumerate(post_urls):
        try:
            driver.get(post_url)
            time.sleep(2)  # 페이지 로딩 대기
            post_html = driver.page_source
            post_soup = BeautifulSoup(post_html, 'html.parser')
            
            # 게시물 제목 가져오기
            post_title = post_soup.find("title").get_text(strip=True) if post_soup.find("title") else f"post_{idx + 1}"
            post_title = sanitize_filename(post_title)

            # 이미지 폴더 생성
            post_image_folder = f"blog_posts/{post_title}_images"
            if not os.path.exists(post_image_folder):
                os.makedirs(post_image_folder)

            # 이미지 다운로드
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
                        img_tag['src'] = img_filename  # 로컬 이미지 경로로 변경
                    except requests.exceptions.RequestException as e:
                        print(f"이미지 다운로드 실패: {img_url} - {e}")
                        continue

            # 게시물 HTML을 로컬에 저장
            with open(f"blog_posts/{post_title}.html", "w", encoding="utf-8") as file:
                file.write(str(post_soup))

            print(f"{post_title} 게시물을 성공적으로 저장했습니다.")

        except Exception as e:
            print(f"게시물 크롤링 중 오류 발생: {post_url} - {e}")

        # 블로그 메인 페이지의 HTML을 로컬에 저장하고, 링크를 수정
        blog_content = soup
        for idx, link in enumerate(blog_content.find_all('a', href=True)):
            if "PostView.naver" in link['href']:
                link_final = sanitize_filename(link.get_text(strip=True))
                link_final = remove_after_year(link_final)
        
                link['href'] = f"blog_posts/{link_final}  네이버 블로그.html"  # 로컬 파일 경로로 변경

    # 다음 페이지로 이동
    current_page += 1

print("모든 페이지의 게시물 크롤링이 완료되었습니다.")

# 블로그 메인 페이지의 HTML을 로컬에 저장하고, 링크를 수정
driver.get(f"https://blog.naver.com/PostList.naver?blogId={blog_id}&parentCategoryNo={parent_category_no}&currentPage=1")
html = driver.page_source
blog_content = BeautifulSoup(html, 'html.parser')

for idx, link in enumerate(blog_content.find_all('a', href=True)):
    if "PostView.naver" in link['href']:
        link_final = sanitize_filename(link.get_text(strip=True))
        link_final = remove_after_year(link_final)
        
        link['href'] = f"blog_posts/{link_final}  네이버 블로그.html"  # 로컬 파일 경로로 변경

with open("blog_content.html", "w", encoding="utf-8") as file:
    file.write(str(blog_content))














# 로컬 저장을 위한 디렉터리 생성
if not os.path.exists("local_pages"):
    os.makedirs("local_pages")

while current_page <= last_page:
    # 페이지 URL
    page_url = f"https://blog.naver.com/PostList.naver?from=postList&blogId={blog_id}&parentCategoryNo={parent_category_no}&currentPage={current_page}"
    driver.get(page_url)
    time.sleep(2)  # 페이지 로딩 대기

    # 현재 페이지 HTML 가져오기
    page_html = driver.page_source
    page_soup = BeautifulSoup(page_html, 'html.parser')

    # 페이지네이션 내용을 로컬 HTML로 저장
    page_filename = f"local_pages/page_{current_page}.html"
    with open(page_filename, "w", encoding="utf-8") as file:
        file.write(str(page_soup))
    print(f"페이지 {current_page}가 로컬에 저장되었습니다.")

    # 다음 페이지로 이동
    current_page += 1

# 페이지네이션의 첫 번째 페이지로 이동
driver.get(f"https://blog.naver.com/PostList.naver?blogId={blog_id}&parentCategoryNo={parent_category_no}&currentPage=1")
html = driver.page_source
blog_content = BeautifulSoup(html, 'html.parser')

# 페이지네이션 부분을 찾기
pagination_div = blog_content.find('div', {'class': 'blog2_paginate'})

# 페이지네이션의 링크를 로컬 파일로 변경
if pagination_div:
    page_links = pagination_div.find_all('a', href=True)
    for link in page_links:
        if "currentPage=" in link['href']:
            # 페이지 번호 추출
            match = re.search(r'currentPage=(\d+)', link['href'])
            if match:
                page_number = match.group(1)
                # 로컬 HTML 파일 링크로 변경
                link['href'] = f"local_pages/page_{page_number}.html"
    print("페이지네이션 링크를 로컬 파일로 변경했습니다.")

# 블로그 메인 페이지의 HTML을 로컬에 저장하고, 링크를 수정
for idx, link in enumerate(blog_content.find_all('a', href=True)):
    if "PostView.naver" in link['href']:
        link_final = sanitize_filename(link.get_text(strip=True))
        link_final = remove_after_year(link_final)
        
        link['href'] = f"blog_posts/{link_final}  네이버 블로그.html"  # 로컬 파일 경로로 변경

# 변경된 HTML을 저장
with open("blog_content_with_pagination.html", "w", encoding="utf-8") as file:
    file.write(str(blog_content))

print("블로그 메인 페이지가 페이지네이션 링크와 함께 로컬에 저장되었습니다.")



# 블로그 메인 페이지의 HTML을 로컬에 저장하고, 링크를 수정
blog_content = soup
for idx, link in enumerate(blog_content.find_all('a', href=True)):
    if "PostView.naver" in link['href']:
        link_final = sanitize_filename(link.get_text(strip=True))
        link_final = remove_after_year(link_final)
        
        link['href'] = f"blog_posts/{link_final}  네이버 블로그.html"  # 로컬 파일 경로로 변경








print("블로그 전체 콘텐츠가 로컬에 저장되었습니다.")

# 드라이버 종료
driver.quit()
