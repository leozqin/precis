from sys import argv
from yaml import load, SafeLoader
from pathlib import Path

from rssynthesis.rss import Config

def main():
    config_path = Path(argv[1]).resolve()

    with open(config_path, "r") as fp:
        configs = load(fp, Loader=SafeLoader)
    
    for config in configs:
        feed = Config(**config)
        print(feed.rss.entries)