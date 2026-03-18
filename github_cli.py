"""
GitHub CLI Client - Interactive Terminal UI
============================================
A visual GitHub client that runs in your terminal.

Features:
  - GitHub Token authentication with retry
  - Browse repositories (search, sort, pagination)
  - View detailed repository info
  - Create / Delete repositories
  - Change repository visibility (public/private)
  - Bilingual UI (English / 中文)
  - Config persisted in ~/.github_cli/config.json

Usage:
    pip install rich requests
    python github_cli.py
"""
import os
import sys

# ── Fix Windows encoding BEFORE any other imports ──
if sys.platform == "win32":
    os.system("chcp 65001 > nul 2>&1")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import json
import time
import re
import requests
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

# ──────────────────────── Config ────────────────────────

CONFIG_DIR = Path.home() / ".github_cli"
CONFIG_FILE = CONFIG_DIR / "config.json"
GITHUB_API = "https://api.github.com"

# ──────────────────────── Helpers ────────────────────────

REPO_NAME_RE = re.compile(r"^[a-zA-Z0-9._-]+$")


class GitHubCLI:
    """Main application class."""

    PER_PAGE = 15

    def __init__(self):
        self.console = Console(force_terminal=True, legacy_windows=False)
        self.lang = "en"
        self.token = ""
        self.username = ""
        self.headers = None
        self.config = {}
        self._load_config()

    @property
    def t(self):
        return LANG[self.lang]

    # ═══════════════════ Config ═══════════════════

    def _load_config(self):
        if CONFIG_FILE.exists():
            try:
                self.config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                self.lang = self.config.get("lang", "en")
                self.token = self.config.get("token") or ""
                self.username = self.config.get("username") or ""
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
        self.config = {
            "lang": self.lang,
            "token": self.token or None,
            "username": self.username or None,
        }
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(
            json.dumps(self.config, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _first_run_language_select(self):
        self.console.clear()
        self.console.print()
        banner = Text()
        banner.append("  GITHUB CLI CLIENT", style="bold bright_cyan")
        self.console.print(Panel(banner, border_style="bright_blue", padding=(1, 4)))
        self.console.print()
        self.lang = Prompt.ask(
            "  [bold cyan]?[/] Choose language / \u9009\u62e9\u8bed\u8a00",
            choices=["en", "zh"], default="en",
        )
        self._save_config()

    # ═══════════════════ API ═══════════════════

    def _api(self, method, endpoint, data=None, params=None):
        if not self.headers:
            return None
        url = f"{GITHUB_API}{endpoint}"
        try:
            resp = requests.request(
                method, url, headers=self.headers,
                json=data, params=params, timeout=30,
            )
            if resp.status_code == 401:
                self.console.print(f"  [bold red]{self.t['token_invalid']}[/]")
                self.token = ""
                self.username = ""
                self.headers = None
                self._save_config()
                return None
            if resp.status_code == 403 and "rate limit" in resp.text.lower():
                self.console.print(f"  [bold yellow]{self.t['rate_limit']}[/]")
                return None
            resp.raise_for_status()
            return resp
        except requests.exceptions.HTTPError as e:
            try:
                err = e.response.json().get("message", str(e))
            except Exception:
                err = str(e)
            self.console.print(f"  [red]{self.t['api_error'].format(error=err)}[/]")
            return None
        except requests.exceptions.ConnectionError as e:
            self.console.print(f"  [red]{self.t['network_error'].format(error=str(e))}[/]")
            return None
        except Exception as e:
            self.console.print(f"  [red]{self.t['error'].format(error=str(e))}[/]")
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
                last_part = [p for p in link_header.split(",") if 'rel="last"' in p][0]
                total_pages = int(last_part.split("page=")[-1].split(">")[0])
            except (IndexError, ValueError):
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

    # ═══════════════════ UI Helpers ═══════════════════

    def _clear(self):
        self.console.clear()

    def _print_header(self, title=None):
        header = Text()
        header.append(" GitHub CLI ", style="bold bright_cyan on blue")
        if self.username:
            header.append(f"  |  @{self.username}", style="bold green")
        self.console.print(Panel(header, border_style="bright_blue", padding=(0, 2)))
        if title:
            self.console.print()
            self.console.print(f"  [bold white]{title}[/]")
            self.console.print(f"  {'─' * 56}", style="dim")
            self.console.print()

    def _wait_back(self):
        Prompt.ask(f"\n  [dim]{self.t['back']}[/]")
        return True

    def _format_size(self, kb):
        if not kb:
            return "0 KB"
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
            return dt_str[:16] if dt_str else self.t["none"]

    def _get_owner(self, repo):
        owner = repo.get("owner")
        if isinstance(owner, dict):
            return owner.get("login", "")
        full = repo.get("full_name", "")
        return full.split("/")[0] if "/" in full else ""

    def _spinner(self, msg):
        with Progress(
            SpinnerColumn(), TextColumn("[bold blue]{task.description}"),
            console=self.console, transient=True,
        ) as progress:
            progress.add_task(msg, total=None)
            time.sleep(0.4)

    # ═══════════════════ Login ═══════════════════

    def _do_login(self):
        while True:
            self._clear()
            self._print_header(self.t["login"])
            self.console.print(f"  [cyan]{self.t['token_hint']}[/]")
            self.console.print()
            token = Prompt.ask(f"  [bold]{self.t['enter_token']}[/]", password=True)
            token = token.strip()
            if not token:
                if Confirm.ask(f"  [yellow]No token entered. Retry? (y/n)[/]", default=True):
                    continue
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
                        f"  [bold green]:heavy_check_mark: "
                        f"{self.t['login_success'].format(name=self.username)}[/]"
                    )
                    time.sleep(1.5)
                    return True
                else:
                    self.console.print(f"  [bold red]:x: {self.t['login_fail']}[/]")
                    if Confirm.ask(f"  [bold]Retry? (y/n)[/]", default=True):
                        continue
                    return False
            except requests.exceptions.ConnectionError:
                self.console.print(
                    f"  [red]{self.t['network_error'].format(error='Cannot connect to GitHub')}[/]"
                )
                if Confirm.ask(f"  [bold]Retry? (y/n)[/]", default=True):
                    continue
                return False
            except Exception as e:
                self.console.print(f"  [red]{self.t['error'].format(error=str(e))}[/]")
                if Confirm.ask(f"  [bold]Retry? (y/n)[/]", default=True):
                    continue
                return False

    def _do_switch_user(self):
        self.token = ""
        self.username = ""
        self.headers = None
        self._save_config()
        self._do_login()

    def _do_switch_lang(self):
        self.lang = "zh" if self.lang == "en" else "en"
        self._save_config()
        msg = self.t["lang_switched_en"] if self.lang == "en" else self.t["lang_switched_zh"]
        self.console.print(f"\n  [green]:heavy_check_mark: {msg}[/]")
        time.sleep(1)

    # ═══════════════════ Settings ═══════════════════

    def _show_settings(self):
        while True:
            self._clear()
            self._print_header(self.t["settings_menu"])
            current_lang = "English" if self.lang == "en" else "\u4e2d\u6587"
            self.console.print(f"  [dim]{self.t['lang_current'].format(lang=current_lang)}[/]")
            self.console.print()
            self.console.print(f"    [bold bright_cyan]1[/]  {self.t['switch_lang']}")
            self.console.print(f"    [bold bright_cyan]0[/]  {self.t['back_to_menu']}")
            self.console.print()
            choice = Prompt.ask(f"  [bold]{self.t['choose']}[/]", choices=["0", "1"])
            if choice == "0":
                return
            elif choice == "1":
                self._do_switch_lang()

    # ═══════════════════ Main Menu ═══════════════════

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
            choice = Prompt.ask(
                f"  [bold]{self.t['choose']}[/]",
                choices=[str(i) for i in range(1, 8)],
            )
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
        bye = "Thank you for using GitHub CLI Client!"
        if self.lang == "zh":
            bye += "\n\u611f\u8c22\u4f7f\u7528 GitHub \u7ec8\u7aef\u5ba2\u6237\u7aef\uff01"
        self.console.print(
            Panel(f"[bold cyan]{bye}[/]", border_style="bright_blue", padding=(1, 4))
        )
        self.console.print()

    # ═══════════════════ Repo List ═══════════════════

    def _show_repo_list(self):
        sort_options = [
            ("a", "updated", "sort_updated"),
            ("b", "created", "sort_created"),
            ("c", "full_name", "sort_name"),
            ("d", "stargazers_count", "sort_stars"),
        ]
        sort_key_map = {k: v for k, v, _ in sort_options}

        page = 1
        current_sort = "updated"
        keyword = ""

        while True:
            self._clear()
            self._print_header(self.t["repo_list"])

            # Sort bar — letter keys to avoid conflict with repo numbers
            sort_parts = []
            for key, val, label_key in sort_options:
                marker = " [reverse bold]" if val == current_sort else ""
                sort_parts.append(f"[cyan]{key}[/].{self.t[label_key]}{marker}")
            self.console.print(
                f"  [bold yellow]{self.t['sort_by']}[/]  " + "  ".join(sort_parts)
            )

            # Search
            self.console.print()
            kw = Prompt.ask(f"  {self.t['search']}", default="")
            if kw.strip():
                keyword = kw.strip()

            self._spinner(self.t["loading"])
            repos, total_pages = self._fetch_repos(sort=current_sort, page=page)

            # Filter by keyword
            if keyword:
                kw_lower = keyword.lower()
                filtered = [
                    r for r in repos
                    if kw_lower in (r.get("name") or "").lower()
                    or kw_lower in (r.get("description") or "").lower()
                    or kw_lower in (r.get("language") or "").lower()
                ]
            else:
                filtered = repos

            if not filtered:
                msg = self.t["no_match"] if keyword else self.t["no_repos"]
                self.console.print(f"\n  [yellow]{msg}[/]")
                keyword = ""
                self._wait_back()
                continue

            # Build table
            table = Table(box=box.ROUNDED, show_lines=False, padding=(0, 1))
            table.add_column("#", style="bold bright_cyan", width=4, justify="right")
            table.add_column(self.t["repo_name"], min_width=22, no_wrap=False)
            table.add_column(self.t["language"], style="bright_magenta", width=14, justify="center")
            table.add_column(self.t["visibility"], width=10, justify="center")
            table.add_column(self.t["stars"], style="yellow", width=7, justify="right")
            table.add_column(self.t["forks"], width=7, justify="right")
            table.add_column(self.t["size"], width=9, justify="right")
            table.add_column(self.t["updated"], style="dim", width=16)

            for idx, r in enumerate(filtered, 1):
                lang = r.get("language") or "-"
                is_priv = r.get("private", False)
                vis = self.t["private"] if is_priv else self.t["public"]
                vis_s = "red" if is_priv else "green"
                stars = r.get("stargazers_count", 0)
                forks = r.get("forks_count", 0)
                size = self._format_size(r.get("size", 0))
                updated = self._format_date(r.get("updated_at", ""))
                desc = (r.get("description") or "")[:50]
                name_text = r["name"]
                if desc:
                    name_text += f"\n[dim]{desc}[/]"
                table.add_row(
                    str(idx), f"[bold]{name_text}[/]", lang,
                    f"[{vis_s}]{vis}[/{vis_s}]",
                    str(stars), str(forks), size, updated,
                )

            self.console.print(table)
            self.console.print()
            nav = (
                f"  [dim]{self.t['page'].format(cur=page, total=total_pages)}[/]"
                f"    [cyan]a-d[/] {self.t['sort_by']}"
                f"    [cyan]p[/] {self.t['prev']}"
                f"    [cyan]n[/] {self.t['next']}"
                f"    [cyan]0[/] {self.t['menu_back']}"
            )
            self.console.print(nav)

            action = Prompt.ask(f"  {self.t['choose_repo']}").strip().lower()
            if action in ("0", ""):
                return
            elif action.isdigit():
                idx = int(action) - 1
                if 0 <= idx < len(filtered):
                    self._show_repo_detail(filtered[idx])
                keyword = ""
            elif action in sort_key_map:
                current_sort = sort_key_map[action]
                page = 1
                keyword = ""
            elif action == "p" and page > 1:
                page -= 1
                keyword = ""
            elif action == "n" and page < total_pages:
                page += 1
                keyword = ""
            else:
                keyword = ""

    # ═══════════════════ Repo Detail ═══════════════════

    def _show_repo_detail(self, repo):
        owner = self._get_owner(repo)
        name = repo.get("name", "")
        full = repo.get("full_name", f"{owner}/{name}")

        self._clear()
        self._print_header(f"{self.t['repo_detail']}: {full}")

        self._spinner(self.t["loading"])
        detail = self._fetch_repo_detail(owner, name)
        if not detail:
            detail = repo

        is_priv = detail.get("private", False)
        vis = self.t["private"] if is_priv else self.t["public"]
        vis_s = "bold red" if is_priv else "bold green"

        info = Table(box=box.SIMPLE, show_header=False, padding=(0, 1), expand=False)
        info.add_column("Key", style="bold cyan", width=18, no_wrap=True)
        info.add_column("Value", style="white", max_width=55)

        rows = [
            (self.t["repo_name"], f"[bold]{detail.get('full_name', '')}[/]"),
            (self.t["description"], detail.get("description") or self.t["not_set"]),
            (self.t["visibility"], f"[{vis_s}]{vis}[/{vis_s}]"),
            (self.t["default_branch"], detail.get("default_branch") or "-"),
            (self.t["language"], detail.get("language") or self.t["none"]),
            (self.t["stars"], str(detail.get("stargazers_count", 0))),
            (self.t["forks"], str(detail.get("forks_count", 0))),
            (self.t["watchers"], str(detail.get("watchers_count", 0))),
            (self.t["issues"], str(detail.get("open_issues_count", 0))),
            (self.t["size"], self._format_size(detail.get("size", 0))),
            (self.t["disk_usage"], self._format_size(detail.get("disk_usage") or 0)),
            (self.t["created"], self._format_date(detail.get("created_at", ""))),
            (self.t["updated"], self._format_date(detail.get("updated_at", ""))),
            (self.t["has_issues"], self.t["yes"] if detail.get("has_issues") else self.t["no"]),
            (self.t["has_projects"], self.t["yes"] if detail.get("has_projects") else self.t["no"]),
            (self.t["has_wiki"], self.t["yes"] if detail.get("has_wiki") else self.t["no"]),
        ]

        # License
        lic = detail.get("license")
        lic_name = lic.get("spdx_id", lic.get("name", "")) if lic else ""
        if not lic_name:
            lic_name = self.t["none"]
        rows.append((self.t["license"], lic_name))

        # Topics
        topics = detail.get("topics") or []
        rows.append((self.t["topics"], ", ".join(topics) if topics else self.t["none"]))

        # Homepage
        hp = detail.get("homepage") or ""
        rows.append((self.t["homepage"], hp if hp else self.t["not_set"]))

        for key, val in rows:
            info.add_row(key, val)

        self.console.print(Panel(info, title=full, border_style="bright_blue", padding=(1, 2)))

        # Clone URLs
        self.console.print()
        clone = Table(box=box.SIMPLE, show_header=False, padding=(0, 1), expand=False)
        clone.add_column("Key", style="bold cyan", width=18, no_wrap=True)
        clone.add_column("Value", style="dim cyan", max_width=55)
        clone.add_row(self.t["clone_url"], detail.get("clone_url", ""))
        clone.add_row(self.t["clone_ssh"], detail.get("ssh_url", ""))
        clone.add_row(self.t["web_url"], detail.get("html_url", ""))
        self.console.print(clone)

        self._wait_back()

    # ═══════════════════ Create Repo ═══════════════════

    def _show_create_repo(self):
        self._clear()
        self._print_header(self.t["create_repo"])
        self.console.print()

        name = Prompt.ask(f"  [bold]{self.t['input_name']}[/]").strip()
        if not name:
            self.console.print(f"  [yellow]{self.t['cancelled']}[/]")
            self._wait_back()
            return

        # Validate repo name
        if not REPO_NAME_RE.match(name):
            self.console.print(f"  [red]{self.t['name_invalid']}[/]")
            self._wait_back()
            return

        desc = Prompt.ask(f"  [bold]{self.t['input_desc']}[/]").strip()
        priv = Confirm.ask(f"  [bold]{self.t['input_private']}[/]")

        self._spinner(self.t["loading"])
        result = self._create_repo(name, desc or None, priv)
        if result:
            self.console.print()
            self.console.print(
                f"  [bold green]:heavy_check_mark: "
                f"{self.t['create_success'].format(name=name)}[/]"
            )
            self.console.print(f"  [dim]{result.get('html_url', '')}[/]")
        else:
            self.console.print()
            self.console.print(f"  [red]{self.t['create_fail'].format(error=self.t['none'])}[/]")
        self._wait_back()

    # ═══════════════════ Delete Repo ═══════════════════

    def _show_delete_repo(self):
        self._clear()
        self._print_header(self.t["delete_repo"])

        self._spinner(self.t["loading"])
        repos, _ = self._fetch_repos(sort="full_name", page=1)
        if not repos:
            self.console.print(f"  [yellow]{self.t['no_repos']}[/]")
            self._wait_back()
            return

        self._print_repo_table(repos)
        self.console.print()

        choice = Prompt.ask(f"  [bold]{self.t['choose_delete']}[/]").strip()
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(repos):
            self.console.print(f"  [yellow]{self.t['cancelled']}[/]")
            self._wait_back()
            return

        repo = repos[int(choice) - 1]
        owner = self._get_owner(repo)
        repo_name = repo.get("name", "")
        full_name = repo.get("full_name", f"{owner}/{repo_name}")

        self.console.print()
        self.console.print(
            f"  [bold red]:warning: {self.t['confirm_delete'].format(name=full_name)}[/]"
        )
        confirm = Prompt.ask(
            f"  [bold red]{self.t['confirm_type'].format(text=full_name)}[/]"
        ).strip()
        if confirm != full_name:
            self.console.print(f"  [yellow]{self.t['delete_cancel']}[/]")
            self._wait_back()
            return

        self._spinner(self.t["loading"])
        ok = self._delete_repo(owner, repo_name)
        if ok:
            self.console.print()
            self.console.print(
                f"  [bold green]:heavy_check_mark: "
                f"{self.t['delete_success'].format(name=full_name)}[/]"
            )
        else:
            self.console.print()
            self.console.print(
                f"  [red]{self.t['delete_fail'].format(error=self.t['none'])}[/]"
            )
        self._wait_back()

    # ═══════════════════ Change Visibility ═══════════════════

    def _show_change_visibility(self):
        self._clear()
        self._print_header(self.t["change_vis"])

        self._spinner(self.t["loading"])
        repos, _ = self._fetch_repos(sort="full_name", page=1)
        if not repos:
            self.console.print(f"  [yellow]{self.t['no_repos']}[/]")
            self._wait_back()
            return

        self._print_repo_table(repos)
        self.console.print()

        choice = Prompt.ask(f"  [bold]{self.t['choose_vis']}[/]").strip()
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(repos):
            self.console.print(f"  [yellow]{self.t['cancelled']}[/]")
            self._wait_back()
            return

        repo = repos[int(choice) - 1]
        owner = self._get_owner(repo)
        repo_name = repo.get("name", "")
        full_name = repo.get("full_name", f"{owner}/{repo_name}")
        is_private = repo.get("private", False)

        new_vis = self.t["vis_public"] if is_private else self.t["vis_private"]
        new_private = not is_private

        self.console.print()
        if Confirm.ask(f"  {self.t['vis_confirm'].format(name=full_name, vis=new_vis)}"):
            self._spinner(self.t["loading"])
            result = self._update_repo(owner, repo_name, {"private": new_private})
            if result:
                self.console.print()
                self.console.print(
                    f"  [bold green]:heavy_check_mark: "
                    f"{self.t['vis_success'].format(name=full_name, vis=new_vis)}[/]"
                )
            else:
                self.console.print()
                self.console.print(
                    f"  [red]{self.t['vis_fail'].format(error=self.t['none'])}[/]"
                )
        else:
            self.console.print(f"  [yellow]{self.t['vis_cancel']}[/]")
        self._wait_back()

    # ═══════════════════ Shared Table ═══════════════════

    def _print_repo_table(self, repos):
        table = Table(box=box.SIMPLE, padding=(0, 1))
        table.add_column("#", style="bold bright_cyan", width=4, justify="right")
        table.add_column(self.t["repo_name"], style="bold white", min_width=25)
        table.add_column(self.t["visibility"], width=10, justify="center")
        for idx, r in enumerate(repos, 1):
            is_priv = r.get("private", False)
            vis = self.t["private"] if is_priv else self.t["public"]
            vis_s = "red" if is_priv else "green"
            table.add_row(
                str(idx), r.get("full_name", r["name"]),
                f"[{vis_s}]{vis}[/{vis_s}]",
            )
        self.console.print(table)

    # ═══════════════════ Run ═══════════════════

    def run(self):
        if not self.token:
            if not self._do_login():
                return
        else:
            self._fetch_user()
            if not self.token:
                if not self._do_login():
                    return
        self._main_menu()


if __name__ == "__main__":
    try:
        app = GitHubCLI()
        app.run()
    except KeyboardInterrupt:
        print("\n\n  Goodbye!\n")
        sys.exit(0)
