import os
import sys
import json
import concurrent.futures

import requests
from tqdm import tqdm
from blessings import Terminal


def main():
    profile_url = "https://www.loyalfans.com/api/v2/profile/star/{}/"
    timeline_url = "https://www.loyalfans.com/api/v2/social/timeline/{}?limit={}&page=0/"
    username = input(
        "Enter the username of the user whose page you would like to scrape:\n >>> ")
    new_profile_url = profile_url.format(username)
    print(f"Retrieving {term.bold(username)}'s page details...")
    limit, name = scrape_profile(new_profile_url)
    print(f"Scraping {term.bold(name)}'s photos and videos...")
    new_timeline_url = timeline_url.format(username, limit)
    images, videos = scrape_timeline(new_timeline_url)
    if images:
        length = len(images)
        with tqdm(total=length, desc="Downloading photos") as bar:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = {executor.submit(
                    download_image, image): image for image in images}
                for future in concurrent.futures.as_completed(futures):
                    future.result
                    bar.update(1)
    if videos:
        length = len(videos)
        with tqdm(total=length, desc="Downloading videos") as bar:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = {executor.submit(
                    download_video, video): video for video in videos}
                for future in concurrent.futures.as_completed(futures):
                    future.result()
                    bar.update(1)
    print(term.green("Program successfully quit"))


def scrape_profile(url):
    with requests.Session() as s:
        r = s.get(url, headers=headers)
        if r.status_code == 200:
            print(term.green(f"{r.status_code} STATUS CODE"))
        else:
            print(term.red(f"{r.status_code} STATUS CODE"))
        content = r.content
    json_decoded = content.decode('utf-8')
    profile = json.loads(json_decoded)
    name = profile['data']['user']['name']
    num_posts = profile['data']['counters']['posts_total']
    num_photos = profile['data']['counters']['photos']
    num_videos = profile['data']['counters']['videos']
    limit = num_posts
    while limit % 4 != 0:
        limit += 1
    print(f"According to LoyalFans, {term.bold(name)} has a total of:")
    print(term.bold(
        f"\t· {num_posts} posts\n\t· {num_photos} photos\n\t· {num_videos} videos"))
    return limit, name


def scrape_timeline(url):
    with requests.Session() as s:
        r = s.get(url, headers=headers)
        if r.status_code == 200:
            print(term.green(f"{r.status_code} STATUS CODE"))
        else:
            print(term.red(f"{r.status_code} STATUS CODE"))
    json_decoded = r.content.decode('utf-8')
    timeline = json.loads(json_decoded)
    posts = timeline['timeline']
    print(f"\t· Found {term.bold(str(len(posts)))} posts")
    images = []
    videos = []
    for post in posts:
        has_photo = post['photo']
        if has_photo:
            has_photos = post['photos']
            if 'photos' in has_photos:
                photos = has_photos['photos']
                for photo in photos:
                    image_url = photo['images']['original']
                    image_url = image_url.replace('\\', '')
                    images.append(image_url)
            else:
                pass
        else:
            pass
        has_video = post['video']
        if has_video:
            video_object = post['video_object']
            videos
            if 'video_url' in video_object:
                video_url = video_object['video_url']
                video_url = video_url.replace('\\', '')
                videos.append(video_url)
            elif 'video_trailer' in video_object:
                if download_preview_videos:
                    video_url = video_object['video_trailer']
                    video_url.replace('\\', '')
                    videos.append(video_url)
                else:
                    pass
            else:
                pass
    print(f"\t· Found {term.bold(str(len(images)))} photos")
    print(f"\t· Found {term.bold(str(len(videos)))} videos")
    return images, videos


def download_image(url):
    filename = url.rsplit('/')[-1].split('?')[0]
    with requests.Session() as s:
        r = s.get(url, headers=headers)
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                f.write(chunk)


def download_video(url):
    filename = url.rsplit('/')[-1]
    if "?" in filename:
        filename = filename.split('?')[0]
    with requests.Session() as s:
        r = s.get(url, headers=headers)
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                f.write(chunk)


current_directory = os.getcwd()
os.chdir(sys.path[0])
with open('settings.json') as f:
    headers = json.load(f)['headers']
with open('settings.json') as f:
    settings = json.load(f)['settings']
    download_preview_videos = settings['download_preview_videos']
os.chdir(current_directory)
term = Terminal()

if __name__ == '__main__':
    main()
