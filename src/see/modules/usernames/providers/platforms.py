"""Platform registry for username search (Sherlock-style).

Each platform defines how to detect whether a username exists:

- ``method == "status"``: user exists if HTTP status is 200, not found if 404.
- ``method == "text"``: site always returns 200; check body for ``error_text``.
- ``method == "manual"``: unreliable automated check; provide URL for manual review.

Sites that block bots (403) are best left as ``manual`` or will be reported
as ``error`` during a scan.
"""

from __future__ import annotations

from typing import Any

PLATFORMS: list[dict[str, Any]] = [
    # =========================================================================
    # Method: status (reliable HTTP status code detection)
    # =========================================================================
    {"name": "github", "url": "https://github.com/{username}", "method": "status"},
    {"name": "gitlab", "url": "https://gitlab.com/{username}", "method": "status"},
    {"name": "bitbucket", "url": "https://bitbucket.org/{username}/", "method": "status"},
    {"name": "reddit", "url": "https://www.reddit.com/user/{username}", "method": "status"},
    {"name": "steam", "url": "https://steamcommunity.com/id/{username}", "method": "status"},
    {"name": "twitch", "url": "https://www.twitch.tv/{username}", "method": "status"},
    {"name": "telegram", "url": "https://t.me/{username}", "method": "status"},
    {"name": "keybase", "url": "https://keybase.io/{username}", "method": "status"},
    {"name": "spotify", "url": "https://open.spotify.com/user/{username}", "method": "status"},
    {"name": "medium", "url": "https://medium.com/@{username}", "method": "status"},
    {"name": "vimeo", "url": "https://vimeo.com/{username}", "method": "status"},
    {"name": "dribbble", "url": "https://dribbble.com/{username}", "method": "status"},
    {"name": "behance", "url": "https://www.behance.net/{username}", "method": "status"},
    {"name": "deviantart", "url": "https://www.deviantart.com/{username}", "method": "status"},
    {"name": "fiverr", "url": "https://www.fiverr.com/{username}", "method": "status"},
    {"name": "askfm", "url": "https://ask.fm/{username}", "method": "status"},
    {"name": "codecademy", "url": "https://www.codecademy.com/profiles/{username}", "method": "status"},
    {"name": "pastebin", "url": "https://pastebin.com/u/{username}", "method": "status"},
    {"name": "periscope", "url": "https://www.periscope.tv/{username}", "method": "status"},
    {"name": "replit", "url": "https://replit.com/@{username}", "method": "status"},
    {"name": "soundcloud", "url": "https://soundcloud.com/{username}", "method": "status"},
    {"name": "wattpad", "url": "https://www.wattpad.com/user/{username}", "method": "status"},
    {"name": "wordpress", "url": "https://{username}.wordpress.com", "method": "status"},
    {"name": "roblox", "url": "https://www.roblox.com/user.aspx?username={username}", "method": "status"},
    {"name": "mastodon", "url": "https://mastodon.social/@{username}", "method": "status"},
    {"name": "vk", "url": "https://vk.com/{username}", "method": "status"},
    {"name": "tumblr", "url": "https://{username}.tumblr.com", "method": "status"},
    {"name": "hackernews", "url": "https://news.ycombinator.com/user?id={username}", "method": "status"},
    {"name": "snapchat", "url": "https://www.snapchat.com/add/{username}", "method": "status"},
    {"name": "pinterest", "url": "https://www.pinterest.com/{username}/", "method": "status"},
    {"name": "blogger", "url": "https://{username}.blogspot.com", "method": "status"},
    {"name": "devto", "url": "https://dev.to/{username}", "method": "status"},
    {"name": "codepen", "url": "https://codepen.io/{username}", "method": "status"},
    {"name": "mixcloud", "url": "https://www.mixcloud.com/{username}/", "method": "status"},
    {"name": "wikipedia", "url": "https://en.wikipedia.org/wiki/User:{username}", "method": "status"},
    {"name": "youpic", "url": "https://youpic.com/photographer/{username}", "method": "status"},
    {"name": "coderwall", "url": "https://coderwall.com/{username}", "method": "status"},
    {"name": "ello", "url": "https://ello.co/{username}", "method": "status"},
    {"name": "instructables", "url": "https://www.instructables.com/member/{username}/", "method": "status"},
    {"name": "kickstarter", "url": "https://www.kickstarter.com/profile/{username}", "method": "status"},
    {"name": "patreon", "url": "https://www.patreon.com/{username}", "method": "status"},
    {"name": "producthunt", "url": "https://www.producthunt.com/@{username}", "method": "status"},
    {"name": "buymeacoffee", "url": "https://www.buymeacoffee.com/{username}", "method": "status"},
    {"name": "aboutme", "url": "https://about.me/{username}", "method": "status"},
    {"name": "trello", "url": "https://trello.com/{username}", "method": "status"},
    {"name": "canva", "url": "https://www.canva.com/{username}", "method": "status"},
    {"name": "ifttt", "url": "https://ifttt.com/p/{username}", "method": "status"},
    {"name": "itchio", "url": "https://{username}.itch.io", "method": "status"},
    {"name": "lastfm", "url": "https://www.last.fm/user/{username}", "method": "status"},
    {"name": "paypalme", "url": "https://www.paypal.me/{username}", "method": "status"},
    {"name": "xboxgamertag", "url": "https://xboxgamertag.com/search/{username}", "method": "status"},

    # =========================================================================
    # Method: text (site returns 200; detect not-found via body text)
    # =========================================================================
    {
        "name": "instagram",
        "url": "https://www.instagram.com/{username}/",
        "method": "text",
        "error_text": "Sorry, this page isn't available",
    },
    {
        "name": "twitter",
        "url": "https://twitter.com/{username}",
        "method": "text",
        "error_text": "This account doesn't exist",
        "headers": {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
    },
    {
        "name": "youtube",
        "url": "https://www.youtube.com/@{username}",
        "method": "text",
        "error_text": "not found",
        "headers": {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
    },

    # =========================================================================
    # Method: manual (provide URL for manual review)
    # =========================================================================
    {
        "name": "facebook",
        "url": "https://www.facebook.com/{username}",
        "method": "manual",
        "note": "Facebook blocks automated checks; verify manually.",
    },
    {
        "name": "tiktok",
        "url": "https://www.tiktok.com/@{username}",
        "method": "manual",
        "note": "TikTok heavily blocks bots; verify manually.",
    },
    {
        "name": "linkedin",
        "url": "https://www.linkedin.com/in/{username}",
        "method": "manual",
        "note": "LinkedIn blocks automated checks; verify manually.",
    },
    {
        "name": "discord",
        "url": "https://discord.com/users/{username}",
        "method": "manual",
        "note": "Discord requires user IDs; verify manually.",
    },
]
