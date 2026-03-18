# 🐙 GitHub CLI Client

A visual, interactive GitHub client that runs entirely in your terminal.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)

## ✨ Features

- 🔐 **GitHub Token Authentication** — Login with a Personal Access Token, credentials saved locally
- 🌐 **Bilingual UI** — English / 中文 interface, selectable on first run and switchable anytime
- 📚 **Repository Browser** — Beautiful tabular view of all your repos (name, language, visibility, stars, forks, size, last updated)
- 🔍 **Search & Sort** — Filter repos by keyword, sort by name / recently updated / recently created / most stars
- 📄 **Pagination** — Browse through repos page by page
- 📊 **Repository Details** — Full info panel (description, default branch, license, topics, clone URLs, etc.)
- ➕ **Create Repository** — Create new public or private repos with a description
- 🗑️ **Delete Repository** — Safely delete repos with full-name confirmation to prevent accidents
- 🔒 **Change Visibility** — Toggle repos between public and private
- ⚙️ **Settings** — Dedicated settings sub-menu with language switching
- 🔄 **Switch User** — Change accounts by re-entering a different token

## 📸 Screenshots

### First Run — Language Selection
```
     G    I   T   H   U   B
     ─── C L I   C L I E N T ───

┌─────────────────────────────────┐
│         Welcome                 │
│  GitHub CLI Client             │
│  Terminal Visual GitHub Client  │
└─────────────────────────────────┘

? Choose language / 选择语言 [en/zh] (en):
```

### Main Menu
```
┌───────────────────────────────────┐
│  GitHub CLI  |  @your_username    │
└───────────────────────────────────┘

  Main Menu
  ────────────────────────────────────────

    1  My Repositories
    2  Create Repository
    3  Delete Repository
    4  Change Visibility
    5  Switch User
    6  Settings
    7  Exit
```

### Repository List
```
┌──────┬───────────────────────┬──────────┬──────────┬───────┬───────┬─────────┬──────────────────┐
│  #   │ Repository Name       │ Language │  Visibility │ Stars │ Forks │   Size  │     Updated     │
├──────┼───────────────────────┼──────────┼──────────┼───────┼───────┼─────────┼──────────────────┤
│  1   │ my-project            │ Python   │  Public   │    42 │     3 │ 1.2 MB  │ 2026-03-18 20:30 │
│  2   │ secret-tool           │ Rust     │  Private  │     7 │     1 │ 856 KB  │ 2026-03-17 14:22 │
└──────┴───────────────────────┴──────────┴──────────┴───────┴───────┴─────────┴──────────────────┘

  Page 1/3    1-4 Sort    p Prev    n Next    0 Back
```

## 🚀 Quick Start

### 1. Clone this repository

```bash
git clone https://github.com/branchweb3/github-tools.git
cd github-tools
```

### 2. Install dependencies

```bash
pip install rich requests
```

### 3. Run

```bash
python github_cli.py
```

On first launch you'll be prompted to choose your language (English or 中文), then asked to enter your GitHub Personal Access Token.

## 🔑 Getting a GitHub Token

1. Go to [GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)](https://github.com/settings/tokens)
2. Click **Generate new token**
3. Select scopes: at minimum enable `repo` (full control of private repositories)
4. Copy the generated token and paste it into the CLI when prompted

> ⚠️ Your token is stored locally in `~/.github_cli/config.json`. It is **never** sent anywhere except the official GitHub API.

## 📁 Project Structure

```
github-tools/
├── github_cli.py   # Main application (GitHub CLI client)
├── i18n.py         # Internationalization strings (English / 中文)
└── README.md       # This file
```

## ⚙️ Configuration

Config file location: `~/.github_cli/config.json`

```json
{
  "lang": "en",
  "token": "ghp_xxxxxxxxxxxx",
  "username": "your_username"
}
```

## 🛠️ Tech Stack

- **Python 3.8+** — Core runtime
- **[Rich](https://github.com/Textualize/rich)** — Terminal formatting, tables, panels, progress spinners
- **[Requests](https://github.com/psf/requests)** — HTTP calls to GitHub REST API v3
- **[GitHub REST API](https://docs.github.com/en/rest)** — Backend data source

## 📋 License

MIT License — feel free to use, modify, and distribute.

---

<p align="center">Made with ❤️ using Python & Rich</p>
