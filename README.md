# 🗂️ Terminal File Manager

Terminal-based file manager with an elegant ANSI/ASCII UI, built with Python and curses.

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## ✨ Features

- **5-Panel Interface**
  - Quick access shortcuts panel
  - Directory tree with visual navigation
  - Detailed file information
  - Live file preview (text & images in ASCII art)
  - Real-time disk usage statistics

- **File Operations**
  - Create, delete, rename files and directories
  - Copy, cut, and paste with clipboard
  - Edit files directly in Neovim/Vim/Nano
  - Execute shell commands on files

- **Advanced Features**
  - Real-time directory auto-refresh
  - Search and filter files
  - Show/hide hidden files
  - Keyboard-driven navigation
  - Auto-update checker built-in

## 📸 Demo Video

Short demo showing the application in action:

[YouTube demo](https://youtu.be/VIDEO_ID)


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

Python 3.8 or higher is required. The application works on Linux/Unix terminals that support curses.

### Quick Start with Launcher Script

The easiest way to run the file manager is using the provided launcher script:

```bash
# Clone the repository
git clone https://github.com/ArturStachera/file-man.git
cd file-man

# Make the launcher executable
chmod +x run.sh

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
source .venv/bin/activate  # On Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run the file manager
python file_manager.py
```

### Optional Dependencies

For full functionality, the following packages are recommended:

```bash
# Image preview support (ANSI)
pip install pillow

# Disk usage information
pip install psutil
```

These are included in `requirements.txt` and will be installed automatically by `run.sh`.

## ⌨️ Keyboard Shortcuts

### Navigation
| Key | Action |
|-----|--------|
| `↑` / `↓` | Move selection up/down |
| `←` | Go to parent directory |
| `→` / `Enter` | Enter selected directory |
| `1-5` | Jump to shortcut (Downloads, Pictures, etc.) |

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
|-----|--------|
| `:` | Execute shell command on file |
| `/` | Search files |
| `h` | Toggle hidden files visibility |
| `u` | Check for updates |
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



Made with ❤️ and Python | Star ⭐ if you find this useful!
