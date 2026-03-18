# 🐙 GitHub CLI Client

A production-ready, visual, interactive GitHub client that runs entirely in your terminal.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)
![Tests](https://img.shields.io/badge/Tests-72%20passed-brightgreen)

## ✨ Features

- 🔐 **GitHub Token Authentication** — Login with Personal Access Token, auto-retry on failure
- 🌐 **Bilingual UI** — English / 中文, selectable on first run, switchable anytime via Settings
- 📚 **Repository Browser** — Beautiful tabular view (name, language, visibility, stars, forks, size, updated)
- 🔍 **Search & Sort** — Filter repos by keyword, sort by name / updated / created / stars (arrow keys ← →)
- 📄 **Pagination** — Browse repos page by page (arrow keys ↑ ↓)
- 📊 **Repository Details** — Full info panel (18 fields: description, branch, license, topics, clone URLs, homepage, watchers, etc.)
- ➕ **Create Repository** — With name validation, optional description, public/private toggle
- 🗑️ **Delete Repository** — Full-name confirmation to prevent accidental deletion
- 🔒 **Change Visibility** — Toggle repos between public and private
- ⚙️ **Settings** — Dedicated settings sub-menu with language switching
- 🔄 **Switch User** — Change accounts by re-entering a different token
- 🛡️ **Error Handling** — Graceful handling of network errors, API rate limits, invalid tokens, null fields
- 🪟 **Windows Compatible** — Auto-fixes terminal encoding for proper Chinese/Unicode display

## 🚀 Quick Start

```bash
git clone https://github.com/BranchCrypto/github-tools.git
cd github-tools
pip install rich requests prompt_toolkit
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
├── github_cli.py   # Main application
├── i18n.py         # Internationalization (English / 中文)
├── .gitignore      # Ignore __pycache__ etc.
└── README.md       # This file
```

## 📋 Keyboard Shortcuts (Repo List)

| Key | Action |
|-----|--------|
| `←` `→` | Cycle through sort options (Updated / Created / Name / Stars) |
| `↑` | Previous page |
| `↓` | Next page |
| `1-15` | View repository detail |
| `Esc` | Back to main menu |
| `0` / `Enter` | Back to main menu |

## ⚙️ Configuration

Config file: `~/.github_cli/config.json`

```json
{
  "lang": "en",
  "token": "ghp_xxxxxxxxxxxx",
  "username": "your_username"
}
```

## 🛠️ Tech Stack

- **Python 3.8+**
- **[Rich](https://github.com/Textualize/rich)** — Terminal UI (tables, panels, progress, colors)
- **[prompt_toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit)** — Arrow key navigation & advanced input handling
- **[Requests](https://github.com/psf/requests)** — HTTP client for GitHub REST API v3

## 📋 License

MIT License — feel free to use, modify, and distribute.

---

<p align="center">Made with ❤️ using Python & Rich</p>
