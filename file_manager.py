#!/usr/bin/env python3
"""
Advanced Terminal File Manager with ASCII UI
A feature-rich file manager with tree view, preview, and disk information
"""

import curses
import os
import shutil
import shlex
import stat
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Tuple
import subprocess
import sys
import time
import urllib.request
import json

# Try to import optional dependencies
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class FileEntry:
    """Represents a file or directory entry"""
    def __init__(self, path: Path):
        self.path = path
        self.name = path.name
        self.is_dir = path.is_dir()
        self.is_hidden = self.name.startswith('.')
        try:
            self.stat = path.stat()
            self.size = self.stat.st_size
            self.modified = datetime.fromtimestamp(self.stat.st_mtime)
            self.created = datetime.fromtimestamp(self.stat.st_ctime)
            self.readable = True
        except (PermissionError, FileNotFoundError):
            self.size = 0
            self.modified = datetime.now()
            self.created = datetime.now()
            self.readable = False
    
    def get_size_str(self) -> str:
        """Convert size to human-readable format"""
        size = self.size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"


class DirectoryTree:
    """Manages directory tree structure and navigation"""
    def __init__(self, start_path: Path):
        self.current_path = start_path
        self.entries: List[FileEntry] = []
        self.selected_index = 0
        self.scroll_offset = 0
        self.show_hidden = False
        self.search_term = ""
        self.last_mtime = 0
        self.load_directory()
    
    def load_directory(self, force: bool = False):
        """Load contents of current directory"""
        try:
            current_mtime = self.current_path.stat().st_mtime
            if not force and current_mtime == self.last_mtime and self.entries:
                return False
            
            self.last_mtime = current_mtime
            items = list(self.current_path.iterdir())
            self.entries = [FileEntry(item) for item in items]
            
            if not self.show_hidden:
                self.entries = [e for e in self.entries if not e.is_hidden]
            
            if self.search_term:
                self.entries = [e for e in self.entries if self.search_term.lower() in e.name.lower()]
            
            self.entries.sort(key=lambda x: (not x.is_dir, x.name.lower()))
            
            if self.current_path != self.current_path.parent:
                parent_entry = FileEntry(self.current_path.parent)
                parent_entry.name = ".."
                self.entries.insert(0, parent_entry)
            
            self.selected_index = min(self.selected_index, len(self.entries) - 1)
            if self.selected_index < 0:
                self.selected_index = 0
            
            return True
        except PermissionError:
            self.entries = []
            return False
    
    def navigate_up(self):
        if self.selected_index > 0:
            self.selected_index -= 1
        elif self.entries:
            self.selected_index = len(self.entries) - 1
    
    def navigate_down(self):
        if self.selected_index < len(self.entries) - 1:
            self.selected_index += 1
        elif self.entries:
            self.selected_index = 0
    
    def enter_directory(self):
        if self.entries and self.entries[self.selected_index].is_dir:
            self.current_path = self.entries[self.selected_index].path
            self.selected_index = 0
            self.scroll_offset = 0
            self.last_mtime = 0
            self.load_directory(force=True)
    
    def get_selected_entry(self) -> Optional[FileEntry]:
        if self.entries:
            return self.entries[self.selected_index]
        return None


class FileOperations:
    """Handles file system operations"""
    @staticmethod
    def delete_file(path: Path) -> bool:
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            return True
        except Exception:
            return False
    
    @staticmethod
    def create_file(path: Path, is_dir: bool = False) -> bool:
        try:
            if is_dir:
                path.mkdir(parents=True, exist_ok=True)
            else:
                path.touch()
            return True
        except Exception:
            return False
    
    @staticmethod
    def copy_file(src: Path, dst: Path) -> bool:
        try:
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
            return True
        except Exception:
            return False
    
    @staticmethod
    def move_file(src: Path, dst: Path) -> bool:
        try:
            shutil.move(str(src), str(dst))
            return True
        except Exception:
            return False


class FilePreview:
    """Handles file preview generation"""
    @staticmethod
    def get_text_preview(path: Path, max_lines: int = 20) -> List[str]:
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [line.rstrip() for line in f.readlines()[:max_lines]]
                return lines
        except Exception:
            return ["[Cannot preview file]"]
    
    @staticmethod
    def get_image_preview(path: Path, width: int = 40, height: int = 20) -> List[str]:
        if not HAS_PIL:
            return ["[Image preview unavailable]", "Install Pillow: pip install pillow"]
        
        try:
            img = Image.open(path)
            aspect_ratio = img.width / img.height
            new_height = height
            new_width = int(aspect_ratio * new_height * 2.2)
            
            if new_width > width:
                new_width = width
                new_height = int(new_width / (aspect_ratio * 2.2))
            
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            img = img.convert('L')
            
            ascii_chars = " .:-=+*#%@"
            preview = []
            
            for y in range(img.height):
                line = ""
                for x in range(img.width):
                    pixel = img.getpixel((x, y))
                    char_index = min(pixel * len(ascii_chars) // 256, len(ascii_chars) - 1)
                    line += ascii_chars[char_index]
                preview.append(line)
            
            return preview
        except Exception as e:
            return [f"[Cannot preview image: {str(e)}]"]


class DiskInfo:
    """Provides disk usage information"""
    @staticmethod
    def get_disk_info() -> List[Tuple[str, int, int, int]]:
        if HAS_PSUTIL:
            disks = []
            try:
                partitions = psutil.disk_partitions()
            except (PermissionError, OSError):
                partitions = []

            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disks.append((
                        partition.mountpoint,
                        usage.total,
                        usage.used,
                        usage.free
                    ))
                except (PermissionError, OSError):
                    continue

            if disks:
                return disks

        try:
            usage = shutil.disk_usage(Path.home())
            return [(str(Path.home()), usage.total, usage.used, usage.free)]
        except Exception:
            return []
    
    @staticmethod
    def bytes_to_gb(bytes_val: int) -> float:
        return bytes_val / (1024 ** 3)


class Drive:
    """Represents a disk drive or partition."""
    def __init__(self, data: dict):
        self.name: str = data.get("name", "")
        self.type: str = data.get("type", "")
        self.size: int = int(data.get("size", 0))
        self.mountpoint: Optional[str] = data.get("mountpoint")
        self.label: Optional[str] = data.get("label")
        self.model: Optional[str] = data.get("model")
        self.is_mounted = bool(self.mountpoint)

    def get_display_name(self) -> str:
        """Get a user-friendly name for the drive."""
        if self.label:
            return self.label
        if self.model:
            return self.model
        return self.name

    def get_size_str(self) -> str:
        """Convert size to human-readable format."""
        if self.size == 0:
            return "N/A"
        size = self.size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"


class DriveManager:
    """Handles discovering and managing drives."""
    def __init__(self):
        self.drives: List[Drive] = []
        self.last_refresh = 0
        self.refresh_interval = 5  # seconds

    def list_drives(self, force: bool = False) -> List[Drive]:
        """List available block devices, filtering for disks and partitions."""
        now = time.time()
        if not force and (now - self.last_refresh) < self.refresh_interval:
            return self.drives

        self.last_refresh = now
        drives = []
        try:
            # -J for JSON, -b for bytes, -o to specify columns
            cmd = "lsblk -Jb -o NAME,TYPE,SIZE,MOUNTPOINT,LABEL,MODEL"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            
            for device in data.get("blockdevices", []):
                # We are interested in disks and their partitions
                if device.get("type") in ["disk", "loop"]:
                    # And its partitions
                    for partition in device.get("children", []):
                         if partition.get("type") in ["part", "loop"]:
                            drives.append(Drive(partition))

        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
            # lsblk might not be present, or output is malformed
            return []
        
        self.drives = sorted(drives, key=lambda d: d.name)
        return self.drives

    def mount(self, drive: Drive, password: Optional[str] = None) -> Tuple[bool, str]:
        """Mounts a drive using udisksctl."""
        if drive.is_mounted:
            return True, "Already mounted."
        
        device_path = f"/dev/{drive.name}"
        cmd = f"udisksctl mount --block-device {device_path}"
        
        try:
            # First, try without sudo
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.list_drives(force=True)
                return True, f"Mounted {drive.get_display_name()}."

            # If it fails, maybe it needs sudo
            if password:
                sudo_cmd = f"echo {shlex.quote(password)} | sudo -S -k {cmd}"
                result = subprocess.run(sudo_cmd, shell=True, capture_output=True, text=True, timeout=15)
                if result.returncode == 0:
                    self.list_drives(force=True)
                    return True, f"Mounted {drive.get_display_name()} with sudo."
                else:
                    error_msg = (result.stderr or result.stdout).strip()
                    if "incorrect password" in error_msg.lower():
                        return False, "Incorrect sudo password."
                    return False, f"Sudo mount failed: {error_msg}"
            else:
                 # Check for common graphical password prompt indicators
                if "polkit" in result.stderr.lower() or "authentication" in result.stderr.lower():
                    return False, "Needs permissions. Try with sudo."
                return False, f"Mount failed: {result.stderr.strip()}"


        except subprocess.TimeoutExpired:
            return False, "Mount command timed out."
        except Exception as e:
            return False, f"An error occurred: {str(e)}"
        
        return False, "Could not mount drive."

    def unmount(self, drive: Drive, password: Optional[str] = None) -> Tuple[bool, str]:
        """Unmounts a drive using udisksctl."""
        if not drive.is_mounted:
            return True, "Already unmounted."

        device_path = f"/dev/{drive.name}"
        cmd = f"udisksctl unmount --block-device {device_path}"

        try:
             # First, try without sudo
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.list_drives(force=True)
                return True, f"Unmounted {drive.get_display_name()}."
            
            # If it fails, maybe it needs sudo
            if password:
                sudo_cmd = f"echo {shlex.quote(password)} | sudo -S -k {cmd}"
                result = subprocess.run(sudo_cmd, shell=True, capture_output=True, text=True, timeout=15)
                if result.returncode == 0:
                    self.list_drives(force=True)
                    return True, f"Unmounted {drive.get_display_name()} with sudo."
                else:
                    return False, f"Sudo unmount failed: {(result.stderr or result.stdout).strip()}"
            else:
                if "polkit" in result.stderr.lower() or "authentication" in result.stderr.lower():
                    return False, "Needs permissions. Try with sudo."
                return False, f"Unmount failed: {result.stderr.strip()}"

        except subprocess.TimeoutExpired:
            return False, "Unmount command timed out."
        except Exception as e:
            return False, f"An error occurred: {str(e)}"
        
        return False, "Could not unmount drive."




class InputDialog:
    """Modal dialog for text input"""
    def __init__(self, stdscr, title: str, initial_text: str = ""):
        self.stdscr = stdscr
        self.title = title
        self.text = initial_text
        self.cursor_pos = len(initial_text)
    
    def show(self) -> Optional[str]:
        height, width = self.stdscr.getmaxyx()
        dialog_height = 7
        dialog_width = min(60, width - 4)
        dialog_y = (height - dialog_height) // 2
        dialog_x = (width - dialog_width) // 2
        dialog_win = curses.newwin(dialog_height, dialog_width, dialog_y, dialog_x)
        dialog_win.keypad(True)
        
        while True:
            dialog_win.clear()
            dialog_win.border()
            title_text = f" {self.title} "
            dialog_win.addstr(0, 2, title_text, curses.color_pair(5) | curses.A_BOLD)
            dialog_win.addstr(2, 2, "Enter text (ESC to cancel, Enter to confirm):")
            
            input_y = 4
            input_x = 2
            input_width = dialog_width - 4
            
            dialog_win.addch(input_y - 1, input_x - 1, curses.ACS_ULCORNER)
            dialog_win.addch(input_y - 1, input_x + input_width, curses.ACS_URCORNER)
            dialog_win.addch(input_y + 1, input_x - 1, curses.ACS_LLCORNER)
            dialog_win.addch(input_y + 1, input_x + input_width, curses.ACS_LRCORNER)
            
            for i in range(input_width):
                dialog_win.addch(input_y - 1, input_x + i, curses.ACS_HLINE)
                dialog_win.addch(input_y + 1, input_x + i, curses.ACS_HLINE)
            
            dialog_win.addch(input_y, input_x - 1, curses.ACS_VLINE)
            dialog_win.addch(input_y, input_x + input_width, curses.ACS_VLINE)
            
            display_text = self.text
            if len(display_text) >= input_width:
                display_text = display_text[-(input_width-1):]
            
            dialog_win.addstr(input_y, input_x, display_text[:input_width])
            
            cursor_display_pos = min(self.cursor_pos, input_width - 1)
            if len(self.text) >= input_width:
                cursor_display_pos = input_width - 1
            
            dialog_win.move(input_y, input_x + cursor_display_pos)
            dialog_win.refresh()
            
            key = dialog_win.getch()
            
            if key == 27:
                return None
            elif key == ord('\n'):
                return self.text
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                if self.cursor_pos > 0:
                    self.text = self.text[:self.cursor_pos-1] + self.text[self.cursor_pos:]
                    self.cursor_pos -= 1
            elif key == curses.KEY_DC:
                if self.cursor_pos < len(self.text):
                    self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos+1:]
            elif key == curses.KEY_LEFT:
                if self.cursor_pos > 0:
                    self.cursor_pos -= 1
            elif key == curses.KEY_RIGHT:
                if self.cursor_pos < len(self.text):
                    self.cursor_pos += 1
            elif key == curses.KEY_HOME:
                self.cursor_pos = 0
            elif key == curses.KEY_END:
                self.cursor_pos = len(self.text)
            elif 32 <= key <= 126:
                self.text = self.text[:self.cursor_pos] + chr(key) + self.text[self.cursor_pos:]
                self.cursor_pos += 1


class FileManagerUI:
    """Main UI renderer for the file manager"""
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.tree = DirectoryTree(Path.home())
        self.message = ""
        self.message_time = 0
        self.message_duration = 5.0
        self.clipboard: Optional[Path] = None
        self.clipboard_mode = None
        self._status_click_regions: List[Tuple[int, int, int]] = []
        self._last_click_target: Optional[Tuple[str, int]] = None
        self._last_click_time = 0.0

        self.drive_manager = DriveManager()
        self.drives: List[Drive] = []
        self.drive_selected_index = 0
        self.drive_scroll_offset = 0
        self.active_panel = "tree" # "tree", "shortcuts", "drives"

        self.shortcut_selected_index = 0
        self.shortcut_scroll_offset = 0
        
        self.current_version = "1.0.2"
        self.github_repo = "ArturStachera/file-man"
        
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
        curses.init_pair(4, curses.COLOR_RED, -1)
        curses.init_pair(5, curses.COLOR_MAGENTA, -1)
        curses.init_pair(6, curses.COLOR_WHITE, -1)
        
        self.shortcuts = [
            (Path.home() / "Downloads", "Downloads"),
            (Path.home() / "Pictures", "Pictures"),
            (Path.home() / "Videos", "Videos"),
            (Path.home() / "Documents", "Documents"),
            (Path.home() / "Desktop", "Desktop"),
        ]
    
    def set_message(self, msg: str):
        self.message = msg
        self.message_time = time.time()
    
    def get_message(self) -> str:
        if self.message and (time.time() - self.message_time) > self.message_duration:
            self.message = ""
        return self.message
    
    def draw_box(self, y: int, x: int, height: int, width: int, title: str = ""):
        try:
            self.stdscr.addch(y, x, '┌')
            self.stdscr.addch(y, x + width - 1, '┐')
            self.stdscr.addch(y + height - 1, x, '└')
            self.stdscr.addch(y + height - 1, x + width - 1, '┘')
            
            for i in range(1, width - 1):
                self.stdscr.addch(y, x + i, '─')
                self.stdscr.addch(y + height - 1, x + i, '─')
            
            for i in range(1, height - 1):
                self.stdscr.addch(y + i, x, '│')
                self.stdscr.addch(y + i, x + width - 1, '│')
            
            if title:
                title_text = f" {title} "
                self.stdscr.addstr(y, x + 2, title_text, curses.color_pair(5) | curses.A_BOLD)
        except curses.error:
            pass
    
    def draw_shortcuts(self, y: int, x: int, height: int, width: int):
        title = "Shortcuts"
        if self.active_panel == "shortcuts":
            title = f"<{title}>"
        self.draw_box(y, x, height, width, title)
        
        row = y + 1
        visible_height = height - 2
        start_idx = self.shortcut_scroll_offset
        end_idx = start_idx + visible_height

        for idx in range(start_idx, min(end_idx, len(self.shortcuts))):
            if row >= y + height - 1:
                break
            
            path, name = self.shortcuts[idx]
            color = curses.color_pair(1) if path.exists() else curses.color_pair(4)
            
            if idx == self.shortcut_selected_index:
                color = curses.color_pair(3) | curses.A_BOLD
            
            text = f" 📁 {name}"
            try:
                self.stdscr.addstr(row, x + 2, text[:width-4], color)
            except curses.error:
                pass
            row += 1

    def draw_drives(self, y: int, x: int, height: int, width: int):
        title = "Drives"
        if self.active_panel == "drives":
            title = f"<{title}>"
        self.draw_box(y, x, height, width, title)
        
        row = y + 1
        visible_height = height - 2
        start_idx = self.drive_scroll_offset
        end_idx = start_idx + visible_height

        for idx in range(start_idx, min(end_idx, len(self.drives))):
            if row >= y + height - 1:
                break
            
            drive = self.drives[idx]
            icon = "💾"
            color = curses.color_pair(6) # Default color
            
            if drive.is_mounted:
                icon = "🟢" # Green circle for mounted
            else:
                icon = "⚪" # White circle for unmounted
                
            if idx == self.drive_selected_index:
                color = curses.color_pair(3) | curses.A_BOLD

            name = drive.get_display_name()
            size_str = drive.get_size_str()
            text = f" {icon} {name} ({size_str})"

            try:
                self.stdscr.addstr(row, x + 2, text[:width-4], color)
            except curses.error:
                pass
            row += 1
    
    def draw_directory_tree(self, y: int, x: int, height: int, width: int):
        title = "Directory Tree"
        if self.active_panel == "tree":
            title = f"<{title}>"
        self.draw_box(y, x, height, width, title)
        
        path_str = str(self.tree.current_path)
        if len(path_str) > width - 6:
            path_str = "..." + path_str[-(width-9):]
        try:
            self.stdscr.addstr(y + 1, x + 2, path_str[:width-4], curses.color_pair(6))
        except curses.error:
            pass
        
        if self.tree.search_term:
            search_text = f"Search: {self.tree.search_term}"
            try:
                self.stdscr.addstr(y + 2, x + 2, search_text[:width-4], curses.color_pair(3))
            except curses.error:
                pass
        
        sep_y = y + (3 if self.tree.search_term else 2)
        for i in range(1, width - 1):
            try:
                self.stdscr.addch(sep_y, x + i, '─')
            except curses.error:
                pass
        
        visible_height = height - (5 if self.tree.search_term else 4)
        start_idx = self.tree.scroll_offset
        end_idx = start_idx + visible_height
        
        row = sep_y + 1
        for idx in range(start_idx, min(end_idx, len(self.tree.entries))):
            if row >= y + height - 1:
                break
            
            entry = self.tree.entries[idx]
            
            if entry.is_dir:
                icon = "📁"
                color = curses.color_pair(1)
            elif entry.readable and os.access(entry.path, os.X_OK):
                icon = "⚙"
                color = curses.color_pair(2)
            else:
                icon = "📄"
                color = curses.color_pair(6)
            
            if idx == self.tree.selected_index:
                color = curses.color_pair(3) | curses.A_BOLD
            
            name = entry.name
            if len(name) > width - 8:
                name = name[:width-11] + "..."
            
            text = f" {icon} {name}"
            try:
                self.stdscr.addstr(row, x + 2, text[:width-4], color)
            except curses.error:
                pass
            
            row += 1
    
    def draw_file_info(self, y: int, x: int, height: int, width: int):
        self.draw_box(y, x, height, width, "File Info")
        
        entry = self.tree.get_selected_entry()
        if not entry:
            return
        
        row = y + 1
        info_lines = [
            f"Name: {entry.name}",
            f"Type: {'Directory' if entry.is_dir else 'File'}",
            f"Size: {entry.get_size_str() if not entry.is_dir else 'N/A'}",
            f"Modified: {entry.modified.strftime('%Y-%m-%d %H:%M')}",
            f"Created: {entry.created.strftime('%Y-%m-%d %H:%M')}",
            f"Readable: {'Yes' if entry.readable else 'No'}",
        ]
        
        if self.clipboard:
            info_lines.append("")
            info_lines.append(f"Clipboard: {self.clipboard_mode}")
            info_lines.append(f"{self.clipboard.name}")
        
        for line in info_lines:
            if row >= y + height - 1:
                break
            try:
                self.stdscr.addstr(row, x + 2, line[:width-4], curses.color_pair(6))
            except curses.error:
                pass
            row += 1
    
    def draw_file_preview(self, y: int, x: int, height: int, width: int):
        self.draw_box(y, x, height, width, "Preview")
        
        entry = self.tree.get_selected_entry()
        if not entry or entry.is_dir:
            return
        
        ext = entry.path.suffix.lower()
        preview_lines = []
        
        if ext in ['.txt', '.py', '.java', '.c', '.cpp', '.h', '.js', '.html', '.css', '.md', '.json', '.xml', '.yml', '.yaml', '.sh', '.conf', '.cfg']:
            preview_lines = FilePreview.get_text_preview(entry.path, height - 3)
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']:
            preview_lines = FilePreview.get_image_preview(entry.path, width - 4, height - 3)
        else:
            preview_lines = ["[No preview available]", f"File type: {ext}"]
        
        row = y + 1
        for line in preview_lines:
            if row >= y + height - 1:
                break
            try:
                self.stdscr.addstr(row, x + 2, line[:width-4], curses.color_pair(6))
            except curses.error:
                pass
            row += 1
    
    def draw_disk_info(self, y: int, x: int, width: int):
        disks = DiskInfo.get_disk_info()
        
        if not disks:
            if not HAS_PSUTIL:
                info = "Disk info unavailable (install psutil: pip install psutil)"
            else:
                info = "Disk info unavailable"
            try:
                self.stdscr.addstr(y, x, info[:width], curses.color_pair(6))
            except curses.error:
                pass
            return
        
        if disks:
            mount, total, used, free = disks[0]
            percent = int((used / total) * 100) if total > 0 else 0
            bar_width = 20
            filled = int((percent / 100) * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)
            info = f" {mount} [{bar}] {percent}%  Free: {DiskInfo.bytes_to_gb(free):.1f}GB"
            try:
                self.stdscr.addstr(y, x + 2, info[:width-4], curses.color_pair(6))
            except curses.error:
                pass
    
    def draw_status_bar(self, y: int, x: int, width: int):
        help_text = "q:Quit d:Del n:New e:Edit c:Copy v:Paste x:Cut r:Rename u:Unmount ::Cmd /:Search h:Hidden"
        
        try:
            self.stdscr.addstr(y, x, help_text[:width-25], curses.color_pair(5))
        except curses.error:
            pass

        self._status_click_regions = []
        display_limit = max(0, width - 25)
        cursor = 0
        for token in help_text.split(' '):
            token_len = len(token)
            if cursor + token_len > display_limit:
                break
            mapped_key: Optional[int] = None
            if token.startswith('q:'):
                mapped_key = ord('q')
            elif token.startswith('d:'):
                mapped_key = ord('d')
            elif token.startswith('n:'):
                mapped_key = ord('n')
            elif token.startswith('e:'):
                mapped_key = ord('e')
            elif token.startswith('c:'):
                mapped_key = ord('c')
            elif token.startswith('v:'):
                mapped_key = ord('v')
            elif token.startswith('x:'):
                mapped_key = ord('x')
            elif token.startswith('r:'):
                mapped_key = ord('r')
            elif token.startswith('u:'):
                mapped_key = ord('u')
            elif token.startswith('::'):
                mapped_key = ord(':')
            elif token.startswith('/:'):
                mapped_key = ord('/')
            elif token.startswith('h:'):
                mapped_key = ord('h')
            if mapped_key is not None:
                self._status_click_regions.append((x + cursor, x + cursor + token_len - 1, mapped_key))
            cursor += token_len + 1
        
        update_text = "┌─────────────────┐"
        update_btn = "│ U: Check Update │"
        update_end = "└─────────────────┘"
        
        try:
            self.stdscr.addstr(y - 2, width - 21, update_text, curses.color_pair(5))
            self.stdscr.addstr(y - 1, width - 21, update_btn, curses.color_pair(5))
            self.stdscr.addstr(y, width - 21, update_end, curses.color_pair(5))
        except curses.error:
            pass
        
        message = self.get_message()
        if message:
            try:
                msg_x = max(0, width - len(message) - 25)
                self.stdscr.addstr(y, x + msg_x, message[:width-msg_x-25], curses.color_pair(4))
            except curses.error:
                pass

    def navigate_shortcut_up(self):
        if self.shortcut_selected_index > 0:
            self.shortcut_selected_index -= 1
        elif self.shortcuts:
            self.shortcut_selected_index = len(self.shortcuts) - 1

    def navigate_shortcut_down(self):
        if self.shortcut_selected_index < len(self.shortcuts) - 1:
            self.shortcut_selected_index += 1
        elif self.shortcuts:
            self.shortcut_selected_index = 0

    def navigate_drive_up(self):
        if self.drive_selected_index > 0:
            self.drive_selected_index -= 1
        elif self.drives:
            self.drive_selected_index = len(self.drives) - 1

    def navigate_drive_down(self):
        if self.drive_selected_index < len(self.drives) - 1:
            self.drive_selected_index += 1
        elif self.drives:
            self.drive_selected_index = 0

    def handle_mouse(self, my: int, mx: int, bstate: int):
        height, width = self.stdscr.getmaxyx()

        shortcuts_width = 25
        info_width = 30
        tree_width = width - shortcuts_width - info_width - 3
        top_height = height // 2

        shortcuts_h = min(8, top_height)
        drives_y = shortcuts_h
        drives_h = top_height - shortcuts_h
        
        update_x = width - 21
        update_y_top = height - 3
        update_y_bottom = height - 1

        button1_clicked = getattr(curses, 'BUTTON1_CLICKED', 0)
        button1_pressed = getattr(curses, 'BUTTON1_PRESSED', 0)
        button1_released = getattr(curses, 'BUTTON1_RELEASED', 0)
        button1_double = getattr(curses, 'BUTTON1_DOUBLE_CLICKED', 0)
        button4_pressed = getattr(curses, 'BUTTON4_PRESSED', 0)
        button5_pressed = getattr(curses, 'BUTTON5_PRESSED', 0)

        is_click = bool(bstate & button1_clicked)
        is_double = bool(bstate & button1_double)
        if not is_click and not is_double:
            if (bstate & button1_released) and not (bstate & button1_pressed):
                is_click = True

        if my == height - 1:
            for x1, x2, mapped_key in self._status_click_regions:
                if x1 <= mx <= x2:
                    if is_click:
                        return self.handle_input(mapped_key)
                    return True

        if update_y_top <= my <= update_y_bottom and update_x <= mx <= width - 1:
            if is_click:
                return self.check_for_updates()

        if 0 <= my < shortcuts_h and 0 <= mx < shortcuts_width:
            self.active_panel = "shortcuts"
            if bstate & button4_pressed:
                self.navigate_shortcut_up()
                return True
            if bstate & button5_pressed:
                self.navigate_shortcut_down()
                return True

            if is_click or is_double:
                row_start = 1
                row_end = shortcuts_h - 2
                if row_start <= my <= row_end:
                    idx = self.shortcut_scroll_offset + (my - row_start)
                    if 0 <= idx < len(self.shortcuts):
                        self.shortcut_selected_index = idx
                        now = time.time()
                        target = ("shortcut", idx)
                        activate = False
                        if is_double:
                            activate = True
                        elif is_click and self._last_click_target == target and (now - self._last_click_time) < 0.40:
                            activate = True
                        
                        self._last_click_target = target
                        self._last_click_time = now

                        if activate:
                            self.handle_input(ord('\n'))
            return True

        if drives_y <= my < drives_y + drives_h and 0 <= mx < shortcuts_width:
            self.active_panel = "drives"
            if bstate & button4_pressed:
                self.navigate_drive_up()
                return True
            if bstate & button5_pressed:
                self.navigate_drive_down()
                return True
            
            if is_click or is_double:
                row_start = drives_y + 1
                row_end = drives_y + drives_h - 2
                if row_start <= my <= row_end:
                    idx = self.drive_scroll_offset + (my - row_start)
                    if 0 <= idx < len(self.drives):
                        self.drive_selected_index = idx
                        now = time.time()
                        target = ("drive", idx)
                        activate = False
                        if is_double:
                            activate = True
                        elif is_click and self._last_click_target == target and (now - self._last_click_time) < 0.40:
                            activate = True
                        
                        self._last_click_target = target
                        self._last_click_time = now

                        if activate:
                            # Emulate enter key press
                            self.handle_input(ord('\n'))

            return True

        tree_x = shortcuts_width + 1
        tree_y = 0
        if tree_y <= my < top_height and tree_x <= mx < tree_x + tree_width:
            self.active_panel = "tree"
            if bstate & button4_pressed:
                self.tree.navigate_up()
                return True
            if bstate & button5_pressed:
                self.tree.navigate_down()
                return True

            if is_click or is_double:
                sep_y = tree_y + (3 if self.tree.search_term else 2)
                row_start = sep_y + 1
                row_end = tree_y + top_height - 2
                if row_start <= my <= row_end:
                    idx = self.tree.scroll_offset + (my - row_start)
                    if 0 <= idx < len(self.tree.entries):
                        self.tree.selected_index = idx
                        now = time.time()
                        target = ("tree", idx)
                        activate = False
                        if is_double:
                            activate = True
                        elif is_click and self._last_click_target == target and (now - self._last_click_time) < 0.40:
                            activate = True
                        self._last_click_target = target
                        self._last_click_time = now
                        if activate:
                            entry = self.tree.get_selected_entry()
                            if entry and entry.is_dir:
                                self.tree.enter_directory()
            return True

        return True
    
    def edit_file(self, file_path: Path):
        curses.def_prog_mode()
        curses.endwin()
        os.system('clear')
        
        try:
            editors = ['nvim', 'vim', 'nano']
            editor = None
            for ed in editors:
                if shutil.which(ed):
                    editor = ed
                    break
            
            if editor:
                subprocess.run([editor, str(file_path)])
                self.set_message(f"Edited with {editor}")
            else:
                self.set_message("No editor found (nvim, vim, nano)")
        except Exception as e:
            self.set_message(f"Edit error: {str(e)}")
        finally:
            curses.reset_prog_mode()
            self.stdscr.refresh()
            self.tree.load_directory(force=True)
    
    def execute_command(self, command: str, file_path: Path):
        curses.def_prog_mode()
        curses.endwin()
        os.system('clear')
        
        try:
            if '{file}' in command:
                cmd = command.replace('{file}', shlex.quote(str(file_path)))
            else:
                cmd = f"{command} {shlex.quote(str(file_path))}"
            
            subprocess.run(cmd, shell=True, capture_output=False, text=True)
            print("\n\nPress Enter to continue...")
            input()
            self.set_message(f"Command executed: {command}")
        except Exception as e:
            print(f"\nError: {str(e)}")
            print("Press Enter to continue...")
            input()
            self.set_message(f"Command error: {str(e)}")
        finally:
            curses.reset_prog_mode()
            self.stdscr.refresh()
            self.tree.load_directory(force=True)
    
    def check_for_updates(self) -> bool:
        curses.def_prog_mode()
        curses.endwin()
        os.system('clear')
        
        try:
            print("🔍 Checking for updates...")
            print(f"Current version: {self.current_version}\n")
            
            api_url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
            req = urllib.request.Request(api_url)
            req.add_header('User-Agent', 'Terminal-File-Manager')
            
            try:
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode())
                    latest_version = data.get('tag_name', '').lstrip('v')
                    
                    if not latest_version:
                        print("⚠️ Cannot determine version.")
                        print("\nPress Enter to continue...")
                        input()
                        curses.reset_prog_mode()
                        self.stdscr.refresh()
                        return True
                    
                    print(f"Latest version: {latest_version}\n")
                    
                    if latest_version > self.current_version:
                        print(f"🎉 New version available: {latest_version}")
                        print(f"Current version: {self.current_version}")
                        print("\nDo you want to update now? (y/n): ", end='', flush=True)
                        choice = input().lower().strip()
                        
                        if choice != 'y':
                            print("\nUpdate cancelled.")
                            print("Press Enter to continue...")
                            input()
                            curses.reset_prog_mode()
                            self.stdscr.refresh()
                            return True
                        
                        print("\n📥 Updating...")
                        
                        if subprocess.run(['git', 'rev-parse', '--git-dir'], capture_output=True).returncode != 0:
                            print("❌ Not a git repository!")
                            print("\nPress Enter to continue...")
                            input()
                            curses.reset_prog_mode()
                            self.stdscr.refresh()
                            return True
                        
                        print("Resetting local changes...")
                        if subprocess.run(['git', 'reset', '--hard', 'HEAD'], capture_output=True).returncode != 0:
                            print("❌ Reset failed!")
                            print("\nPress Enter to continue...")
                            input()
                            curses.reset_prog_mode()
                            self.stdscr.refresh()
                            return True
                        
                        print("Cleaning cache...")
                        subprocess.run(['git', 'clean', '-fd'], capture_output=True)
                        
                        print("Downloading updates...")
                        if subprocess.run(['git', 'pull', 'origin', 'main'], capture_output=True).returncode != 0:
                            print("❌ Update failed!")
                            print("\nPress Enter to continue...")
                            input()
                            curses.reset_prog_mode()
                            self.stdscr.refresh()
                            return True
                        
                        try:
                            os.chmod(Path(__file__).parent / 'run.sh', 0o755)
                        except:
                            pass
                        
                        os.system('clear')
                        print("\n" + "="*60)
                        print("  ✅ UPDATE SUCCESSFUL!")
                        print(f"  v{self.current_version} → v{latest_version}")
                        print()
                        print("  Restart: ./run.sh")
                        print("="*60)
                        print("\nPress Enter to exit...")
                        input()
                        os._exit(0)
                    else:
                        print(f"✅ You're up to date! (v{self.current_version})")
                        print("\nPress Enter to continue...")
                        input()
                        curses.reset_prog_mode()
                        self.stdscr.refresh()
                        return True
                        
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    print("✅ No updates available.")
                else:
                    print("❌ Cannot check for updates.")
                print("\nPress Enter to continue...")
                input()
                curses.reset_prog_mode()
                self.stdscr.refresh()
                return True
                    
        except Exception:
            print("❌ Cannot check for updates.")
            print("\nPress Enter to continue...")
            input()
            curses.reset_prog_mode()
            self.stdscr.refresh()
            return True
        
        return True
    
    def draw(self):
        self.stdscr.erase()
        height, width = self.stdscr.getmaxyx()
        
        shortcuts_width = 25
        info_width = 30
        tree_width = width - shortcuts_width - info_width - 3
        
        top_height = height // 2
        bottom_height = height - top_height - 3
        
        shortcuts_h = min(8, top_height)
        drives_y = shortcuts_h
        drives_h = top_height - shortcuts_h

        self.draw_shortcuts(0, 0, shortcuts_h, shortcuts_width)
        if drives_h > 2:
            self.draw_drives(drives_y, 0, drives_h, shortcuts_width)

        self.draw_directory_tree(0, shortcuts_width + 1, top_height, tree_width)
        self.draw_file_info(0, shortcuts_width + tree_width + 2, top_height, info_width)
        self.draw_file_preview(top_height, 0, bottom_height, width)
        self.draw_disk_info(height - 2, 0, width)
        self.draw_status_bar(height - 1, 0, width)
        
        self.stdscr.noutrefresh()
        curses.doupdate()
    
    def handle_input(self, key: int):
        if key == curses.KEY_MOUSE:
            try:
                _, mx, my, _, bstate = curses.getmouse()
            except Exception:
                return True
            result = self.handle_mouse(my, mx, bstate)
            # Mouse handling might change the active panel or selection, so we ensure visiblity
            self.ensure_selection_visible()
            return result

        entry = self.tree.get_selected_entry()

        if key == ord('\t'):
            panels = ["tree", "drives", "shortcuts"]
            try:
                current_index = panels.index(self.active_panel)
                self.active_panel = panels[(current_index + 1) % len(panels)]
            except ValueError:
                self.active_panel = "tree"
        
        elif key == curses.KEY_UP:
            if self.active_panel == "tree":
                self.tree.navigate_up()
            elif self.active_panel == "drives":
                self.navigate_drive_up()
            elif self.active_panel == "shortcuts":
                self.navigate_shortcut_up()

        elif key == curses.KEY_DOWN:
            if self.active_panel == "tree":
                self.tree.navigate_down()
            elif self.active_panel == "drives":
                self.navigate_drive_down()
            elif self.active_panel == "shortcuts":
                self.navigate_shortcut_down()

        elif key == curses.KEY_RIGHT or key == ord('\n'):
            if self.active_panel == "tree":
                self.tree.enter_directory()
            elif self.active_panel == "shortcuts" and self.shortcuts:
                 if 0 <= self.shortcut_selected_index < len(self.shortcuts):
                    path, name = self.shortcuts[self.shortcut_selected_index]
                    if path.exists():
                        self.tree.current_path = path
                        self.tree.selected_index = 0
                        self.tree.search_term = ""
                        self.tree.last_mtime = 0
                        self.tree.load_directory(force=True)
                    else:
                        self.set_message(f"Path does not exist: {name}")
            elif self.active_panel == "drives" and self.drives:
                if 0 <= self.drive_selected_index < len(self.drives):
                    drive = self.drives[self.drive_selected_index]
                    if drive.is_mounted and drive.mountpoint:
                        self.tree.current_path = Path(drive.mountpoint)
                        self.tree.selected_index = 0
                        self.tree.last_mtime = 0
                        self.tree.load_directory(force=True)
                        self.set_message(f"Opened {drive.get_display_name()}")
                    elif not drive.is_mounted:
                        success, message = self.drive_manager.mount(drive)
                        if "Needs permissions" in message:
                            dialog = InputDialog(self.stdscr, f"Sudo password for mounting {drive.name}", "")
                            password = dialog.show()
                            if password is not None:
                                success, message = self.drive_manager.mount(drive, password)
                        self.set_message(message)
                        if success:
                            self.drives = self.drive_manager.list_drives(force=True)

        elif key == curses.KEY_LEFT:
            if self.active_panel == "tree":
                self.tree.current_path = self.tree.current_path.parent
                self.tree.selected_index = 0
                self.tree.last_mtime = 0
                self.tree.load_directory(force=True)

        elif key == ord('u'):
            if self.active_panel == "drives" and self.drives:
                if 0 <= self.drive_selected_index < len(self.drives):
                    drive = self.drives[self.drive_selected_index]
                    if drive.is_mounted and drive.mountpoint:
                        mountpoint_before_unmount = drive.mountpoint
                        success, message = self.drive_manager.unmount(drive)
                        
                        if "Needs permissions" in message:
                            dialog = InputDialog(self.stdscr, f"Sudo password for unmounting {drive.name}", "")
                            password = dialog.show()
                            if password is not None:
                                success, message = self.drive_manager.unmount(drive, password)
                        
                        if success:
                            self.drives = self.drive_manager.list_drives(force=True) # Refresh drive list
                            
                            # Check if we were inside the unmounted drive
                            if mountpoint_before_unmount and str(self.tree.current_path).startswith(mountpoint_before_unmount):
                                self.tree.current_path = Path.home()
                                self.tree.selected_index = 0
                                self.tree.scroll_offset = 0
                                self.set_message(f"Unmounted. Path reset to home.")
                            else:
                                self.set_message(message)
                            self.tree.load_directory(force=True) # Refresh tree view
                        else:
                            self.set_message(message)
                    else:
                        self.set_message("Drive is not mounted.")
        
        elif key == ord('U'):
            return self.check_for_updates()

        elif key == ord('d') and entry and entry.name != ".." and self.active_panel == "tree":
            if FileOperations.delete_file(entry.path):
                self.set_message("Deleted successfully")
                self.tree.load_directory(force=True)
            else:
                self.set_message("Delete failed")
        elif key == ord('e') and entry and entry.name != ".." and self.active_panel == "tree":
            if not entry.is_dir:
                self.edit_file(entry.path)
            else:
                self.set_message("Cannot edit directory")
        elif key == ord(':') and entry and entry.name != ".." and self.active_panel == "tree":
            dialog = InputDialog(self.stdscr, "Execute command (use {file} for path)", "")
            result = dialog.show()
            if result:
                self.execute_command(result, entry.path)
        
        elif key == ord('n') and self.active_panel == "tree":
            dialog = InputDialog(self.stdscr, "Create (f:file d:directory) name")
            result = dialog.show()
            if result:
                if result.startswith('f '):
                    name = result[2:]
                    new_path = self.tree.current_path / name
                    if FileOperations.create_file(new_path, is_dir=False):
                        self.set_message("File created")
                        self.tree.load_directory(force=True)
                    else:
                        self.set_message("Failed to create file")
                elif result.startswith('d '):
                    name = result[2:]
                    new_path = self.tree.current_path / name
                    if FileOperations.create_file(new_path, is_dir=True):
                        self.set_message("Directory created")
                        self.tree.load_directory(force=True)
                    else:
                        self.set_message("Failed to create directory")
                else:
                    self.set_message("Use 'f name' or 'd name'")
        elif key == ord('r') and entry and entry.name != ".." and self.active_panel == "tree":
            dialog = InputDialog(self.stdscr, "Rename to", entry.name)
            result = dialog.show()
            if result:
                new_path = entry.path.parent / result
                if FileOperations.move_file(entry.path, new_path):
                    self.set_message("Renamed successfully")
                    self.tree.load_directory(force=True)
                else:
                    self.set_message("Rename failed")
        elif key == ord('c') and entry and entry.name != ".." and self.active_panel == "tree":
            self.clipboard = entry.path
            self.clipboard_mode = "copy"
            self.set_message(f"Copied: {entry.name}")
        elif key == ord('x') and entry and entry.name != ".." and self.active_panel == "tree":
            self.clipboard = entry.path
            self.clipboard_mode = "cut"
            self.set_message(f"Cut: {entry.name}")
        elif key == ord('v') and self.clipboard and self.active_panel == "tree":
            dest_path = self.tree.current_path / self.clipboard.name
            
            if dest_path.exists():
                counter = 1
                stem = self.clipboard.stem
                suffix = self.clipboard.suffix
                while dest_path.exists():
                    dest_path = self.tree.current_path / f"{stem}_{counter}{suffix}"
                    counter += 1
            
            if self.clipboard_mode == "copy":
                if FileOperations.copy_file(self.clipboard, dest_path):
                    self.set_message("Pasted successfully")
                    self.tree.load_directory(force=True)
                else:
                    self.set_message("Paste failed")
            elif self.clipboard_mode == "cut":
                if FileOperations.move_file(self.clipboard, dest_path):
                    self.set_message("Moved successfully")
                    self.clipboard = None
                    self.clipboard_mode = None
                    self.tree.load_directory(force=True)
                else:
                    self.set_message("Move failed")
        elif key == ord('/'):
            dialog = InputDialog(self.stdscr, "Search files", self.tree.search_term)
            result = dialog.show()
            if result is not None:
                self.tree.search_term = result
                self.tree.selected_index = 0
                self.tree.load_directory(force=True)
        elif key == 27:
            if self.tree.search_term:
                self.tree.search_term = ""
                self.tree.load_directory(force=True)
        elif key == ord('h'):
            self.tree.show_hidden = not self.tree.show_hidden
            self.tree.load_directory(force=True)
            self.set_message(f"Hidden files: {'shown' if self.tree.show_hidden else 'hidden'}")
        elif key == ord('q'):
            return False
        
        self.ensure_selection_visible()
        
        return True

    def ensure_selection_visible(self):
        """Adjusts scroll offsets to make sure the selected item is visible."""
        height, width = self.stdscr.getmaxyx()
        shortcuts_h = min(8, height // 2)

        if self.active_panel == "shortcuts":
            visible_height = shortcuts_h - 2
            if visible_height > 0:
                if self.shortcut_selected_index < self.shortcut_scroll_offset:
                    self.shortcut_scroll_offset = self.shortcut_selected_index
                elif self.shortcut_selected_index >= self.shortcut_scroll_offset + visible_height:
                    self.shortcut_scroll_offset = self.shortcut_selected_index - visible_height + 1
        elif self.active_panel == "tree":
            visible_height = height // 2 - (5 if self.tree.search_term else 4)
            if self.tree.selected_index < self.tree.scroll_offset:
                self.tree.scroll_offset = self.tree.selected_index
            elif self.tree.selected_index >= self.tree.scroll_offset + visible_height:
                self.tree.scroll_offset = self.tree.selected_index - visible_height + 1
        elif self.active_panel == "drives":
            drives_h = (height // 2) - shortcuts_h
            visible_height = drives_h - 2
            if visible_height > 0:
                if self.drive_selected_index < self.drive_scroll_offset:
                    self.drive_scroll_offset = self.drive_selected_index
                elif self.drive_selected_index >= self.drive_scroll_offset + visible_height:
                    self.drive_scroll_offset = self.drive_selected_index - visible_height + 1
    
    def run(self):
        running = True
        refresh_counter = 0
        self.drives = self.drive_manager.list_drives(force=True) # Initial load
        while running:
            refresh_counter += 1
            if refresh_counter >= 100: # Refresh every 10 seconds
                self.tree.load_directory()
                self.drives = self.drive_manager.list_drives()
                refresh_counter = 0
            
            self.draw()
            key = self.stdscr.getch()
            if key != -1:
                running = self.handle_input(key)


def main(stdscr):
    curses.curs_set(0)
    stdscr.keypad(True)
    stdscr.timeout(100)

    try:
        curses.mouseinterval(0)
    except Exception:
        pass
    try:
        curses.mousemask(curses.ALL_MOUSE_EVENTS | getattr(curses, 'REPORT_MOUSE_POSITION', 0))
    except Exception:
        pass
    
    ui = FileManagerUI(stdscr)
    ui.run()


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
