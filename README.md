<h1 align="center">Welcome to pinboard-bookmarks-updater 👋</h1>
<p>
  <img alt="Version" src="https://img.shields.io/badge/version-0.1.0-blue.svg?cacheSeconds=2592000" />
  <a href="https://github.com/jefftriplett/pinboard-bookmarks-updater" target="_blank">
    <img alt="Documentation" src="https://img.shields.io/badge/documentation-yes-brightgreen.svg" />
  </a>
  <a href="https://twitter.com/webology" target="_blank">
    <img alt="Twitter: webology" src="https://img.shields.io/twitter/follow/webology.svg?style=social" />
  </a>
</p>

> Pinboard Bot

### 🏠 [Homepage](https://github.com/jefftriplett/pinboard-bookmarks-updater)

## Usage

If you are running locally, you'll need to define a few environment variables: 

- `GITHUB_TOKEN`
- `GITHUB_USERNAME`
- `PINBOARD_TOKEN`

### Find duplicates

```sh
$ python main.py remove_dupes
```
### Fix common tag issues
```sh
$ python main.py fix_tags
```

### Apply Titlecase to your links

```sh
$ python main.py fix_titlecase
```

## Author

<!-- [[[cog
import cog
import requests
response = requests.get("https://raw.githubusercontent.com/jefftriplett/actions/main/footer.txt")
response.raise_for_status()
print(response.text.strip())
]]] -->
## Author

👤 **Jeff Triplett**

* Website: https://jefftriplett.com
* Mastodon: [@webology](https://mastodon.social/@webology)
* Twitter: [@webology](https://twitter.com/webology)
* GitHub: [@jefftriplett](https://github.com/jefftriplett)

## Show your support

Give a ⭐️ if this project helped you!
<!-- [[[end]]] -->
