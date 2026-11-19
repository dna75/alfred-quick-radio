# Forum post (Alfred community: Share your workflows). Posted 19 Nov 2026: https://www.alfredforum.com/topic/24225-quick-radio-pick-add-and-search-internet-radio-stations-played-with-mpv/

**Title:** Quick Radio – pick, add and search internet radio stations, played with mpv

Hi all,

I rebuilt my radio workflow from scratch. It plays internet radio through an invisible mpv (no window, no Dock icon), and it makes adding stations easy: suggestions appear while you type.

**Keywords** (configurable)
- `rd` – your stations, last played first; type to filter by name or country (`rd be`, `rd radio 2`)
- `rd add radio 538` – add a station; suggestions from radio-browser.info appear while you type, Enter adds one with its stream URL
- `rd add My Station https://example.com/stream.mp3 NL` – add a station with your own stream URL
- `rd find jazz` – search stations online; Enter adds, Cmd+Enter plays right away
- `qr` – stop the radio

**Actions on a station**
- Enter – play
- Cmd+Enter – copy the stream URL
- Opt+Enter – remove it from your list
- Ctrl+Enter – open the stations file (plain JSON) to edit by hand

While something plays, the first result shows what it is; Enter on it stops the radio. Starting a station pauses Spotify and Music.

**Notes**
- Needs mpv: `brew install mpv`. Also Python 3 (`/usr/bin/python3`).
- Your list is stored in the workflow data folder, so updating never overwrites it. Optional logos per station (PNG) show in the list.
- The only thing sent anywhere is the text you type after `add` or `find`, which is looked up on radio-browser.info.
- The starter list is short (NL, BE, ES, UK); some streams may be offline, so use `rd find` to replace them.

**Disclosure:** this workflow was created with the help of an AI assistant (Claude by Anthropic) and tested by me.

Download: https://github.com/dna75/alfred-quick-radio/releases/latest (source and details on GitHub). Feedback and bug reports welcome!
