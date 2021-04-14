from praw.exceptions import RedditAPIException
from praw.models.reddit.submission import Submission
from praw.models.reddit.comment import Comment
import re
import spacy
from urllib.parse import quote_plus
import functools
import time
import logging

nlp = spacy.load("en_core_web_trf")


def clean_title(title: str) -> str:
    title = re.sub(r'(\(|\[)OC(\)|\])', '', title)  # removes (OC), [OC]
    title = re.sub(r'(\(|\[)?[0-9]+ ?[x|X|×] ?[0-9]+(\)|\])?', '', title)  # removes [4000x3000], (4000x3000) etc
    title = re.sub(r'@( )?[a-zA-Z_0-9.]+', '', title)  # removes @ social media handles
    title = title.strip()

    return title


def get_location(title: str) -> str:
    doc = nlp(title)
    loc, gpe = [], []

    for entity in doc.ents:
        print(entity.text, entity.label_)
        if entity.label_ == 'LOC' and entity.text not in loc:  # very occasionally there are duplicates in a long title
            loc.append(entity.text)
        elif entity.label_ == 'GPE' and entity.text not in gpe:
            gpe.append(entity.text)
    
    location = loc + gpe  # loc is more specific than gpe so loc should come first

    return ', '.join(location)


def get_gmap_link(location: str, prefix: str = 'https://www.google.com/maps/search/?api=1&query=') -> str:
    # this function can probably be made more useful when we want to use other google map APIs
    return prefix + quote_plus(location)


def retry(retry_count=5, delay=60, allowed_exceptions=(RedditAPIException)):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for _ in range(retry_count):
                try:
                    result = func(*args, **kwargs)
                    if result:
                        return result
                except allowed_exceptions as e:
                    time.sleep(delay)
                    pass
        return wrapper
    return decorator


@retry(retry_count=5, delay=2*60)  # I haven't been rate limited when cross posting so I don't think this delay needs to be very long
def crosspost_to_sub(submission: Submission, **kwargs) -> Submission:
    cross_post = submission.crosspost(**kwargs)
    return cross_post


@retry(retry_count=3, delay=10*60)  # rate limit (at least on r/test) seems to be 7++
def comment_on_post(submission: Submission, commenttext: str) -> Comment:
    comment = submission.reply(commenttext)
    return comment


def handle_submission(submission: Submission, crosspost: bool, crosspost_to: str) -> None:    
    print(f"submission id {submission} has title {submission.title}, photo can be found at {submission.url}")
    title = clean_title(submission.title)
    print(f"Cleaner title: {title}")
    
    location = get_location(title)

    if location:
        print(f"Location is {location}")

        gmapsearchlink = get_gmap_link(location)
        print(gmapsearchlink)

        if crosspost:
            cross_post = crosspost_to_sub(submission=submission, subreddit=crosspost_to, title=location, send_replies=False)
            comment_on_post(submission=cross_post, commenttext=gmapsearchlink)
        
    else:
        print("No location found\n")
