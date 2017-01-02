

urls = set()
with open('trackers.info', 'r') as info:
    for line in info:
        urls.add(line)
urls = sorted(urls)
with open('trackers.unique.info', 'w') as info:
    for url in urls:
        info.write(url)

