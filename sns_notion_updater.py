import feedparser
import requests
import os
from datetime import datetime

# 환경 변수에서 RSS 피드 URL, Notion API Key 및 Database ID 가져오기
TISTORY_RSS_FEED_URL_1 = os.getenv('TISTORY_RSS_FEED_URL_1')
NOTION_API_KEY = os.getenv('NOTION_API_KEY')
NOTION_DATABASE_ID_1 = os.getenv('NOTION_DATABASE_ID_1')

def get_latest_posts(rss_url):
    feed = feedparser.parse(rss_url)
    if feed.bozo:
        print("Error parsing RSS feed:", feed.bozo_exception)
        return []
    posts = []
    for entry in feed.entries:
        post = {
            'url': entry.link,
            'date': entry.published
        }
        posts.append(post)
    return posts

def convert_to_iso_8601(date_str):
    # feedparser에서 가져온 날짜를 datetime 객체로 변환
    date_obj = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
    # ISO 8601 형식의 문자열로 변환
    return date_obj.isoformat()

def get_existing_urls():
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID_1}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    existing_urls = []
    has_more = True
    while has_more:
        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            for result in data['results']:
                if 'URL' in result['properties']:
                    existing_urls.append(result['properties']['URL']['url'])
            has_more = data['has_more']
        else:
            print("Failed to fetch existing posts from Notion:", response.status_code, response.text)
            break
    return existing_urls

def add_post_to_notion(post):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    data = {
        "parent": {"database_id": NOTION_DATABASE_ID_1},
        "properties": {
            "URL": {
                "url": post['url']
            },
            "Date": {
                "date": {
                    "start": convert_to_iso_8601(post['date'])
                }
            }
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        print("Failed to add post to Notion:", response.status_code, response.text)
    else:
        print("Successfully added post to Notion:", post['url'])

def update_notion_with_latest_posts():
    posts = get_latest_posts(TISTORY_RSS_FEED_URL_1)
    if not posts:
        print("No posts found in RSS feed.")
        return

    existing_urls = get_existing_urls()
    for post in posts:
        if post['url'] not in existing_urls:
            print("Adding post to Notion:", post['url'])
            add_post_to_notion(post)
        else:
            print("Post already exists in Notion:", post['url'])

if __name__ == "__main__":
    print("Starting Notion updater...")
    update_notion_with_latest_posts()
    print("Notion updater finished.")
