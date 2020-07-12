# import click
import pinboard
import requests
import typer

from bs4 import BeautifulSoup
from envparse import Env
from pathlib import Path
from stop_words import safe_get_stop_words
from titlecase import titlecase
from unidecode import unidecode
from yarl import URL


env = Env(GITHUB_USERNAME=str, GITHUB_TOKEN=str, PINBOARD_TOKEN=str)

GITHUB_TOKEN = env.str("GITHUB_TOKEN")
GITHUB_USERNAME = env.str("GITHUB_USERNAME")
PINBOARD_TOKEN = env.str("PINBOARD_TOKEN")

IGNORE_WORDS = set(
    [word.lower() for word in Path("IGNORE_WORDS.txt").read_text().split()]
)

STOP_WORDS = set([word.lower() for word in Path("STOP_WORDS.txt").read_text().split()])
STOP_WORDS.update(set(safe_get_stop_words("english")))

IGNORE_TAGS = IGNORE_WORDS | STOP_WORDS


def get_dev_to_info_for_url(url):
    try:
        req = requests.get(url, timeout=1.0)
        soup = BeautifulSoup(req.text, "html.parser")
        data = {
            "tags": [
                tag.text.lstrip("#") for tag in soup.find_all("a", {"class": "tag"})
            ]
        }
        return data

    except Exception as e:
        print(e)
        return {}


def get_github_info_for_url(url):
    bits = url.replace("https://github.com/", "").split("/")
    owner, repo = bits[0], bits[1]
    url = "https://api.github.com/repos/{owner}/{repo}".format(owner=owner, repo=repo)
    req = requests.get(
        url,
        auth=(GITHUB_USERNAME, GITHUB_TOKEN),
        headers={"Accept": "application/vnd.github.mercy-preview+json"},
        timeout=1.0,
    )
    try:
        return req.json()
    except Exception as e:
        print(e)
        return {}


def normalize_tags(original_tags, ignore_meta_tags=False):
    tags = [unidecode(tag.lower()) for tag in original_tags if len(tag)]

    if ignore_meta_tags:
        tags = [tag for tag in tags if ":" not in tag]

    tags = set(tags).difference(IGNORE_TAGS)

    return tags


class Bookmarks(object):
    def __init__(self, pinboard_token, start=0, count=20):
        self.pinboard_token = pinboard_token
        self.pinboard = pinboard.Pinboard(pinboard_token)
        self.count = count
        self.start = start

    """
    TODO:

    Implement a clean() and clean_fieldname() approach to help normalize
    our bookmark model.
    - Store the initial values.
    - Run the clean script.
      - clean
      - clean_fieldname
    - Mark bookmark as modified.
    - If the link changed, delete the old, and replace the url.
    - Save bookmark.
    """

    def get_bookmarks(self, start=None, count=None):
        return self.pinboard.posts.all(
            start=start or self.start, results=count or self.count
        )

    def fix_tags(self, start=None, count=None):

        links = self.get_bookmarks(start=start, count=count)

        for link in links:
            dirty = False
            try:
                description = unidecode(link.description)
                titlecase_description = titlecase(description)
                extended = link.extended = unidecode(link.extended)
                url = URL(link.url)

                """
                TODO: Add better support for common websites like:
                - dev.to
                - github.com
                - medium.com

                Possible features:
                - more accurate tags
                - check for meta descriptions
                """
                if url.host == "github.com":
                    github = get_github_info_for_url(link.url)
                    github_tags = set(github.get("topics", []))
                    description = github.get("full_name")
                    titlecase_description = titlecase(description)
                    github_description = github.get("description")
                    extended = (
                        "> {0}".format(github_description)
                        if github_description
                        else link.extended
                    )

                    # Github projects should be visible...
                    if not link.shared:
                        link.shared = True
                        dirty = True

                    if len(link.description) == 0 or link.description == "github.com":
                        link.description = titlecase_description
                        dirty = True

                    if len(link.extended) == 0:
                        link.extended = extended
                        dirty = True

                # dev.to articles should be shared by default...
                elif url.host == "dev.to":
                    devto_data = get_dev_to_info_for_url(link.url)
                    github_tags = set(devto_data.get("tags", []))

                    if not link.shared:
                        link.shared = True
                        dirty = True

                    if "- DEV" in link.description:
                        link.description = (link.description.split("- DEV")[0]).strip()
                        dirty = True

                    if not github_tags.issubset(set(link.tags)):
                        dirty = True

                else:
                    github_tags = set([])

                if len(description.split(" ")) == 1 and url.host is not "github.com":
                    typer.secho("description is blank", fg="red")
                    try:
                        doc = requests.get(link.url, timeout=1.0)
                        soup = BeautifulSoup(doc.text, "html.parser")
                        description = soup.find("title").text
                        link.description = description
                        dirty = True

                    except (Exception, requests.exceptions.Timeout) as e:
                        typer.secho(e, fg="red")

                if len(link.extended) == 0:
                    typer.secho("extended is blank", fg="red")
                    try:
                        doc = requests.get(link.url, timeout=1.0)
                        soup = BeautifulSoup(doc.text, "html.parser")
                        try:
                            content = ""

                            if soup.find("meta", {"name": "description"}):
                                content = soup.find(
                                    "meta", {"name": "description"}
                                ).get("content")

                            if soup.find("meta", {"name": "description"}):
                                content = soup.find(
                                    "meta", {"name": "description"}
                                ).get("value")

                            if soup.find("meta", {"property": "og:description"}):
                                content = soup.find(
                                    "meta", {"property": "og:description"}
                                ).get("content")

                            if content:
                                # TODO: Split this out by the first paragraph
                                link.extended = f"> {content.strip()}"
                                typer.echo(link.extended)
                                dirty = True

                        except AttributeError as e:
                            print(e)
                            # try:
                            #     content = soup.find('meta', {'property': 'og:description'}).get('content')
                            #     link.extended = f'> {content}'
                            #     typer.echo(link.extended)
                            #     dirty = True
                            # except AttributeError:
                            #     pass
                            pass

                    except (Exception, requests.exceptions.Timeout) as e:
                        typer.secho(e, fg="red")

                    # link.extended = titlecase_description
                    # dirty = True

                # Sets
                tags = set(normalize_tags(link.tags))
                suggested = self.pinboard.posts.suggest(url=link.url)
                popular, recommended = suggested
                popular = normalize_tags(popular.get("popular"), ignore_meta_tags=True)
                recommended = normalize_tags(
                    recommended.get("recommended"), ignore_meta_tags=True
                )
                new_tags = list(tags | popular | recommended | github_tags)

                if len(new_tags) != len(tags) or dirty:
                    typer.echo("saving... {}".format(link.url))
                    typer.echo("description: {}".format(titlecase_description))
                    if extended:
                        typer.echo("extended: {}".format(extended))
                    typer.echo("my tags: {}".format(tags))
                    typer.echo("updating to: {}".format(new_tags))

                    try:
                        link.tags = new_tags
                        link.save()

                    except UnicodeEncodeError:
                        try:
                            link.description = description
                            link.extended = extended
                            link.save()
                        except Exception as e:
                            typer.echo("=" * 100)
                            typer.echo(e)
                            typer.echo(type(e))
                            typer.echo("=" * 100)

                    except Exception as e:
                        typer.echo("=" * 100)
                        typer.echo(e)
                        typer.echo(type(e))
                        typer.echo("=" * 100)

            except Exception as e:
                typer.echo("=" * 100)
                typer.echo(e)
                typer.echo(type(e))
                typer.echo("=" * 100)

    def fix_titlecase(self, start=None, count=None):

        links = self.get_bookmarks(start=start, count=count)

        for link in links:
            description = unidecode(link.description)
            titlecase_description = titlecase(description)
            extended = unidecode(link.extended)

            if description != titlecase_description:
                typer.echo("description: {}".format(description))
                typer.echo("description: {}".format(titlecase_description))

                try:
                    link.description = titlecase_description
                    link.save()

                except UnicodeEncodeError:
                    try:
                        link.description = titlecase_description
                        link.extended = extended
                        link.save()
                    except UnicodeEncodeError:
                        typer.echo("*" * 60)
                        typer.echo(
                            "description: {}".format(unidecode(link.description))
                        )
                        typer.echo("extended: {}".format(unidecode(link.extended)))
                        typer.echo("url: {}".format(link.url))
                        typer.echo("tags: {}".format(set(normalize_tags(link.tags))))
                        typer.echo("*" * 60)

                except Exception as e:
                    typer.echo("=" * 100)
                    typer.echo(e)
                    typer.echo(type(e))
                    typer.echo(link.url)
                    typer.echo("=" * 100)

    def remove_dupes(self, start=None, count=None):

        links = self.get_bookmarks(start=start, count=count)

        for link in links:
            tags = link.tags
            tags = [
                tag for tag in tags if len(tags) and tag.startswith(("http", "https"))
            ]
            tag = tags[0] if len(tags) else ""

            if tag.startswith(("http", "https")) and tag not in ["http", "https"]:
                typer.echo("description: {}".format(unidecode(link.description)))
                typer.echo("extended: {}".format(unidecode(link.extended)))
                typer.echo("url: {}".format(link.url))
                typer.echo("tags: {}".format(tags))
                typer.echo("tag: {}".format(tag))

                if tag.startswith("http://xn--%20https:-dk9c//"):
                    tag = tag.replace("http://xn--%20https:-dk9c//", "https://")

                new_description = link.description
                new_url = tag

                link.delete()

                if new_url.startswith("http://xn--%20https:-dk9c//"):
                    new_url = new_url.replace("http://xn--%20https:-dk9c//", "https://")

                self.pinboard.posts.add(
                    url=new_url, description=unidecode(new_description), private=True
                )

                typer.echo("---")


# CLI api
app = typer.Typer()


@app.command("fix_tags")
def fix_tags(start: int = 0, count: int = 10):
    typer.secho("fix_tags()...", fg="green")

    bookmarks = Bookmarks(PINBOARD_TOKEN)
    bookmarks.fix_tags(start, count)


@app.command("fix_titlecase")
def fix_titlecase(start: int = 0, count: int = 10):
    typer.secho("fix_titlecase()...", fg="green")

    bookmarks = Bookmarks(PINBOARD_TOKEN)
    bookmarks.fix_titlecase(start, count)


@app.command("remove_dupes")
def remove_dupes(start: int = 0, count: int = 10):
    typer.secho("remove_dupes()...", fg="green")

    bookmarks = Bookmarks(PINBOARD_TOKEN)
    bookmarks.remove_dupes(start, count)


if __name__ == "__main__":
    app()
