import os
import sys
import json
import concurrent.futures
import time
import datetime
from collections import deque
from threading import Timer

import requests
from tqdm import tqdm
from blessed import Terminal
from dateutil.parser import parse

from logs.logger import Logger


class F:
    files = []


def main():
    following_count = scrape_user(user_url)
    creators_list = scrape_follow(follow_url, following_count)
    slug = menu(creators_list)
    new_profile_url = profile_url.format(slug)
    logger.info(f"Retrieving {term.bold(slug)}'s page details...")
    limit, name, num_store_videos = scrape_profile(new_profile_url)
    slug_dir = os.path.join(destination, slug)
    if not os.path.isdir(slug_dir):
        os.mkdir(slug_dir)
    timeline_dir = os.path.join(slug_dir, "Timeline")
    if not os.path.isdir(timeline_dir):
        os.mkdir(timeline_dir)
    logger.info(f"Scraping {term.bold(name)}'s photos and videos...")
    new_timeline_url = timeline_url.format(slug, limit)
    images, videos = scrape_timeline(new_timeline_url)
    if images:
        if separate_file_types:
            images_dir = os.path.join(timeline_dir, "Images")
            if not os.path.isdir(images_dir):
                os.mkdir(images_dir)
            os.chdir(images_dir)
        else:
            os.chdir(timeline_dir)
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
            videos_dir = os.path.join(timeline_dir, "Videos")
            if not os.path.isdir(videos_dir):
                os.mkdir(videos_dir)
            os.chdir(videos_dir)
        else:
            os.chdir(timeline_dir)
        if avoid_duplicates:
            v.files = os.listdir()
        with tqdm(total=len(videos), desc="Downloading videos") as bar:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = {executor.submit(
                    download_video, video): video for video in videos}
                for future in concurrent.futures.as_completed(futures):
                    future.result()
                    bar.update(1)
    logger.info(f"Scraping your messages with {term.bold(name)}...")
    new_messages_url = messages_url.format(slug, timezone, '')
    msg_images, msg_videos = scrape_messages(new_messages_url, slug, timezone)
    if msg_images or msg_videos:
        msg_dir = os.path.join(slug_dir, "Messages")
        if not os.path.isdir(msg_dir):
            os.mkdir(msg_dir)
        if msg_images:
            if separate_file_types:
                msg_images_dir = os.path.join(msg_dir, "Images")
                if not os.path.isdir(msg_images_dir):
                    os.mkdir(msg_images_dir)
                os.chdir(msg_images_dir)
            else:
                os.chdir(msg_dir)
            if avoid_duplicates:
                msg_i.files = os.listdir()
                i.files = []
            with tqdm(total=len(msg_images), desc="Downloading photos") as bar:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    futures = {executor.submit(
                        download_image, image): image for image in msg_images}
                    for future in concurrent.futures.as_completed(futures):
                        future.result
                        bar.update(1)
        if msg_videos:
            if separate_file_types:
                msg_videos_dir = os.path.join(msg_dir, "Videos")
                if not os.path.isdir(msg_videos_dir):
                    os.mkdir(msg_videos_dir)
                os.chdir(msg_videos_dir)
            else:
                os.chdir(msg_dir)
            if avoid_duplicates:
                msg_v.files = os.listdir()
                v.files = []
            with tqdm(total=len(msg_videos), desc="Downloading videos") as bar:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    futures = {executor.submit(
                        download_video, video): video for video in msg_videos}
                    for future in concurrent.futures.as_completed(futures):
                        future.result()
                        bar.update(1)
    if num_store_videos:
        logger.info(f"Scraping {term.bold(name)}'s store videos...")
        store_videos = scrape_video_store(
            video_store_url, num_store_videos, slug)
        if store_videos:
            store_videos_dir = os.path.join(slug_dir, "Store Videos")
            if not os.path.isdir(store_videos_dir):
                os.mkdir(store_videos_dir)
            os.chdir(store_videos_dir)
            if avoid_duplicates:
                store_v.files = os.listdir()
                msg_v.files = []
            with tqdm(total=len(store_videos), desc="Downloading store videos") as bar:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    futures = {executor.submit(
                        download_video, video): video for video in store_videos}
                    for future in concurrent.futures.as_completed(futures):
                        future.result
                        bar.update(1)
    if avoid_duplicates:
        i.files, msg_i.files = [], []
        v.files, msg_v.files, store_v.files = [], [], []
    main()


def scrape_user(url):
    with requests.Session() as s:
        r = s.get(url, headers=headers)
    if r.status_code == 200:
        logger.debug(term.green(f"{r.status_code} STATUS CODE"))
    else:
        logger.info(term.red(f"{r.status_code} STATUS CODE"))
        logger.info(term.red(logger.status_error))
        sys.exit([0])
    try:
        following_count = json.loads(r.text)['following']
    except KeyError:
        logger.error(term.red(logger.key_error))
    return following_count


def scrape_follow(url, count):
    payload = {
        'limit': count,
    }
    with requests.Session() as s:
        r = s.post(url, headers=headers, params=payload)
    if r.status_code == 200:
        logger.debug(term.green(f"{r.status_code} STATUS CODE"))
    else:
        logger.info(term.red(f"{r.status_code} STATUS CODE"))
        logger.info(term.red(logger.status_error))
        sys.exit([0])
    creators = json.loads(r.text)['response']['followed']
    creators_info_list = [(creator['name'].strip(), creator['slug'])
                          for creator in creators]
    creators_info_list.sort(key=lambda x: x[0].casefold())
    creators_list = list(enumerate(creators_info_list, 1))
    return creators_list


def menu(lis):
    logger.info(
        term.bold("Select a creator by entering their corresponding number:\n"))
    d = deque(lis)
    d.appendleft(('NUMBER', 'NAME', 'HANDLE'))
    fmt = '{:<22}' * len(d[0])
    logger.info(term.underline(fmt.format(*d[0])))
    d.popleft()
    for num, value in d:
        logger.info(fmt.format(num, *value))
    logger.info("\nEnter any negative number to quit the program")
    while True:
        try:
            number = int(input(" >>> "))
            if number < 0:
                logger.info(term.green("Program successfully quit"))
                sys.exit([0])
            for num, value in d:
                if num == number:
                    slug = value[1]
                    return slug
        except Exception:
            logger.info(term.yellow("Please enter a number"))


def scrape_profile(url):
    with requests.Session() as s:
        r = s.get(url, headers=headers)
    if r.status_code == 200:
        logger.debug(term.green(f"{r.status_code} STATUS CODE"))
    else:
        logger.info(term.red(f"{r.status_code} STATUS CODE"))
        logger.info(term.red(logger.status_error))
        sys.exit([0])
    profile = json.loads(r.text)
    try:
        name = profile['data']['user']['name']
        num_posts = profile['data']['counters']['posts_total']
        num_photos = profile['data']['counters']['photos']
        num_videos = profile['data']['counters']['videos']
        num_store_videos = profile['data']['counters']['store_videos']
        num_videos -= num_store_videos
    except KeyError:
        logger.error(logger.key_error)
    limit = num_posts
    while limit % 4 != 0:
        limit += 1
    logger.info(f"According to LoyalFans, {term.bold(name)} has a total of:")
    logger.info(term.bold(
        f"\t· {num_posts} posts\n\t· {num_photos} photos\n\t· {num_videos} videos\n\t· {num_store_videos} store videos"))
    return limit, name, num_store_videos


def scrape_timeline(url):
    t1, t2 = Timer(7.5, wait, [1]), Timer(15, wait, [0])
    t1.start(), t2.start()
    with requests.Session() as s:
        r = s.get(url, headers=headers)
    if r.status_code == 200:
        logger.debug(term.green(f"{r.status_code} STATUS CODE"))
    else:
        logger.info(term.red(f"{r.status_code} STATUS CODE"))
        logger.info(term.red(logger.status_error))
        sys.exit([0])
    timeline = json.loads(r.text)
    posts = timeline['timeline']
    logger.info(f"\t· Found {term.bold(str(len(posts)))} posts")
    images, videos = [], []
    for post in posts:
        if post['photo']:
            if 'photos' in (has_photos := post['photos']):
                date = get_timestamp(post['created_at']['date'])
                photos = has_photos['photos']
                for photo in photos:
                    image_url = photo['images']['original']
                    image_url = image_url.replace('\\', '')
                    image_tuple = (image_url, date)
                    images.append(image_tuple)
            else:
                pass
        else:
            pass
        if post['video']:
            if 'video_url' in (video_object := post['video_object']):
                date = get_timestamp(post['created_at']['date'])
                video_url = video_object['video_url']
                video_url = video_url.replace('\\', '')
                video_tuple = (video_url, date)
                videos.append(video_tuple)
            elif 'video_trailer' in video_object:
                if download_preview_videos:
                    date = get_timestamp(post['created_at']['date'])
                    video_url = video_object['video_trailer']
                    video_url.replace('\\', '')
                    video_tuple = (video_url, date)
                    videos.append(video_tuple)
                else:
                    pass
            else:
                pass
    t1.cancel(), t2.cancel()
    logger.info(f"\t· Found {term.bold(str(len(images)))} photos")
    logger.info(f"\t· Found {term.bold(str(len(videos)))} videos")
    return images, videos


def scrape_messages(url, slug, tz, array=[]):
    with requests.Session() as s:
        r = s.get(url, headers=headers)
    if r.status_code == 200:
        logger.debug(term.green(f"{r.status_code} STATUS CODE"))
    else:
        logger.info(term.red(f"{r.status_code} STATUS CODE"))
        logger.info(term.red(logger.status_error))
        sys.exit([0])
    messages_api = json.loads(r.text)
    try:
        list_messages = messages_api['messages']
        list_messages += array
        mid = "&mid=" + messages_api['mid_token']
        new_messages_url = messages_url.format(slug, tz, mid)
        messages = scrape_messages(new_messages_url, slug, tz, list_messages)
    except KeyError:
        if array:
            return list_messages
        else:
            messages = list_messages
    if array:
        return messages
    logger.info(f"\t· Found {term.bold(str(len(messages)))} messages")
    image_urls, video_urls = [], []
    for message in list(messages):
        if message['has_images']:
            if not message['is_locked']:
                images = message['images']
                date = get_timestamp(message['created_at']['date'])
                for image in images:
                    image_urls.append((image['image'], date))
            else:
                pass
        if message['has_video']:
            if not message['is_locked']:
                date = get_timestamp(message['created_at']['date'])
                video_urls.append((message['video'], date))
            else:
                pass
    logger.info(f"\t· Found {term.bold(str(len(image_urls)))} photos")
    logger.info(f"\t· Found {term.bold(str(len(video_urls)))} videos")
    return image_urls, video_urls


def scrape_video_store(url, num, slug):
    payload = {
        'limit': num,
        'slug': slug,
        'privacy': [],
        'type': 'video',
    }
    with requests.Session() as s:
        r = s.post(url, headers=headers, params=payload)
    if r.status_code == 200:
        logger.debug(term.green(f"{r.status_code} STATUS CODE"))
    else:
        logger.info(term.red(f"{r.status_code} STATUS CODE"))
        logger.info(term.red(logger.status_error))
        sys.exit([0])
    videos = []
    store_videos = json.loads(r.text)['list']
    if store_videos:
        for video in store_videos:
            if video['is_bought']:
                if 'video_url' in (video_object := video['video_object']):
                    video_url = video_object['video_url']
                    video_url = video_url.replace('\\', '')
                    date = get_timestamp(video['created_at']['date'])
                    videos.append((video_url, date))
            else:
                if download_preview_videos:
                    if 'video_trailer' in (video_object := video['video_object']):
                        video_trailer = video_object['video_trailer']
                        video_trailer.replace('\\', '')
                        date = get_timestamp(video['created_at']['date'])
                        videos.append((video_trailer, date))
    logger.info(f"\t· Found {term.bold(str(len(videos)))} store videos")
    return videos


def wait(num):
    if num:
        logger.info(term.bold(logger.wait1))
    else:
        logger.info(term.bold(logger.wait2))


def get_timestamp(date):
    iso_datetime = parse(date)
    timezone = time.strftime('%z', time.gmtime())
    timezone = timezone.replace('+', '')
    if timezone == '0000':
        timezone = 0
    else:
        timezone = timezone.replace('0', '')
    delta = datetime.timedelta(hours=int(timezone))
    timestamp = datetime.datetime.timestamp(iso_datetime + delta)
    return timestamp


def download_image(tup):
    filename = tup[0].rsplit('/')[-1].split('?')[0]
    if avoid_duplicates:
        if filename in i.files or msg_i.files:
            return None
    with requests.Session() as s:
        r = s.get(tup[0], headers=headers)
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                f.write(chunk)
    if use_original_dates:
        time = (tup[1], tup[1])
        os.utime(filename, time)


def download_video(tup):
    filename = tup[0].rsplit('/')[-1]
    if "?" in filename:
        filename = filename.split('?')[0]
    if avoid_duplicates:
        if filename in v.files or msg_v.files or store_v.files:
            return None
    with requests.Session() as s:
        r = s.get(tup[0], headers=headers)
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                f.write(chunk)
    if use_original_dates:
        time = (tup[1], tup[1])
        os.utime(filename, time)


if __name__ == '__main__':
    settings_file = os.path.join(sys.path[0], 'config.json')
    with open(settings_file) as f:
        config = json.load(f)['config']
    headers, settings, urls = config['headers'], config['settings'], config['urls']
    if not (destination := settings['destination_path']):
        destination = os.getcwd()
    separate_file_types = settings['separate_file_types']
    download_preview_videos = settings['download_preview_videos']
    if avoid_duplicates := settings['avoid_duplicates']:
        i, v, msg_i, msg_v, store_v = F(), F(), F(), F(), F()
    use_original_dates = settings['use_original_dates']
    timezone = settings['timezone']
    debug = settings['debug']
    logger = Logger(debug)
    user_url = urls['user_url']
    follow_url = urls['follow_url']
    profile_url = urls['profile_url']
    timeline_url = urls['timeline_url']
    messages_url = urls['messages_url']
    video_store_url = urls['video_store_url']
    term = Terminal()
    main()
