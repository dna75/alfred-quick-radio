#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Alfred workflow "Radio": pick, add, search and play internet radio stations with mpv.

  radio.py list "<query>"   -> Script Filter JSON (stations, 'add ...' and 'find ...' modes)
  radio.py run  "<json>"    -> performs the chosen action (play / stop / add / remove / copy / open)

Stations live in stations.json in the workflow data folder (created from stations.default.json).
Playback is a plain mpv call: invisible (no window), with the station name as title, an optional logo and an IPC
socket (/tmp/mpvsocket) so other tools can show what is playing.
"""
import sys, os, re, json, time, socket, shutil, subprocess, urllib.request, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("alfred_workflow_data") or os.path.expanduser("~/Library/Application Support/Alfred/Workflow Data/nl.spinnerz.radio")
STATIONS = os.path.join(DATA, "stations.json")
RECENT = os.path.join(DATA, "recent.json")
def find_mpv():
    """mpv from the workflow setting, else the usual Homebrew locations, else PATH. None if not installed."""
    for cand in (os.environ.get("mpv_path"), "/opt/homebrew/bin/mpv", "/usr/local/bin/mpv", shutil.which("mpv")):
        if cand and os.path.exists(os.path.expanduser(cand)):
            return os.path.expanduser(cand)
    return None


MPV = find_mpv()
LOGOS = os.path.expanduser(os.environ.get("logo_folder") or "")
SOCKET = os.environ.get("mpv_socket") or "/tmp/mpvsocket"
API = ["https://de1.api.radio-browser.info", "https://nl1.api.radio-browser.info", "https://at1.api.radio-browser.info"]
ICON = "icon.png"


# ---------------------------------------------------------------- data
def load_stations():
    if not os.path.exists(STATIONS):
        os.makedirs(DATA, exist_ok=True)
        shutil.copy(os.path.join(HERE, "stations.default.json"), STATIONS)
    try:
        return json.load(open(STATIONS))
    except Exception:
        return []


def save_stations(stations):
    os.makedirs(DATA, exist_ok=True)
    json.dump(stations, open(STATIONS, "w"), indent=1, ensure_ascii=False)


def load_recent():
    try:
        return json.load(open(RECENT))
    except Exception:
        return {}


def slug(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def logo_for(st):
    """Path of a logo image for the station (explicit 'logo' field, else matching file name), or None."""
    try:
        files = os.listdir(LOGOS) if LOGOS else []
    except Exception:
        return None
    if st.get("logo") and st["logo"] in files:
        return os.path.join(LOGOS, st["logo"])
    for f in files:
        if f.lower().endswith(".png") and os.path.splitext(f)[0].lower() == slug(st["name"]):
            return os.path.join(LOGOS, f)
    return None


# ---------------------------------------------------------------- mpv
def mpv_ask(sock, command, rid):
    sock.sendall((json.dumps({"command": command, "request_id": rid}) + "\n").encode())
    buf = b""
    end = time.time() + 0.5
    while time.time() < end:
        try:
            buf += sock.recv(4096)
        except socket.timeout:
            break
        for line in buf.split(b"\n"):
            try:
                d = json.loads(line)
            except Exception:
                continue
            if d.get("request_id") == rid:
                return d.get("data")
    return None


def mpv_state():
    """{'title':..., 'paused':bool} when mpv is running, else None."""
    if not os.path.exists(SOCKET):
        return None
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(0.3)
        s.connect(SOCKET)
        title = mpv_ask(s, ["get_property", "media-title"], 1)
        paused = mpv_ask(s, ["get_property", "pause"], 2)
        s.close()
        return {"title": title or "", "paused": bool(paused)}
    except Exception:
        return None


def play(station):
    if not MPV:
        print("mpv is not installed (brew install mpv)")
        return
    name = os.path.basename(MPV)
    subprocess.run(["/usr/bin/pkill", "-x", name], capture_output=True)
    time.sleep(0.3)
    for app in ("Spotify", "Music"):                     # pause other players
        if subprocess.run(["/usr/bin/pgrep", "-x", app], capture_output=True).returncode == 0:
            subprocess.run(["/usr/bin/osascript", "-e", 'tell application "%s" to pause' % app], capture_output=True)
    cmd = [MPV, "--no-terminal", "--vo=null", "--force-window=no", "--input-ipc-server=" + SOCKET,
           "--force-media-title=" + station["name"]]
    logo = logo_for(station)
    if logo:
        cmd.append("--external-file=" + logo)
    cmd.append(station["url"])
    subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    recent = load_recent()
    recent[station["name"]] = time.time()
    os.makedirs(DATA, exist_ok=True)
    json.dump(recent, open(RECENT, "w"))


# ---------------------------------------------------------------- list mode
def out(items):
    print(json.dumps({"items": items}, ensure_ascii=False))


def act(action, **kw):
    return json.dumps(dict(kw, action=action), ensure_ascii=False)


def station_item(st, playing_title):
    sub = st.get("country", "")
    if playing_title and playing_title.lower() == st["name"].lower():
        sub = (sub + " · " if sub else "") + "▶ playing"
    return {
        "title": st["name"], "subtitle": sub, "icon": {"path": logo_for(st) or ICON}, "autocomplete": st["name"],
        "arg": act("play", name=st["name"], url=st["url"], logo=st.get("logo", "")),
        "mods": {
            "cmd": {"subtitle": "Copy stream URL", "arg": act("copy", url=st["url"], name=st["name"])},
            "alt": {"subtitle": "Remove from my list", "arg": act("remove", name=st["name"])},
            "ctrl": {"subtitle": "Open stations file (edit by hand)", "arg": act("open")},
        },
    }


def now_playing_item(state):
    paused = state["paused"]
    return {"title": ("⏸ Paused: " if paused else "▶ Now playing: ") + (state["title"] or "stream"),
            "subtitle": "↩ stop the radio · or pick another station below", "icon": {"path": ICON}, "arg": act("stop")}


def hint_items(q=""):
    items = []
    if q:
        items.append({"title": "Search online for “%s”" % q, "subtitle": "Find more stations (radio-browser.info)", "autocomplete": "find " + q, "valid": False, "icon": {"path": ICON}})
    items.append({"title": "Add a station…", "subtitle": "Type a name for suggestions, or: add <name> <stream url> [NL]", "autocomplete": "add ", "valid": False, "icon": {"path": ICON}})
    items.append({"title": "Find a station online…", "subtitle": "Type: find <name>", "autocomplete": "find ", "valid": False, "icon": {"path": ICON}})
    return items


def parse_add(rest):
    tokens = rest.split()
    url = next((t for t in tokens if re.match(r"https?://", t)), "")
    if url:
        tokens.remove(url)
    country = ""
    if tokens and re.fullmatch(r"[A-Z]{2}", tokens[-1]):
        country = tokens.pop()
    return " ".join(tokens).strip(), url, country


def clipboard_stream():
    """A URL on the clipboard that looks like a radio stream, else ''."""
    clip = subprocess.run(["/usr/bin/pbpaste"], capture_output=True, text=True).stdout.strip()
    if re.match(r"https?://\S+$", clip) and re.search(r"\.(mp3|aac|m3u8?|pls|ogg|opus)(\?|$)|stream|icecast|shoutcast|radio|live", clip, re.I):
        return clip
    return ""


def add_mode(rest, head):
    name, url, country = parse_add(rest)
    items = []
    if name and url:
        st = dict(name=name, url=url, country=country)
        items.append({"title": "Add “%s”" % name, "subtitle": "%s %s" % (country or "—", url), "icon": {"path": ICON},
                      "arg": act("add", **st), "mods": {"cmd": {"subtitle": "Add and play now", "arg": act("add", play=True, **st)}}})
    # suggestions: stations from radio-browser.info that match the name you are typing
    if len(name) >= 2:
        found, err = search_items(name, 8)
        if found:
            items.append({"title": "Suggestions for “%s”" % name, "subtitle": "Pick one to add it with its stream URL", "valid": False, "icon": {"path": ICON}})
            items += found
        elif not items:
            items.append({"title": "No suggestions for “%s”" % name, "subtitle": "Add a stream URL yourself: add <name> <url> [NL]", "valid": False, "icon": {"path": ICON}})
    clip = clipboard_stream() if (name and not url) else ""
    if clip:
        st = dict(name=name, url=clip, country=country)
        items.append({"title": "Add “%s” with the URL on your clipboard" % name, "subtitle": clip[:80], "icon": {"path": ICON},
                      "arg": act("add", **st), "mods": {"cmd": {"subtitle": "Add and play now", "arg": act("add", play=True, **st)}}})
    if not items:
        sub = "Type a station name for suggestions, or: add <name> <url> [NL]"
        items.append({"title": "Add a station", "subtitle": sub, "valid": False, "icon": {"path": ICON}})
    out(head + items)


def search_items(term, limit=15):
    """Online suggestions from radio-browser.info as Alfred items. Returns (items, error)."""
    qs = urllib.parse.urlencode({"name": term, "limit": limit, "hidebroken": "true", "order": "clickcount", "reverse": "true"})
    data, err = None, ""
    for base in API:
        try:
            req = urllib.request.Request(base + "/json/stations/search?" + qs, headers={"User-Agent": "alfred-radio-workflow/1.0"})
            data = json.load(urllib.request.urlopen(req, timeout=5))
            break
        except Exception as e:
            err = str(e)
    if data is None:
        return [], err or "no connection"
    mine = {s["url"].rstrip("/") for s in load_stations()}
    items, seen = [], set()
    for d in data:
        url = d.get("url_resolved") or d.get("url")
        if not url or url.rstrip("/") in seen:
            continue
        seen.add(url.rstrip("/"))
        st = dict(name=d.get("name", "").strip(), url=url, country=(d.get("countrycode") or "").upper())
        info = " · ".join(x for x in [st["country"], ("%s %s kbps" % (d.get("codec", ""), d.get("bitrate"))).strip() if d.get("bitrate") else d.get("codec", ""), (d.get("tags") or "")[:40]] if x)
        have = url.rstrip("/") in mine
        items.append({"title": st["name"] + ("  ✓" if have else ""), "subtitle": info + ("   (already in your list)" if have else "   ↩ add · ⌘↩ play now"),
                      "icon": {"path": ICON}, "arg": act("add", **st),
                      "mods": {"cmd": {"subtitle": "Play now without adding", "arg": act("play", **st)}}})
    return items, ""


def find_mode(term, head):
    if len(term.strip()) < 2:
        return out(head + [{"title": "Find a station online", "subtitle": "Type at least 2 letters of the name", "valid": False, "icon": {"path": ICON}}])
    items, err = search_items(term)
    if err:
        return out(head + [{"title": "Could not reach radio-browser.info", "subtitle": err[:100], "valid": False, "icon": {"path": ICON}}])
    if not items:
        items = [{"title": "No stations found for “%s”" % term, "valid": False, "icon": {"path": ICON}}]
    out(head + items)


def list_mode(q):
    q = q.strip()
    state = mpv_state()
    head = [now_playing_item(state)] if state else []
    if not MPV:
        head.append({"title": "mpv is not installed", "subtitle": "Install it with: brew install mpv   (then try again)", "valid": False, "icon": {"path": ICON}})
    m = re.match(r"^(add|toevoegen|\+)\s*(.*)$", q, re.I)
    if m:
        return add_mode(m.group(2), head)
    m = re.match(r"^(find|zoek|search|\?)\s*(.*)$", q, re.I)
    if m:
        return find_mode(m.group(2), head)
    if q.lower() in ("stop", "off"):
        return out(head or [{"title": "Nothing is playing", "valid": False, "icon": {"path": ICON}}])
    stations = load_stations()
    recent = load_recent()
    words = q.lower().split()
    def hay(s): return (s["name"] + " " + s.get("country", "")).lower()
    shown = [s for s in stations if all(w in hay(s) for w in words)]
    shown.sort(key=lambda s: (not (words and s["name"].lower().startswith(words[0])), -recent.get(s["name"], 0), s["name"].lower()))
    playing = state["title"] if state else ""
    items = [station_item(s, playing) for s in shown]
    out(head + items + (hint_items(q) if (words and len(items) < 4) or not words else []))


# ---------------------------------------------------------------- run mode
def run_mode(arg):
    if arg.strip() == "stop":
        arg = act("stop")
    try:
        d = json.loads(arg)
    except Exception:
        return
    a = d.get("action")
    if a == "play":
        play(d)
    elif a == "stop":
        subprocess.run(["/usr/bin/pkill", "-x", os.path.basename(MPV or "mpv")], capture_output=True)
    elif a == "add":
        stations = load_stations()
        known = next((s for s in stations if s["url"].rstrip("/") == d["url"].rstrip("/") or s["name"].lower() == d["name"].lower()), None)
        if known:
            known.update(name=d["name"], url=d["url"], country=d.get("country") or known.get("country", ""))
            print("Updated “%s”" % d["name"])
        else:
            stations.append(dict(name=d["name"], url=d["url"], country=d.get("country", "")))
            print("Added “%s”" % d["name"])
        save_stations(stations)
        if d.get("play"):
            play(d)
    elif a == "remove":
        stations = [s for s in load_stations() if s["name"] != d["name"]]
        save_stations(stations)
        print("Removed “%s”" % d["name"])
    elif a == "copy":
        subprocess.run(["/usr/bin/pbcopy"], input=d["url"], text=True)
        print("Copied the URL of “%s”" % d.get("name", "station"))
    elif a == "open":
        load_stations()
        subprocess.run(["/usr/bin/open", "-t", STATIONS])


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "list"
    arg = sys.argv[2] if len(sys.argv) > 2 else ""
    list_mode(arg) if mode == "list" else run_mode(arg)
