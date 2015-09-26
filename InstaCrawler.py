import json
import os
import requests
import sys
import concurrent.futures
import argparse
import datetime

def enum(**enums):
    return type('Enum', (), enums)

Quality = enum(Thumbnail = 'thumbnail', Low = 'low_resolution', Standard = 'standard_resolution')

class InstaCrawler:

    quality = Quality.Standard
    max_workers = 10
    user_name = ''

    def __init__(self, user_name, quality=Quality.Standard):
        self.user_name = user_name
        self.quality = quality

    def asyncStart(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_item = dict((executor.submit(self.download, item, './' + self.user_name), item) for item in self.crawl())

        for future in concurrent.futures.as_completed(future_to_item):
            item = future_to_item[future]
            url = item[item['type'] + 's']['standard_resolution']['url']
            if future.exception() is not None:
                print('%r generated an exception: %s' % (url, future.exception()))

    def crawl(self, items=[], max_id=None):
        url = 'http://instagram.com/' + self.user_name + '/media' + ('?&max_id=' + max_id if max_id is not None else '')
        media = json.loads(requests.get(url).text)

        items.extend([ curr_item for curr_item in media['items'] ])

        if 'more_available' not in media or media['more_available'] is False:
            return items
        else:
            max_id = media['items'][-1]['id']
            return self.crawl(items, max_id)

    def download(self, item, save_dir='./'):
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        url = item[item['type'] + 's'][self.quality]['url']
        base_name = url.split('/')[-1]
        file_path = os.path.join(save_dir, base_name)

        with open(file_path, 'wb') as file:
            print("Downloading %s" % base_name)
            bytes = requests.get(url).content
            file.write(bytes)

if __name__ == '__main__':
  parser = argparse.ArgumentParser(add_help=True)
  parser.add_argument('username')
  args = parser.parse_args()
  insta = InstaCrawler(args.username)
  insta.asyncStart()