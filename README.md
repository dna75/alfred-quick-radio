# Quick Radio for Alfred

Listen to internet radio from [Alfred](https://www.alfredapp.com): pick a station, add your own, or search thousands of stations online, all from one keyword. Playback runs in an invisible [mpv](https://mpv.io) player, so there is no window, no Dock icon and no browser tab.

![icon](docs/icon.png)

## Install

1. Install mpv: `brew install mpv`
2. Download `Quick.Radio.alfredworkflow` from the [latest release](https://github.com/dna75/alfred-quick-radio/releases/latest) and double-click it. Requires the Alfred Powerpack.

## Usage

| You type | What happens |
|---|---|
| `rd` | Your stations, the most recently played first. Type to filter by name or country (`rd be`, `rd radio 2`). |
| `rd add radio 538` | Add a station. Suggestions from [radio-browser.info](https://www.radio-browser.info) appear while you type; <kbd>↩</kbd> adds one with its stream URL. |
| `rd add My Station https://example.com/stream.mp3 NL` | Add a station with your own stream URL (country code optional). If you copied something that looks like a stream URL, the workflow offers to use it. |
| `rd find jazz` | Search stations online. <kbd>↩</kbd> adds the station to your list, <kbd>⌘</kbd><kbd>↩</kbd> plays it right away without adding. |
| `qr` | Stop the radio. |

On a station in the list:

- <kbd>↩</kbd> play
- <kbd>⌘</kbd><kbd>↩</kbd> copy the stream URL
- <kbd>⌥</kbd><kbd>↩</kbd> remove it from your list
- <kbd>⌃</kbd><kbd>↩</kbd> open the stations file to edit it by hand

While something plays, the first result shows what it is (`▶ Now playing: …`); <kbd>↩</kbd> on it stops the radio.

## Your stations

The workflow starts with a small list of Dutch, Belgian, Spanish and UK stations. Streams change over time, so if one stops working, remove it or add a new one with `rd find`. Your list is a plain JSON file:

```
~/Library/Application Support/Alfred/Workflow Data/nl.spinnerz.radio/stations.json
```

```json
[
  { "name": "Radio 2", "url": "https://icecast.omroep.nl/radio2-bb-mp3", "country": "NL" },
  { "name": "My Station", "url": "https://example.com/stream.mp3", "country": "", "logo": "mystation.png" }
]
```

`logo` is optional (see *Logos* below). The file is created on first use, so updating the workflow never overwrites your list.

## Configuration

Alfred Preferences → Workflows → Quick Radio → Configure Workflow:

- **Keyword**: `rd` by default.
- **mpv**: path to mpv. The usual Homebrew locations and your `PATH` are searched automatically.
- **Logo folder**: optional. A folder with PNG logos named after the station (`radio2.png` for "Radio 2": lowercase, no spaces or punctuation), or any file name set in the station's `logo` field. Logos show in the list and are loaded into mpv as cover art.

## How it works

A station starts with a plain mpv call: no window, the station name as title and an optional logo as cover art. The player also opens an IPC socket at `/tmp/mpvsocket`, which the workflow uses to show what is playing; other tools can read it too. When a station starts, any other mpv stream is replaced and Spotify and Music are paused (if they are playing).

## Privacy

Everything stays on your Mac, except when you add or search by name: the text you type after `add` or `find` is sent to the public radio-browser.info directory to look up stations. Nothing else is sent anywhere. Radio streams themselves connect directly from mpv to the broadcaster.

## Requirements

- macOS, Alfred 5 with the Powerpack
- [mpv](https://mpv.io) (`brew install mpv`)
- Python 3 (Apple's, part of the Command Line Tools, or Homebrew's). The workflow uses `/usr/bin/python3`.

## Limitations

- The starter list is short and some streams may be offline by now; use `rd find` to replace them.
- Stations that only offer a web player page (no direct stream) cannot be played by mpv.
- Previous versions of this workflow played through QuickTime Player; that version is still in the git history.

## Disclosure

This workflow was created with the help of an AI assistant (Claude by Anthropic) and tested by the author.
