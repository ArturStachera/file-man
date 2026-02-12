# 🗂️ Terminal File Manager

Terminal-based file manager with an elegant ANSI/ASCII UI, built with Python and curses.

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Android-lightgrey)

![Terminal File Manager Screenshot](https://github.com/ArturStachera/file-man/releases/download/v1.0.1/Screenshot_20-Jan-2026.png)

## 🆕 Release Notes

### v1.0.3

- **Dual-Panel File Tree:** Introduced a toggleable second file tree panel (key `t`), allowing for efficient side-by-side browsing, copying, and moving of files between directories, similar to Midnight Commander. The second panel remembers its last visited location.
- **Enhanced Help Screen:** The help screen (`m` key) now dynamically scales and centers its display based on terminal size and content, ensuring readability for all shortcuts without text wrapping.
- **Simplified Status Bar:** The main status bar now provides a concise overview of essential file operation shortcuts, with a dedicated "[M]ore" button to access the comprehensive help screen.

### v1.0.2

- **Disk Management Panel:** A new dedicated panel to view, mount, unmount, and open storage drives (USB, HDD/SSD) directly from the UI. Features an integrated in-app sudo password prompt for seamless privileged operations.
- **Enhanced UI Navigation:** The "Shortcuts" panel has been refactored into a fully navigable list, consistent with other panels. Navigate seamlessly between panels using the `Tab` key, and enjoy overflow scrolling for all lists.
- **Improved Stability:** Fixed a critical bug preventing application crashes when unmounting the current working directory.
- **Better Diagnostics:** Mount and unmount operations now provide more detailed error messages to assist with troubleshooting.
- **Overflow Navigation:** Implemented wrap-around navigation for all lists, allowing selection to loop from top to bottom and vice-versa.

### v1.0.1

- Mouse/touch support (works in desktop terminals and Termux)
  - Single click/tap selects an item
  - Double click/double tap enters a directory
  - Mouse wheel scrolling in the directory tree
  - Clickable shortcuts panel, bottom action bar, and update box
- Termux improvements
  - More robust `run.sh` virtual environment detection (`python`, `python3`, `python3.X`)
  - Handles non-portable `.venv` directories copied from another system with an actionable message
  - Disk info fallback via `shutil.disk_usage()` when `psutil` is unavailable or blocked
- Screenshot management
  - README screenshot is linked as a GitHub Release asset instead of being stored in the repository
- Bug fixes
  - Prevented double-triggering actions on mouse press/release

## ✨ Features

- **5/6-Panel Interface (dynamic)**
  - Quick access shortcuts panel (fully navigable)
  - Primary directory tree with visual navigation
  - Secondary directory tree (toggleable with `t`)
  - Detailed file information
  - Live file preview (text & images in ASCII art)
  - Real-time disk usage statistics
  - **NEW: Dedicated Drives Panel for mounting/unmounting**

- **File Operations**
  - Create, delete, rename files and directories
  - Copy, cut, and paste with clipboard
  - Edit files directly in Neovim/Vim/Nano
  - Execute shell commands on files
  - **NEW: Mount and unmount drives with in-app sudo prompt**

- **Advanced Features**
  - Real-time directory auto-refresh
  - Search and filter files
  - Show/hide hidden files
  - Keyboard-driven navigation (Tab for panel switching, overflow scrolling)
  - Mouse/touch-friendly navigation
  - Auto-update checker built-in (now 'U' key)

## 📸 Demo Video

Short demo showing the application in action:

[YouTube demo](https://www.youtube.com/watch?v=_O91ZIo4ti0)

## 🚀 Installation

### Prerequisites

**For Debian/Ubuntu/Mint:**
```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

**For Arch Linux:**
```bash
sudo pacman -S python
```

**For Android (Termux):**
```bash
# Install Termux from F-Droid (recommended) or Google Play
# Then inside Termux:
pkg update && pkg upgrade
pkg install python git libjpeg-turbo libpng zlib
```

Python 3.8 or higher is required. The application works on Linux/Unix terminals that support curses.

### Quick Start with Launcher Script

The easiest way to run the file manager is using the provided launcher script:

**Linux/macOS/Termux:**
```bash
# Clone the repository
git clone https://github.com/ArturStachera/file-man.git
cd file-man

# Run the file manager (handles all setup automatically)
./run.sh
```

The `run.sh` script automatically:
- Creates a virtual environment if it doesn't exist
- Installs/updates all dependencies
- Launches the file manager

### Manual Installation (Optional)

If you prefer to set up manually:

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Linux/Mac/Termux

# Install dependencies
pip install -r requirements.txt

# Run the file manager
python file_manager.py
```

### Optional Dependencies

For full functionality, the following packages are recommended:

```bash
# Image preview support (ASCII art)
pip install pillow

# Disk usage information
pip install psutil
```

These are included in `requirements.txt` and will be installed automatically by `run.sh`.

**Note for Termux users:** Image preview works with ASCII art conversion. Disk usage info shows your Termux home directory storage.

## ⌨️ Keyboard Shortcuts

### Navigation
| Key | Action |
|-----|--------|
| `↑` / `↓` | Move selection up/down |
| `←` | Go to parent directory |
| `→` / `Enter` | Enter selected directory / Activate selected shortcut / Mount/Open selected drive |
| `Tab` | Switch active panel (Tree, Drives, Shortcuts) |

### File Operations
| Key | Action |
|-----|--------|
| `n` | Create new file/directory (enter `f name` or `d name`) |
| `d` | Delete selected file/directory |
| `r` | Rename selected item |
| `e` | Edit file in Neovim/Vim/Nano |
| `c` | Copy to clipboard |
| `x` | Cut to clipboard |
| `v` | Paste from clipboard |

### Other
| Key | Action |
|-----/--------|
| `:` | Execute shell command on file |
| `/` | Search files |
| `h` | Toggle hidden files visibility |
| `u` | Unmount selected drive |
| `U` | Check for updates |
| `ESC` | Clear search/cancel |
| `q` | Quit application |

## 💡 Usage Examples

### Creating Files and Directories

**Create a file:**
1. Press `n`
2. Type: `f myfile.txt`
3. Press `Enter`

**Create a directory:**
1. Press `n`
2. Type: `d MyFolder`
3. Press `Enter`

### Copy and Paste

1. Navigate to file
2. Press `c` to copy (or `x` to cut)
3. Navigate to destination directory
4. Press `v` to paste

### Execute Commands

Run any shell command on the selected file:

1. Select a file
2. Press `:`
3. Enter command, e.g., `cat` or `file {file}` or `chmod +x`
4. Press `Enter`

The `{file}` placeholder will be replaced with the file path.

### Search Files

1. Press `/`
2. Type search term
3. Press `Enter`
4. Press `ESC` to clear search

### Check for Updates

1. Press `u` (or click the update box in bottom right)
2. The application will check GitHub for new versions
3. Follow on-screen instructions if update is available

## 🛠️ Configuration

### Customize Shortcuts

Edit the `shortcuts` list in `FileManagerUI.__init__()` in `file_manager.py`:

```python
self.shortcuts = [
    (Path.home() / "Downloads", "Downloads"),
    (Path.home() / "Projects", "Projects"),
    # Add more shortcuts here
]
```

### Change Default Editor

The application automatically detects available editors in this order:
1. Neovim (`nvim`)
2. Vim (`vim`)
3. Nano (`nano`)

To change the priority, edit the `editors` list in the `edit_file()` method.

## 🐛 Troubleshooting

### Problem: No image preview
**Solution:** Install Pillow
```bash
pip install pillow
```

### Problem: No disk information
**Solution:** Install psutil
```bash
pip install psutil
```

**Note for Termux:** If you see "Disk info unavailable" even with psutil installed, this is normal due to Android restrictions. The app will still show your home directory storage usage.

### Problem: Unicode characters not displaying correctly
**Solution:** Ensure your terminal supports UTF-8 encoding
```bash
export LANG=en_US.UTF-8
```

### Problem: Import error or module not found
**Solution:** Make sure you're using the virtual environment
```bash
source .venv/bin/activate  # Then run the application
```

### Problem: Permission denied when running run.sh
**Solution:** Make the script executable
```bash
chmod +x run.sh
```

### Termux-specific issues

**Problem:** Pillow build fails on Termux
**Solution:** Make sure you installed the required packages:
```bash
pkg install libjpeg-turbo libpng zlib
```

**Problem:** Permission errors on Android
**Solution:** Termux has limited access to some system directories. Navigate to accessible directories like:
- `/data/data/com.termux/files/home` (your Termux home)
- `/storage/emulated/0` (internal storage, if permissions granted)

## 📝 Roadmap & Planned Features

- [ ] Multiple file selection
- [ ] Bookmark system for favorite directories
- [ ] File permissions viewer/editor
- [ ] Trash bin functionality instead of permanent delete
- [ ] Color themes and customization
- [ ] Plugin system for extensibility
- [ ] Archive support (zip, tar, etc.)
- [ ] Network/remote file system support
- [ ] Split view for two directories
- [ ] File comparison tool

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with Python's `curses` library for terminal UI
- Image processing with [Pillow](https://python-pillow.org/)
- System information with [psutil](https://github.com/giampaolo/psutil)
- Inspired by classic file managers like Midnight Commander and ranger
- Tested on Linux, macOS, and Android (Termux)

---

Made with ❤️ and Python | Star ⭐ if you find this useful!
