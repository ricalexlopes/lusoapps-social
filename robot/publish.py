#!/usr/bin/env python3
"""Publish the posts placed in approved/ to the brand's Facebook page and its linked Instagram account.

Each approved/<name>.json is a post (brand, text, image or image_url). After publishing, approved/<name>.result.json
records the post ids (never the keys). A post that already has a result file is never published again.

Keys come from the environment only (FB_TOKEN_SWIMHEAT, FB_TOKEN_FLIGHTHOME, FB_TOKEN_STORMHOME) and are never printed.
"""
import glob, json, os, sys, time, urllib.parse, urllib.request, urllib.error, datetime as dt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = "https://raw.githubusercontent.com/ricalexlopes/lusoapps-social/main/"
G = "https://graph.facebook.com/v21.0/"
TOKENS = {"swimheat": "FB_TOKEN_SWIMHEAT", "flighthome": "FB_TOKEN_FLIGHTHOME", "stormhome": "FB_TOKEN_STORMHOME"}

def call(method, path, token, **params):
    params["access_token"] = token
    data = urllib.parse.urlencode(params).encode()
    if method == "GET":
        req = urllib.request.Request(G + path + "?" + data.decode())
    else:
        req = urllib.request.Request(G + path, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read().decode()).get("error", {})
        except Exception:
            err = {}
        raise RuntimeError(f"Graph API {e.code}: {err.get('message', '')[:200]} (code {err.get('code')})") from None

def publish(post, token):
    image = post.get("image_url") or (RAW + post["image"])
    me = call("GET", "me", token, fields="id,name,instagram_business_account{id,username}")
    page_id, ig = me["id"], (me.get("instagram_business_account") or {})
    res = {"page": me.get("name"), "published_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    fb = call("POST", f"{page_id}/photos", token, url=image, caption=post["text"], published="true")
    res["facebook_post_id"] = fb.get("post_id") or fb.get("id")
    if ig.get("id"):
        c = call("POST", f"{ig['id']}/media", token, image_url=image, caption=post["text"])
        for _ in range(20):
            st = call("GET", c["id"], token, fields="status_code").get("status_code")
            if st == "FINISHED":
                break
            if st == "ERROR":
                raise RuntimeError("Instagram could not process the image")
            time.sleep(3)
        m = call("POST", f"{ig['id']}/media_publish", token, creation_id=c["id"])
        res["instagram"] = ig.get("username")
        res["instagram_media_id"] = m.get("id")
    else:
        res["instagram"] = "no Instagram account linked to the page"
    return res

def main():
    files = sorted(f for f in glob.glob(os.path.join(ROOT, "approved", "*.json")) if not f.endswith(".result.json"))
    failed = 0
    for f in files:
        out = f[:-5] + ".result.json"
        if os.path.exists(out):
            continue
        post = json.load(open(f, encoding="utf-8"))
        token = os.environ.get(TOKENS.get(post.get("brand", ""), ""), "")
        name = os.path.basename(f)
        if not token:
            print(f"{name}: no key for brand '{post.get('brand')}' - not published"); failed += 1
            continue
        try:
            r = publish(post, token)
            json.dump(r, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print(f"{name}: published -> {json.dumps(r, ensure_ascii=False)}")
        except Exception as ex:
            failed += 1
            json.dump({"error": str(ex), "at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")},
                      open(f[:-5] + ".error.json", "w"), indent=1)
            print(f"{name}: FAILED - {ex}")
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())
