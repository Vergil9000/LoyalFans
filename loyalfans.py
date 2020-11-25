import os
import sys
import json
import concurrent.futures

import requests
from tqdm import tqdm
from blessed import Terminal


class Files:
    files = []


def main():
    username = input(
        "Enter the username of the user whose page you would like to scrape:\n >>> ")
    new_profile_url = profile_url.format(username)
    print(f"Retrieving {term.bold(username)}'s page details...")
    limit, name, slug = scrape_profile(new_profile_url)
    slug_dir = os.path.join(destination, slug)
    if os.path.isdir(slug_dir):
        pass
    else:
        os.mkdir(slug_dir)
    print(f"Scraping {term.bold(name)}'s photos and videos...")
    new_timeline_url = timeline_url.format(username, limit)
    images, videos = scrape_timeline(new_timeline_url)
    if images:
        if separate_file_types:
            images_dir = os.path.join(slug_dir, "Images")
            if os.path.isdir(images_dir):
                pass
            else:
                os.mkdir(images_dir)
            os.chdir(images_dir)
        else:
            os.chdir(slug_dir)
        if avoid_duplicates:
            i.files = os.listdir()
        with tqdm(total=len(images), desc="Downloading photos") as bar:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = {executor.submit(
                    download_image, image): image for image in images}
                for future in concurrent.futures.as_completed(futures):
                    future.result
                    bar.update(1)
    if videos:
        if separate_file_types:
            videos_dir = os.path.join(slug_dir, "Videos")
            if os.path.isdir(videos_dir):
                pass
            else:
                os.mkdir(videos_dir)
            os.chdir(videos_dir)
        else:
            os.chdir(slug_dir)
        if avoid_duplicates:
            v.files = os.listdir()
        with tqdm(total=len(videos), desc="Downloading videos") as bar:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = {executor.submit(
                    download_video, video): video for video in videos}
                for future in concurrent.futures.as_completed(futures):
                    future.result()
                    bar.update(1)


def scrape_profile(url):
    with requests.Session() as s:
        r = s.get(url, headers=headers)
        if r.status_code == 200:
            print(term.green(f"{r.status_code} STATUS CODE"))
        else:
            print(term.red(f"{r.status_code} STATUS CODE"))
    profile = json.loads(r.text)
    name = profile['data']['user']['name']
    slug = profile['data']['user']['slug']
    # uid = profile['data']['user']['uid']
    num_posts = profile['data']['counters']['posts_total']
    num_photos = profile['data']['counters']['photos']
    num_videos = profile['data']['counters']['videos']
    limit = num_posts
    while limit % 4 != 0:
        limit += 1
    print(f"According to LoyalFans, {term.bold(name)} has a total of:")
    print(term.bold(
        f"\t· {num_posts} posts\n\t· {num_photos} photos\n\t· {num_videos} videos"))
    return limit, name, slug


def scrape_timeline(url):
    with requests.Session() as s:
        r = s.get(url, headers=headers)
        if r.status_code == 200:
            print(term.green(f"{r.status_code} STATUS CODE"))
        else:
            print(term.red(f"{r.status_code} STATUS CODE"))
    timeline = json.loads(r.text)
    posts = timeline['timeline']
    print(f"\t· Found {term.bold(str(len(posts)))} posts")
    images = []
    videos = []
    for post in posts:
        if post['photo']:
            if 'photos' in (has_photos := post['photos']):
                photos = has_photos['photos']
                for photo in photos:
                    image_url = photo['images']['original']
                    image_url = image_url.replace('\\', '')
                    images.append(image_url)
            else:
                pass
        else:
            pass
        if post['video']:
            if 'video_url' in (video_object := post['video_object']):
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
    if avoid_duplicates:
        if filename in i.files:
            return None
    with requests.Session() as s:
        r = s.get(url, headers=headers)
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                f.write(chunk)


def download_video(url):
    filename = url.rsplit('/')[-1]
    if "?" in filename:
        filename = filename.split('?')[0]
    if avoid_duplicates:
        if filename in v.files:
            return None
    with requests.Session() as s:
        r = s.get(url, headers=headers)
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                f.write(chunk)


if __name__ == '__main__':
    settings_file = os.path.join(sys.path[0], 'config.json')
    with open(settings_file) as f:
        config = json.load(f)['config']
    headers = config['headers']
    settings = config['settings']
    if not (destination := settings['destination_path']):
        destination = os.getcwd()
    separate_file_types = settings['separate_file_types']
    download_preview_videos = settings['download_preview_videos']
    if avoid_duplicates := settings['avoid_duplicates']:
        i = Files()
        v = Files()
    profile_url = config['urls']['profile_url']
    timeline_url = config['urls']['timeline_url']
    term = Terminal()
    main()
    print(term.green('Program successfully quit'))
