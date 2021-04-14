import praw
from praw.util.token_manager import FileTokenManager
from processing import handle_submission
import argparse
import logging


REFRESH_TOKEN_FILENAME = "refresh_token.txt"  # has to be uploaded


CROSSPOST_TO = "picsmirrortest"
SOURCE_SUBS = ["EarthPorn"]


def main(
        read_mode: str,
        limit: int,
        crosspost: bool,
        pause_after: int
    ) -> None:
    reddit = praw.Reddit(
        token_manager=FileTokenManager(REFRESH_TOKEN_FILENAME),
        user_agent="use_file_token_manager/v0 by u/bboe",
        check_for_async=False
    )

    scopes = reddit.auth.scopes()
    if scopes == {"*"}:
        print(f"{reddit.user.me()} is authenticated with all scopes")
    elif "identity" in scopes:
        print(f"{reddit.user.me()} is authenticated with the following scopes: {scopes}")
    else:
        print(f"You are authenticated with the following scopes: {scopes}")

    print(f"Read-only is {reddit.read_only}")

    sub = reddit.subreddit('+'.join(SOURCE_SUBS))  # + to specify multiple subreddits

    if read_mode == 'new':
        for submission in sub.new(limit=limit):
            handle_submission(submission, crosspost=crosspost, crosspost_to=CROSSPOST_TO)
    elif read_mode == 'hot':
        for submission in sub.hot(limit=limit):
            handle_submission(submission, crosspost=crosspost, crosspost_to=CROSSPOST_TO)
    elif read_mode == 'rising':
        for submission in sub.rising(limit=limit):
            handle_submission(submission, crosspost=crosspost, crosspost_to=CROSSPOST_TO)
    elif read_mode == 'stream':
        posts_read = 0
        for submission in sub.stream.submissions(skip_existing=True, pause_after=pause_after):
            if submission is None:
                print(f"Stream paused after {pause_after} requests.")
                break
            
            handle_submission(submission, crosspost=crosspost, crosspost_to=CROSSPOST_TO)

            posts_read += 1
            if posts_read >= limit:
                break



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read reddit titles and infer location.")
    parser.add_argument('--mode',
                        dest='mode',
                        required=True,
                        choices=['new', 'hot', 'stream', 'rising'],
                        default='new',
                        help='Mode of reading subreddit: stream, new, etc.')
    parser.add_argument('--limit',
                        dest='limit',
                        required=False,
                        default=2,
                        type=int,
                        help='Number of posts to read.')
    parser.add_argument('--crosspost',
                        dest='crosspost',
                        action='store_true',
                        help='Crosspost to a subreddit and reply to that crosspost.')
    parser.add_argument('--no-crosspost',
                        dest='crosspost',
                        action='store_false',
                        help='Read posts without crossposting.')
    parser.set_defaults(crosspost=False)
    parser.add_argument('--pauseafter',
                       dest='pauseafter',
                       required=False,
                       help='Number of stream requests yielding no new items before pause. Never pauses if not specified.')
    args = parser.parse_args()
    main(
        read_mode=args.mode,
        limit=max(1, args.limit),
        crosspost=args.crosspost,
        pause_after=args.pauseafter
    )

