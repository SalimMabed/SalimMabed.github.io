import os
import json
import time

try:
    from linkedin_api import Linkedin
except ImportError:
    print("linkedin-api not installed")
    raise SystemExit(1)

email = os.environ.get("LINKEDIN_EMAIL")
password = os.environ.get("LINKEDIN_PASSWORD")
profile_id = "salim-mabed-27308a227"

if not email or not password:
    print("Missing LINKEDIN_EMAIL or LINKEDIN_PASSWORD")
    raise SystemExit(1)


def extract_text(post):
    """Try multiple response shapes from linkedin-api."""
    # Shape 1: commentary.text.text
    c = post.get("commentary", {})
    if isinstance(c, dict):
        t = c.get("text", {})
        if isinstance(t, dict):
            return t.get("text", "")
        if isinstance(t, str):
            return t
    if isinstance(c, str):
        return c

    # Shape 2: specificContent (ugcPost)
    share = (
        post.get("specificContent", {})
        .get("com.linkedin.ugc.ShareContent", {})
    )
    text = share.get("shareCommentary", {}).get("text", "")
    if text:
        return text

    return ""


def extract_reactions(post):
    social = post.get("socialDetail", {})
    if isinstance(social, dict):
        counts = social.get("totalSocialActivityCounts", {})
        if isinstance(counts, dict):
            return counts.get("numLikes", 0)
    return 0


try:
    api = Linkedin(email, password)
    posts = api.get_profile_posts(profile_id, post_count=10) or []

    result = {"updated_at": int(time.time()), "post": None}

    for post in posts:
        text = extract_text(post).strip()
        if len(text) < 15:
            continue

        urn = post.get("entityUrn", "")
        url = (
            f"https://www.linkedin.com/feed/update/{urn}/"
            if urn
            else f"https://www.linkedin.com/in/{profile_id}/"
        )

        ts = post.get("createdAt", 0)
        if ts > 1e12:
            ts = int(ts // 1000)

        result["post"] = {
            "text": text,
            "url": url,
            "created_at": ts,
            "reactions": extract_reactions(post),
        }
        break

    with open("latest-post.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    if result["post"]:
        print(f"✓ Post updated: {result['post']['text'][:80]}…")
    else:
        print("✓ No suitable post found — file updated with null")

except Exception as exc:
    print(f"Error: {exc}")
    import traceback; traceback.print_exc()
    if not os.path.exists("latest-post.json"):
        with open("latest-post.json", "w") as f:
            json.dump({"updated_at": int(time.time()), "post": None}, f)
    raise SystemExit(1)
