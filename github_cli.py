"""GitHub CLI Client - Interactive Terminal UI."""
import os, sys
if sys.platform == "win32":
    os.system("chcp 65001 > nul 2>&1")
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
import json, time, requests
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
from i18n import LANG

CONFIG_DIR = Path.home() / ".github_cli"
CONFIG_FILE = CONFIG_DIR / "config.json"
GITHUB_API = "https://api.github.com"

class GitHubCLI:
    PER_PAGE = 15

    def __init__(self):
        self.console = Console(force_terminal=True, legacy_windows=False)
        self.lang = "en"
        self.token = None
        self.username = None
        self.headers = None
        self.config = {}
        self._load_config()

    @property
    def t(self):
        return LANG[self.lang]

    # ── Config ──

    def _load_config(self):
        if CONFIG_FILE.exists():
            try:
                self.config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                self.lang = self.config.get("lang", "en")
                self.token = self.config.get("token", "")
                self.username = self.config.get("username", "")
            except Exception:
                self.config = {}
        else:
            self._first_run_language_select()
        self._build_headers()

    def _build_headers(self):
        if self.token:
            self.headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        else:
            self.headers = None

    def _save_config(self):
        self.config = {"lang": self.lang, "token": self.token, "username": self.username}
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(self.config, ensure_ascii=False, indent=2), encoding="utf-8")

    def _first_run_language_select(self):
        self.console.clear()
        self.console.print(r"""
[bold cyan]
     G    I   T   H   U   B
     ─── C L I   C L I E N T ───
[/bold cyan]""")
        self.console.print(Panel(
            "[bold white]GitHub CLI Client[/]\n[dim]Terminal Visual GitHub Client[/]",
            title="Welcome", border_style="bright_blue", padding=(1, 4)))
        self.console.print()
        self.lang = Prompt.ask(
            "[bold cyan]?[/] Choose language / 选择语言",
            choices=["en", "zh"], default="en")
        self._save_config()

    # ── API ──

    def _api(self, method, endpoint, data=None, params=None):
        if not self.headers:
            return None
        url = f"{GITHUB_API}{endpoint}"
        try:
            resp = requests.request(method, url, headers=self.headers,
                                   json=data, params=params, timeout=30)
            if resp.status_code == 401:
                self.console.print(f"[bold red]{self.t['token_invalid']}[/]")
                self.token = None; self.username = None; self.headers = None
                self._save_config()
                return None
            if resp.status_code == 403 and "rate limit" in resp.text.lower():
                self.console.print(f"[bold yellow]{self.t['rate_limit']}[/]")
                return None
            resp.raise_for_status()
            return resp
        except requests.exceptions.HTTPError as e:
            try:
                err = e.response.json().get("message", str(e))
            except Exception:
                err = str(e)
            self.console.print(f"[red]{self.t['error'].format(error=err)}[/]")
            return None
        except Exception as e:
            self.console.print(f"[red]{self.t['error'].format(error=str(e))}[/]")
            return None

    def _fetch_user(self):
        resp = self._api("GET", "/user")
        if resp:
            user = resp.json()
            self.username = user.get("login", "")
            self._save_config()
            return user
        return None

    def _fetch_repos(self, sort="updated", page=1):
        params = {"sort": sort, "per_page": self.PER_PAGE, "page": page, "type": "owner"}
        resp = self._api("GET", "/user/repos", params=params)
        if resp is None:
            return [], 0
        repos = resp.json()
        total_pages = 1
        link_header = resp.headers.get("Link", "")
        if 'rel="last"' in link_header:
            try:
                last_url = [p for p in link_header.split(",") if 'rel="last"' in p][0]
                total_pages = int(last_url.split("page=")[-1].split(">")[0])
            except Exception:
                pass
        return repos, total_pages

    def _fetch_repo_detail(self, owner, repo):
        resp = self._api("GET", f"/repos/{owner}/{repo}")
        return resp.json() if resp else None

    def _create_repo(self, name, description, private):
        data = {"name": name, "description": description, "private": private, "auto_init": True}
        resp = self._api("POST", "/user/repos", data=data)
        return resp.json() if resp else None

    def _delete_repo(self, owner, repo):
        resp = self._api("DELETE", f"/repos/{owner}/{repo}")
        return resp is not None

    def _update_repo(self, owner, repo, data):
        resp = self._api("PATCH", f"/repos/{owner}/{repo}", data=data)
        return resp.json() if resp else None

    # ── UI Helpers ──

    def _clear(self):
        self.console.clear()

    def _print_header(self, title=None):
        header = Text()
        header.append(" GitHub CLI ", style="bold bright_cyan on blue")
        if self.username:
            header.append(f" | @{self.username}", style="bold green")
        self.console.print(Panel(header, border_style="bright_blue", padding=(0, 2)))
        if title:
            self.console.print()
            self.console.print(f"  [bold white]{title}[/]")
            self.console.print(f"  {'─' * 56}", style="dim")
            self.console.print()

    def _wait_back(self):
        Prompt.ask(f"\n[dim]{self.t['back']}[/]")
        return True

    def _format_size(self, kb):
        if kb < 1024:
            return f"{kb} KB"
        return f"{kb / 1024:.1f} MB"

    def _format_date(self, dt_str):
        if not dt_str:
            return self.t["none"]
        try:
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return dt_str[:16]

    def _spinner(self, msg):
        with Progress(SpinnerColumn(), TextColumn("[bold blue]{task.description}"),
                      console=self.console, transient=True) as progress:
            progress.add_task(msg, total=None)
            time.sleep(0.3)

    # ── Login ──

    def _do_login(self):
        while True:
            self._clear()
            self._print_header(self.t["login"])
            self.console.print(f"  [cyan]{self.t['token_hint']}[/]")
            self.console.print()
            token = Prompt.ask(f"  [bold]{self.t['enter_token']}[/]", password=True)
            token = token.strip()
            if not token:
                retry_msg = "No token entered. Retry? (y/n)" if self.lang == "en" else "未输入 Token，重试？(y/n)"
                if Confirm.ask(f"  [yellow]{retry_msg}[/]", default=True):
                    continue
                else:
                    return False
            test_headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            try:
                r = requests.get(f"{GITHUB_API}/user", headers=test_headers, timeout=15)
                if r.status_code == 200:
                    user = r.json()
                    self.token = token
                    self.username = user.get("login", "")
                    self._build_headers()
                    self._save_config()
                    self.console.print()
                    self.console.print(
                        f"  [bold green]:heavy_check_mark: {self.t['login_success'].format(name=self.username)}[/]")
                    time.sleep(1.5)
                    return True
                else:
                    self.console.print(f"  [bold red]:x: {self.t['login_fail']}[/]")
                    retry_msg = "Retry? (y/n)" if self.lang == "en" else "重试？(y/n)"
                    if Confirm.ask(f"  [bold]{retry_msg}[/]", default=True):
                        continue
                    else:
                        return False
            except Exception as e:
                self.console.print(f"  [red]{self.t['error'].format(error=str(e))}[/]")
                retry_msg = "Retry? (y/n)" if self.lang == "en" else "重试？(y/n)"
                if Confirm.ask(f"  [bold]{retry_msg}[/]", default=True):
                    continue
                else:
                    return False

    def _do_switch_user(self):
        self.token = None
        self.username = None
        self.headers = None
        self._save_config()
        self._do_login()

    def _do_switch_lang(self):
        self.lang = "zh" if self.lang == "en" else "en"
        self._save_config()
        if self.lang == "en":
            msg = self.t.get("lang_switched_en", "Switched to English.")
        else:
            msg = self.t.get("lang_switched_zh", "已切换为中文。")
        self.console.print(f"\n  [green]:heavy_check_mark: {msg}[/]")
        time.sleep(1)

    def _show_settings(self):
        while True:
            self._clear()
            self._print_header(self.t["settings_menu"])

            current_lang = "English" if self.lang == "en" else "中文"
            self.console.print(f"  [dim]{self.t['lang_current'].format(lang=current_lang)}[/]")
            self.console.print()
            self.console.print(f"    [bold bright_cyan]1[/]  {self.t['switch_lang']}")
            self.console.print(f"    [bold bright_cyan]0[/]  {self.t['back_to_menu']}")
            self.console.print()

            choice = Prompt.ask(
                f"  [bold]{self.t['choose']}[/]",
                choices=["0", "1"]
            )
            if choice == "0":
                return
            elif choice == "1":
                self._do_switch_lang()

    # ── Main Menu ──

    def _main_menu(self):
        while True:
            self._clear()
            self._print_header(self.t["main_menu"])
            menu_items = [
                self.t["repo_list"],
                self.t["create_repo"],
                self.t["delete_repo"],
                self.t["change_vis"],
                self.t["switch_user"],
                self.t["settings"],
                self.t["exit"],
            ]
            for i, label in enumerate(menu_items, 1):
                self.console.print(f"    [bold bright_cyan]{i}[/]  {label}")
            self.console.print()
            choice = Prompt.ask(f"  [bold]{self.t['choose']}[/]", choices=[str(i) for i in range(1, 8)])
            choice = int(choice)
            if choice == 1:
                self._show_repo_list()
            elif choice == 2:
                self._show_create_repo()
            elif choice == 3:
                self._show_delete_repo()
            elif choice == 4:
                self._show_change_visibility()
            elif choice == 5:
                self._do_switch_user()
            elif choice == 6:
                self._show_settings()
            elif choice == 7:
                self._goodbye()
                break

    def _goodbye(self):
        self._clear()
        self.console.print()
        self.console.print(Panel(
            "[bold cyan]Thank you for using GitHub CLI Client![/]\n"
            "[dim]感谢使用 GitHub 终端客户端！[/]",
            border_style="bright_blue", padding=(1, 4)))
        self.console.print()

    # ── Repo List ──

    def _show_repo_list(self):
        sort_map = {"1": "updated", "2": "created", "3": "full_name", "4": "pushed"}
        sort_labels_key = ["sort_updated", "sort_created", "sort_name", "sort_updated"]

        page = 1
        current_sort = "updated"
        keyword = ""

        while True:
            self._clear()
            self._print_header(self.t["repo_list"])

            # sort bar
            self.console.print(f"  [bold yellow]{self.t['sort_by']}[/]", end="")
            for i in range(1, 5):
                marker = " [reverse]" if sort_map[str(i)] == current_sort else ""
                self.console.print(f"  {i}.{self.t[sort_labels_key[i-1]]}{marker}", end="")
            self.console.print()

            # search
            self.console.print()
            kw = Prompt.ask(f"  {self.t['search']}", default="")
            if kw.strip():
                keyword = kw.strip()

            self._spinner(self.t["loading"])
            repos, total_pages = self._fetch_repos(sort=current_sort, page=page)

            # filter
            if keyword:
                kw_lower = keyword.lower()
                filtered = [r for r in repos if kw_lower in (r.get("name") or "").lower()
                            or kw_lower in (r.get("description") or "").lower()
                            or kw_lower in (r.get("language") or "").lower()]
            else:
                filtered = repos

            if not filtered:
                self.console.print(f"  [yellow]{self.t['no_match'] if keyword else self.t['no_repos']}[/]")
                keyword = ""
                self._wait_back()
                continue

            # table
            table = Table(box=box.ROUNDED, show_lines=False, padding=(0, 1))
            table.add_column("#", style="bold bright_cyan", width=4, justify="right")
            table.add_column(self.t["repo_name"], style="bold white", min_width=22)
            table.add_column(self.t["language"], style="bright_magenta", width=14, justify="center")
            table.add_column(self.t["visibility"], width=10, justify="center")
            table.add_column(self.t["stars"], style="yellow", width=7, justify="right")
            table.add_column(self.t["forks"], width=7, justify="right")
            table.add_column(self.t["size"], width=9, justify="right")
            table.add_column(self.t["updated"], style="dim", width=16)

            for idx, r in enumerate(filtered, 1):
                lang = r.get("language") or "-"
                vis = self.t["private"] if r.get("private") else self.t["public"]
                vis_s = "red" if r.get("private") else "green"
                stars = r.get("stargazers_count", 0)
                forks = r.get("forks_count", 0)
                size = self._format_size(r.get("size", 0))
                updated = self._format_date(r.get("updated_at", ""))
                desc = (r.get("description") or "")[:40]
                name_col = f"{r['name']}" + (f"\n[dim]{desc}[/]" if desc else "")
                table.add_row(str(idx), name_col, lang,
                              f"[{vis_s}]{vis}[/{vis_s}]",
                              str(stars), str(forks), size, updated)

            self.console.print(table)
            self.console.print()
            nav = (f"  [dim]{self.t['page'].format(cur=page, total=total_pages)}[/]"
                   f"    [cyan]1-4[/] {self.t['sort_by']}"
                   f"    [cyan]p[/] {self.t['prev']}"
                   f"    [cyan]n[/] {self.t['next']}"
                   f"    [cyan]0[/] {self.t['menu_back']}")
            self.console.print(nav)

            action = Prompt.ask(f"  {self.t['choose_repo']}").strip().lower()
            if action in ("0", ""):
                return
            elif action.isdigit():
                idx = int(action) - 1
                if 0 <= idx < len(filtered):
                    self._show_repo_detail(filtered[idx])
                keyword = ""
            elif action == "p" and page > 1:
                page -= 1; keyword = ""
            elif action == "n" and page < total_pages:
                page += 1; keyword = ""
            elif action in sort_map:
                current_sort = sort_map[action]; page = 1; keyword = ""
            else:
                keyword = ""

    # ── Repo Detail ──

    def _show_repo_detail(self, repo):
        owner = repo.get("owner", {}).get("login", "") if isinstance(repo.get("owner"), dict) else repo.get("full_name", "").split("/")[0]
        name = repo.get("name", "")
        self._clear()
        self._print_header(f"{self.t['repo_detail']}: {owner}/{name}")

        # refresh detail
        self._spinner(self.t["loading"])
        detail = self._fetch_repo_detail(owner, name)
        if not detail:
            detail = repo

        vis = self.t["private"] if detail.get("private") else self.t["public"]
        vis_s = "bold red" if detail.get("private") else "bold green"

        info_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1), width=70)
        info_table.add_column("Key", style="bold cyan", width=18)
        info_table.add_column("Value", style="white")

        info_table.add_row(self.t["repo_name"], f"[bold]{detail.get('full_name', '')}[/]")
        info_table.add_row(self.t["description"], detail.get("description") or self.t["not_set"])
        info_table.add_row(self.t["visibility"], f"[{vis_s}]{vis}[/{vis_s}]")
        info_table.add_row(self.t["default_branch"], detail.get("default_branch", ""))
        info_table.add_row(self.t["language"], detail.get("language") or self.t["none"])
        info_table.add_row(self.t["stars"], str(detail.get("stargazers_count", 0)))
        info_table.add_row(self.t["forks"], str(detail.get("forks_count", 0)))
        info_table.add_row(self.t["issues"], str(detail.get("open_issues_count", 0)))
        info_table.add_row(self.t["size"], self._format_size(detail.get("size", 0)))
        info_table.add_row(self.t["created"], self._format_date(detail.get("created_at", "")))
        info_table.add_row(self.t["updated"], self._format_date(detail.get("updated_at", "")))
        info_table.add_row(self.t["has_issues"], self.t["yes"] if detail.get("has_issues") else self.t["no"])
        info_table.add_row(self.t["has_projects"], self.t["yes"] if detail.get("has_projects") else self.t["no"])
        info_table.add_row(self.t["has_wiki"], self.t["yes"] if detail.get("has_wiki") else self.t["no"])

        lic = detail.get("license")
        lic_name = lic.get("name", self.t["none"]) if lic else self.t["none"]
        info_table.add_row(self.t["license"], lic_name)

        topics = detail.get("topics", [])
        info_table.add_row(self.t["topics"], ", ".join(topics) if topics else self.t["none"])

        self.console.print(Panel(info_table, title=name, border_style="bright_blue", padding=(1, 2)))

        # clone URLs
        self.console.print()
        clone_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1), width=70)
        clone_table.add_column("Key", style="bold cyan", width=18)
        clone_table.add_column("Value", style="dim")
        clone_table.add_row(self.t["clone_url"], detail.get("clone_url", ""))
        clone_table.add_row(self.t["clone_ssh"], detail.get("ssh_url", ""))
        self.console.print(clone_table)

        self._wait_back()

    # ── Create Repo ──

    def _show_create_repo(self):
        self._clear()
        self._print_header(self.t["create_repo"])
        self.console.print()
        name = Prompt.ask(f"  [bold]{self.t['input_name']}[/]").strip()
        if not name:
            self.console.print("  [yellow]Cancelled.[/]")
            self._wait_back()
            return
        desc = Prompt.ask(f"  [bold]{self.t['input_desc']}[/]").strip()
        priv = Confirm.ask(f"  [bold]{self.t['input_private']}[/]")

        self._spinner(self.t["loading"])
        result = self._create_repo(name, desc, priv)
        if result:
            self.console.print()
            self.console.print(f"  [bold green]:heavy_check_mark: {self.t['create_success'].format(name=name)}[/]")
            self.console.print(f"  [dim]{result.get('html_url', '')}[/]")
        else:
            self.console.print()
            self.console.print(f"  [red]{self.t['create_fail'].format(error='Unknown')}[/]")
        self._wait_back()

    # ── Delete Repo ──

    def _show_delete_repo(self):
        self._clear()
        self._print_header(self.t["delete_repo"])

        self._spinner(self.t["loading"])
        repos, _ = self._fetch_repos(sort="full_name", page=1)
        if not repos:
            self.console.print(f"  [yellow]{self.t['no_repos']}[/]")
            self._wait_back()
            return

        table = Table(box=box.SIMPLE, padding=(0, 1))
        table.add_column("#", style="bold bright_cyan", width=4, justify="right")
        table.add_column(self.t["repo_name"], style="bold white", min_width=25)
        table.add_column(self.t["visibility"], width=10, justify="center")
        for idx, r in enumerate(repos, 1):
            vis = self.t["private"] if r.get("private") else self.t["public"]
            vis_s = "red" if r.get("private") else "green"
            table.add_row(str(idx), r.get("full_name", r["name"]), f"[{vis_s}]{vis}[/{vis_s}]")
        self.console.print(table)
        self.console.print()

        choice = Prompt.ask(f"  [bold]{self.t['choose_delete']}[/]").strip()
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(repos):
            self.console.print("  [yellow]Invalid selection.[/]")
            self._wait_back()
            return

        repo = repos[int(choice) - 1]
        owner = repo.get("owner", {}).get("login", "") if isinstance(repo.get("owner"), dict) else ""
        repo_name = repo.get("name", "")
        full_name = repo.get("full_name", f"{owner}/{repo_name}")

        self.console.print()
        self.console.print(f"  [bold red]:warning: {self.t['confirm_delete'].format(name=full_name)}[/]")
        confirm = Prompt.ask(f"  [bold red]{self.t['confirm_type'].format(text=full_name)}[/]").strip()
        if confirm != full_name:
            self.console.print(f"  [yellow]{self.t['delete_cancel']}[/]")
            self._wait_back()
            return

        self._spinner("Deleting...")
        ok = self._delete_repo(owner, repo_name)
        if ok:
            self.console.print()
            self.console.print(f"  [bold green]:heavy_check_mark: {self.t['delete_success'].format(name=full_name)}[/]")
        else:
            self.console.print()
            self.console.print(f"  [red]{self.t['delete_fail'].format(error='Failed')}[/]")
        self._wait_back()

    # ── Change Visibility ──

    def _show_change_visibility(self):
        self._clear()
        self._print_header(self.t["change_vis"])

        self._spinner(self.t["loading"])
        repos, _ = self._fetch_repos(sort="full_name", page=1)
        if not repos:
            self.console.print(f"  [yellow]{self.t['no_repos']}[/]")
            self._wait_back()
            return

        table = Table(box=box.SIMPLE, padding=(0, 1))
        table.add_column("#", style="bold bright_cyan", width=4, justify="right")
        table.add_column(self.t["repo_name"], style="bold white", min_width=25)
        table.add_column(self.t["visibility"], width=10, justify="center")
        for idx, r in enumerate(repos, 1):
            vis = self.t["private"] if r.get("private") else self.t["public"]
            vis_s = "red" if r.get("private") else "green"
            table.add_row(str(idx), r.get("full_name", r["name"]), f"[{vis_s}]{vis}[/{vis_s}]")
        self.console.print(table)
        self.console.print()

        choice = Prompt.ask(f"  [bold]{self.t['choose_vis']}[/]").strip()
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(repos):
            self.console.print("  [yellow]Invalid selection.[/]")
            self._wait_back()
            return

        repo = repos[int(choice) - 1]
        owner = repo.get("owner", {}).get("login", "") if isinstance(repo.get("owner"), dict) else ""
        repo_name = repo.get("name", "")
        full_name = repo.get("full_name", f"{owner}/{repo_name}")
        is_private = repo.get("private", False)

        if is_private:
            new_vis = self.t["vis_public"].replace("Make ", "").replace("设为", "")
            new_private = False
        else:
            new_vis = self.t["vis_private"].replace("Make ", "").replace("设为", "")
            new_private = True

        self.console.print()
        if Confirm.ask(f"  {self.t['vis_confirm'].format(name=full_name, vis=new_vis)}"):
            self._spinner("Updating...")
            result = self._update_repo(owner, repo_name, {"private": new_private})
            if result:
                self.console.print()
                self.console.print(f"  [bold green]:heavy_check_mark: {self.t['vis_success'].format(name=full_name, vis=new_vis)}[/]")
            else:
                self.console.print()
                self.console.print(f"  [red]{self.t['vis_fail'].format(error='Failed')}[/]")
        else:
            self.console.print(f"  [yellow]{self.t['vis_cancel']}[/]")
        self._wait_back()

    # ── Run ──

    def run(self):
        if not self.token:
            self._do_login()
            if not self.token:
                return
        else:
            # verify token still works
            self._fetch_user()

        self._main_menu()


if __name__ == "__main__":
    try:
        app = GitHubCLI()
        app.run()
    except KeyboardInterrupt:
        print("\n\n  Goodbye!\n")
        sys.exit(0)
