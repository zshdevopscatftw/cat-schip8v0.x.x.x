#!/usr/bin/env python3
"""
Cat's CHIP8 EMU - Project 64 0.1 GUI
Complete Chip-8 emulator with fully functional Project64-inspired GUI.

Features:
- Full Chip-8 + Super Chip-8 instruction set
- Project64-style dark theme GUI
- Drag & Drop ROM loading
- Working menus, toolbar, debug panel
- Save/Load states
- Configurable colors and speed

(c) 2025 Cat's Emulation Team
"""

import pygame
import pygame.freetype
import sys
import os
import random
import math
import array
import time
from typing import List, Tuple, Dict, Callable, Optional

# ============================================================================
# CONSTANTS
# ============================================================================

CHIP8_WIDTH, CHIP8_HEIGHT = 64, 32
SCHIP_WIDTH, SCHIP_HEIGHT = 128, 64

WINDOW_WIDTH = 960
WINDOW_HEIGHT = 680
MENUBAR_H = 26
TOOLBAR_H = 40
STATUSBAR_H = 24

DISPLAY_X = 16
DISPLAY_Y = MENUBAR_H + TOOLBAR_H + 12
DISPLAY_W = 640
DISPLAY_H = 320

DEBUG_X = DISPLAY_X + DISPLAY_W + 16
DEBUG_Y = DISPLAY_Y
DEBUG_W = 260
DEBUG_H = 380

# Project64 Dark Theme Colors
BG_DARK = (22, 22, 26)
BG_MED = (32, 34, 38)
BG_LIGHT = (48, 50, 56)
BG_HOVER = (62, 65, 72)
BG_ACTIVE = (75, 80, 90)
BORDER = (58, 60, 68)
TEXT = (210, 212, 218)
TEXT_DIM = (120, 124, 135)
ACCENT = (82, 148, 226)
ACCENT_HI = (102, 168, 246)
GREEN = (72, 199, 116)
YELLOW = (255, 193, 77)
RED = (239, 98, 98)

PIX_OFF = (8, 10, 14)
PIX_ON = (45, 255, 120)

MEMORY_SIZE = 4096
PROGRAM_START = 0x200
TIMER_HZ = 60

FONTSET = bytes([
    0xF0,0x90,0x90,0x90,0xF0, 0x20,0x60,0x20,0x20,0x70,
    0xF0,0x10,0xF0,0x80,0xF0, 0xF0,0x10,0xF0,0x10,0xF0,
    0x90,0x90,0xF0,0x10,0x10, 0xF0,0x80,0xF0,0x10,0xF0,
    0xF0,0x80,0xF0,0x90,0xF0, 0xF0,0x10,0x20,0x40,0x40,
    0xF0,0x90,0xF0,0x90,0xF0, 0xF0,0x90,0xF0,0x10,0xF0,
    0xF0,0x90,0xF0,0x90,0x90, 0xE0,0x90,0xE0,0x90,0xE0,
    0xF0,0x80,0x80,0x80,0xF0, 0xE0,0x90,0x90,0x90,0xE0,
    0xF0,0x80,0xF0,0x80,0xF0, 0xF0,0x80,0xF0,0x80,0x80,
])

SCHIP_FONT = bytes([
    0x3C,0x7E,0xE7,0xC3,0xC3,0xC3,0xC3,0xE7,0x7E,0x3C,
    0x18,0x38,0x58,0x18,0x18,0x18,0x18,0x18,0x18,0x3C,
    0x3E,0x7F,0xC3,0x06,0x0C,0x18,0x30,0x60,0xFF,0xFF,
    0x3C,0x7E,0xC3,0x03,0x0E,0x0E,0x03,0xC3,0x7E,0x3C,
    0x06,0x0E,0x1E,0x36,0x66,0xC6,0xFF,0xFF,0x06,0x06,
    0xFF,0xFF,0xC0,0xC0,0xFC,0xFE,0x03,0xC3,0x7E,0x3C,
    0x3E,0x7C,0xC0,0xC0,0xFC,0xFE,0xC3,0xC3,0x7E,0x3C,
    0xFF,0xFF,0x03,0x06,0x0C,0x18,0x30,0x60,0x60,0x60,
    0x3C,0x7E,0xC3,0xC3,0x7E,0x7E,0xC3,0xC3,0x7E,0x3C,
    0x3C,0x7E,0xC3,0xC3,0x7F,0x3F,0x03,0x03,0x3E,0x7C,
])

KEY_MAP = {
    pygame.K_1: 0x1, pygame.K_2: 0x2, pygame.K_3: 0x3, pygame.K_4: 0xC,
    pygame.K_q: 0x4, pygame.K_w: 0x5, pygame.K_e: 0x6, pygame.K_r: 0xD,
    pygame.K_a: 0x7, pygame.K_s: 0x8, pygame.K_d: 0x9, pygame.K_f: 0xE,
    pygame.K_z: 0xA, pygame.K_x: 0x0, pygame.K_c: 0xB, pygame.K_v: 0xF,
}


# ============================================================================
# PYGAME FILE BROWSER (No tkinter needed!)
# ============================================================================

class FileBrowser:
    """Pure pygame file browser - no tkinter conflicts on macOS!"""
    
    def __init__(self, screen, font, start_path=None):
        self.screen = screen
        self.font = font
        self.path = start_path or os.path.expanduser("~")
        self.selected = 0
        self.scroll = 0
        self.files = []
        self.result = None
        self.active = False
        self.extensions = ('.ch8', '.c8', '.rom', '.bin')
        self._refresh()
    
    def _refresh(self):
        """Refresh file list."""
        self.files = []
        try:
            # Parent directory
            if self.path != '/':
                self.files.append(('..', True))
            
            items = []
            for name in os.listdir(self.path):
                if name.startswith('.'):
                    continue
                full = os.path.join(self.path, name)
                is_dir = os.path.isdir(full)
                # Show directories and matching files
                if is_dir or name.lower().endswith(self.extensions):
                    items.append((name, is_dir))
            
            # Sort: directories first, then files
            items.sort(key=lambda x: (not x[1], x[0].lower()))
            self.files.extend(items)
            
        except PermissionError:
            self.files = [('.. (Permission Denied)', True)]
        
        self.selected = 0
        self.scroll = 0
    
    def open(self):
        """Open the file browser."""
        self.active = True
        self.result = None
        self._refresh()
    
    def close(self):
        """Close the file browser."""
        self.active = False
    
    def draw(self):
        """Draw the file browser."""
        if not self.active:
            return
        
        sw, sh = self.screen.get_size()
        
        # Darken background
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        # Dialog box
        bw, bh = 500, 400
        bx, by = (sw - bw) // 2, (sh - bh) // 2
        
        pygame.draw.rect(self.screen, BG_MED, (bx, by, bw, bh), border_radius=8)
        pygame.draw.rect(self.screen, BORDER, (bx, by, bw, bh), 2, border_radius=8)
        
        # Title bar
        pygame.draw.rect(self.screen, BG_LIGHT, (bx, by, bw, 32), border_radius=8)
        pygame.draw.rect(self.screen, BG_LIGHT, (bx, by + 16, bw, 16))
        ts, _ = self.font.render("Open ROM File", TEXT)
        self.screen.blit(ts, (bx + 12, by + 8))
        
        # Current path
        path_display = self.path
        if len(path_display) > 55:
            path_display = "..." + path_display[-52:]
        ts, _ = self.font.render(path_display, TEXT_DIM)
        self.screen.blit(ts, (bx + 12, by + 40))
        
        # File list
        list_y = by + 60
        list_h = bh - 110
        visible = list_h // 22
        
        pygame.draw.rect(self.screen, BG_DARK, (bx + 8, list_y, bw - 16, list_h), border_radius=4)
        
        for i in range(visible):
            idx = self.scroll + i
            if idx >= len(self.files):
                break
            
            name, is_dir = self.files[idx]
            iy = list_y + 4 + i * 22
            
            # Highlight selected
            if idx == self.selected:
                pygame.draw.rect(self.screen, ACCENT, (bx + 10, iy, bw - 20, 20), border_radius=3)
                fg = BG_DARK
            else:
                fg = TEXT
            
            # Icon and name
            icon = "[DIR] " if is_dir else "      "
            display = icon + name
            if len(display) > 50:
                display = display[:47] + "..."
            ts, _ = self.font.render(display, fg)
            self.screen.blit(ts, (bx + 16, iy + 3))
        
        # Scrollbar
        if len(self.files) > visible:
            sb_h = max(20, list_h * visible // len(self.files))
            sb_y = list_y + (list_h - sb_h) * self.scroll // max(1, len(self.files) - visible)
            pygame.draw.rect(self.screen, BG_LIGHT, (bx + bw - 20, sb_y, 8, sb_h), border_radius=4)
        
        # Buttons
        btn_y = by + bh - 40
        
        # Cancel button
        cancel_rect = pygame.Rect(bx + bw - 170, btn_y, 70, 28)
        pygame.draw.rect(self.screen, BG_LIGHT, cancel_rect, border_radius=4)
        ts, tr = self.font.render("Cancel", TEXT)
        self.screen.blit(ts, (cancel_rect.centerx - tr.width//2, cancel_rect.centery - tr.height//2))
        
        # Open button
        open_rect = pygame.Rect(bx + bw - 90, btn_y, 70, 28)
        pygame.draw.rect(self.screen, ACCENT, open_rect, border_radius=4)
        ts, tr = self.font.render("Open", BG_DARK)
        self.screen.blit(ts, (open_rect.centerx - tr.width//2, open_rect.centery - tr.height//2))
        
        # Instructions
        ts, _ = self.font.render("↑↓:Select  Enter:Open  Esc:Cancel", TEXT_DIM)
        self.screen.blit(ts, (bx + 12, btn_y + 6))
        
        # Store button rects for click handling
        self._cancel_rect = cancel_rect
        self._open_rect = open_rect
        self._list_rect = pygame.Rect(bx + 8, list_y, bw - 16, list_h)
        self._visible = visible
    
    def handle(self, ev) -> Optional[str]:
        """Handle events. Returns file path if selected, None otherwise."""
        if not self.active:
            return None
        
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                self.close()
            elif ev.key == pygame.K_UP:
                self.selected = max(0, self.selected - 1)
                if self.selected < self.scroll:
                    self.scroll = self.selected
            elif ev.key == pygame.K_DOWN:
                self.selected = min(len(self.files) - 1, self.selected + 1)
                if self.selected >= self.scroll + self._visible:
                    self.scroll = self.selected - self._visible + 1
            elif ev.key == pygame.K_RETURN:
                return self._select_current()
            elif ev.key == pygame.K_BACKSPACE:
                # Go up one directory
                self.path = os.path.dirname(self.path)
                self._refresh()
        
        elif ev.type == pygame.MOUSEBUTTONDOWN:
            if ev.button == 1:
                # Cancel button
                if hasattr(self, '_cancel_rect') and self._cancel_rect.collidepoint(ev.pos):
                    self.close()
                # Open button
                elif hasattr(self, '_open_rect') and self._open_rect.collidepoint(ev.pos):
                    return self._select_current()
                # File list click
                elif hasattr(self, '_list_rect') and self._list_rect.collidepoint(ev.pos):
                    rel_y = ev.pos[1] - self._list_rect.y - 4
                    idx = self.scroll + rel_y // 22
                    if 0 <= idx < len(self.files):
                        if idx == self.selected:
                            # Double-click effect
                            return self._select_current()
                        self.selected = idx
            
            # Scroll
            elif ev.button == 4:
                self.scroll = max(0, self.scroll - 3)
            elif ev.button == 5:
                max_scroll = max(0, len(self.files) - self._visible)
                self.scroll = min(max_scroll, self.scroll + 3)
        
        return None
    
    def _select_current(self) -> Optional[str]:
        """Select the current item."""
        if not self.files:
            return None
        
        name, is_dir = self.files[self.selected]
        
        if name == '..':
            self.path = os.path.dirname(self.path)
            self._refresh()
            return None
        
        full_path = os.path.join(self.path, name)
        
        if is_dir:
            self.path = full_path
            self._refresh()
            return None
        else:
            self.close()
            return full_path


# ============================================================================
# MESSAGE BOX (Pure pygame)
# ============================================================================

class MessageBox:
    """Pure pygame message box."""
    
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.active = False
        self.title = ""
        self.message = ""
    
    def show(self, title: str, message: str):
        """Show the message box."""
        self.title = title
        self.message = message
        self.active = True
    
    def draw(self):
        """Draw the message box."""
        if not self.active:
            return
        
        sw, sh = self.screen.get_size()
        
        # Darken background
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Calculate size based on message
        lines = self.message.split('\n')
        bw = max(300, max(len(line) * 8 for line in lines) + 40)
        bh = max(150, len(lines) * 18 + 90)
        bx, by = (sw - bw) // 2, (sh - bh) // 2
        
        # Box
        pygame.draw.rect(self.screen, BG_MED, (bx, by, bw, bh), border_radius=8)
        pygame.draw.rect(self.screen, BORDER, (bx, by, bw, bh), 2, border_radius=8)
        
        # Title
        pygame.draw.rect(self.screen, BG_LIGHT, (bx, by, bw, 30), border_radius=8)
        pygame.draw.rect(self.screen, BG_LIGHT, (bx, by + 15, bw, 15))
        ts, _ = self.font.render(self.title, TEXT)
        self.screen.blit(ts, (bx + 12, by + 7))
        
        # Message
        y = by + 45
        for line in lines:
            ts, _ = self.font.render(line, TEXT)
            self.screen.blit(ts, (bx + 15, y))
            y += 18
        
        # OK button
        btn_rect = pygame.Rect(bx + bw//2 - 40, by + bh - 40, 80, 28)
        pygame.draw.rect(self.screen, ACCENT, btn_rect, border_radius=4)
        ts, tr = self.font.render("OK", BG_DARK)
        self.screen.blit(ts, (btn_rect.centerx - tr.width//2, btn_rect.centery - tr.height//2))
        
        self._btn_rect = btn_rect
    
    def handle(self, ev) -> bool:
        """Handle events. Returns True if closed."""
        if not self.active:
            return False
        
        if ev.type == pygame.KEYDOWN:
            if ev.key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE):
                self.active = False
                return True
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if hasattr(self, '_btn_rect') and self._btn_rect.collidepoint(ev.pos):
                self.active = False
                return True
        
        return False


# ============================================================================
# SOUND
# ============================================================================

class Sound:
    def __init__(self):
        self.sound = None
        self.playing = False
        try:
            n = 4410
            samples = []
            for i in range(n):
                t = i / 44100
                env = min(1.0, i/80) * min(1.0, (n-i)/80)
                val = int(16000 * env * math.sin(2 * math.pi * 440 * t))
                samples.extend([val, val])
            self.sound = pygame.mixer.Sound(buffer=array.array('h', samples))
            self.sound.set_volume(0.2)
        except:
            pass

    def play(self):
        if self.sound and not self.playing:
            self.sound.play(-1)
            self.playing = True

    def stop(self):
        if self.sound and self.playing:
            self.sound.stop()
            self.playing = False


# ============================================================================
# CHIP-8 CPU
# ============================================================================

class CPU:
    def __init__(self):
        self.reset()

    def reset(self):
        self.mem = bytearray(MEMORY_SIZE)
        self.V = [0] * 16
        self.I = 0
        self.PC = PROGRAM_START
        self.stack = [0] * 16
        self.SP = 0
        self.DT = self.ST = 0
        self.hires = False
        self.gfx = [[0]*CHIP8_WIDTH for _ in range(CHIP8_HEIGHT)]
        self.gfx_hi = [[0]*SCHIP_WIDTH for _ in range(SCHIP_HEIGHT)]
        self.keys = [0] * 16
        self.wait_key = False
        self.wait_reg = 0
        self.draw_flag = True
        self.halted = False
        self.loaded = False
        self.rom_name = ""
        self.rom_path = ""
        self.cycles = 0
        self.rpl = [0] * 8
        self.mem[0:len(FONTSET)] = FONTSET
        self.mem[80:80+len(SCHIP_FONT)] = SCHIP_FONT

    def load(self, path: str) -> bool:
        try:
            with open(path, 'rb') as f:
                data = f.read()
            if len(data) > MEMORY_SIZE - PROGRAM_START:
                return False
            self.reset()
            self.mem[PROGRAM_START:PROGRAM_START+len(data)] = data
            self.loaded = True
            self.rom_name = os.path.basename(path)
            self.rom_path = path
            return True
        except:
            return False

    def load_bytes(self, data: bytes, name: str = "ROM"):
        if len(data) > MEMORY_SIZE - PROGRAM_START:
            return False
        self.reset()
        self.mem[PROGRAM_START:PROGRAM_START+len(data)] = data
        self.loaded = True
        self.rom_name = name
        return True

    def display(self):
        return self.gfx_hi if self.hires else self.gfx

    def size(self):
        return (SCHIP_WIDTH, SCHIP_HEIGHT) if self.hires else (CHIP8_WIDTH, CHIP8_HEIGHT)

    def step(self):
        if self.halted or self.wait_key:
            return
        op = (self.mem[self.PC] << 8) | self.mem[self.PC + 1]
        self._exec(op)
        self.cycles += 1

    def _exec(self, op):
        nnn, nn, n = op & 0xFFF, op & 0xFF, op & 0xF
        x, y, hi = (op >> 8) & 0xF, (op >> 4) & 0xF, (op >> 12) & 0xF

        if op == 0x00E0:
            g = self.gfx_hi if self.hires else self.gfx
            for r in g:
                for i in range(len(r)): r[i] = 0
            self.draw_flag = True
            self.PC += 2
        elif op == 0x00EE:
            self.SP -= 1
            self.PC = self.stack[self.SP] + 2
        elif op == 0x00FB:
            self._scroll_r()
            self.PC += 2
        elif op == 0x00FC:
            self._scroll_l()
            self.PC += 2
        elif op == 0x00FD:
            self.halted = True
        elif op == 0x00FE:
            self.hires = False
            self.PC += 2
        elif op == 0x00FF:
            self.hires = True
            self.PC += 2
        elif hi == 0 and (op & 0xF0) == 0xC0:
            self._scroll_d(n)
            self.PC += 2
        elif hi == 0:
            self.PC += 2
        elif hi == 1:
            self.PC = nnn
        elif hi == 2:
            self.stack[self.SP] = self.PC
            self.SP += 1
            self.PC = nnn
        elif hi == 3:
            self.PC += 4 if self.V[x] == nn else 2
        elif hi == 4:
            self.PC += 4 if self.V[x] != nn else 2
        elif hi == 5 and n == 0:
            self.PC += 4 if self.V[x] == self.V[y] else 2
        elif hi == 6:
            self.V[x] = nn
            self.PC += 2
        elif hi == 7:
            self.V[x] = (self.V[x] + nn) & 0xFF
            self.PC += 2
        elif hi == 8:
            self._alu(x, y, n)
            self.PC += 2
        elif hi == 9 and n == 0:
            self.PC += 4 if self.V[x] != self.V[y] else 2
        elif hi == 0xA:
            self.I = nnn
            self.PC += 2
        elif hi == 0xB:
            self.PC = nnn + self.V[0]
        elif hi == 0xC:
            self.V[x] = random.randint(0, 255) & nn
            self.PC += 2
        elif hi == 0xD:
            self._draw(x, y, n)
            self.PC += 2
        elif hi == 0xE:
            k = self.V[x] & 0xF
            if nn == 0x9E:
                self.PC += 4 if self.keys[k] else 2
            elif nn == 0xA1:
                self.PC += 4 if not self.keys[k] else 2
            else:
                self.PC += 2
        elif hi == 0xF:
            self._misc(x, nn)
        else:
            self.PC += 2

    def _alu(self, x, y, n):
        if n == 0: self.V[x] = self.V[y]
        elif n == 1: self.V[x] |= self.V[y]; self.V[0xF] = 0
        elif n == 2: self.V[x] &= self.V[y]; self.V[0xF] = 0
        elif n == 3: self.V[x] ^= self.V[y]; self.V[0xF] = 0
        elif n == 4:
            r = self.V[x] + self.V[y]
            self.V[x] = r & 0xFF
            self.V[0xF] = 1 if r > 255 else 0
        elif n == 5:
            f = 1 if self.V[x] >= self.V[y] else 0
            self.V[x] = (self.V[x] - self.V[y]) & 0xFF
            self.V[0xF] = f
        elif n == 6:
            f = self.V[x] & 1
            self.V[x] >>= 1
            self.V[0xF] = f
        elif n == 7:
            f = 1 if self.V[y] >= self.V[x] else 0
            self.V[x] = (self.V[y] - self.V[x]) & 0xFF
            self.V[0xF] = f
        elif n == 0xE:
            f = (self.V[x] >> 7) & 1
            self.V[x] = (self.V[x] << 1) & 0xFF
            self.V[0xF] = f

    def _misc(self, x, nn):
        if nn == 0x07: self.V[x] = self.DT
        elif nn == 0x0A:
            self.wait_key = True
            self.wait_reg = x
            return
        elif nn == 0x15: self.DT = self.V[x]
        elif nn == 0x18: self.ST = self.V[x]
        elif nn == 0x1E: self.I = (self.I + self.V[x]) & 0xFFFF
        elif nn == 0x29: self.I = (self.V[x] & 0xF) * 5
        elif nn == 0x30: self.I = 80 + (self.V[x] & 0xF) * 10
        elif nn == 0x33:
            v = self.V[x]
            self.mem[self.I] = v // 100
            self.mem[self.I+1] = (v // 10) % 10
            self.mem[self.I+2] = v % 10
        elif nn == 0x55:
            for i in range(x+1): self.mem[(self.I+i) & 0xFFF] = self.V[i]
        elif nn == 0x65:
            for i in range(x+1): self.V[i] = self.mem[(self.I+i) & 0xFFF]
        elif nn == 0x75:
            for i in range(min(x+1, 8)): self.rpl[i] = self.V[i]
        elif nn == 0x85:
            for i in range(min(x+1, 8)): self.V[i] = self.rpl[i]
        self.PC += 2

    def _draw(self, x, y, n):
        vx, vy = self.V[x], self.V[y]
        g = self.gfx_hi if self.hires else self.gfx
        w, h = self.size()
        if n == 0 and self.hires:
            self._draw16(vx, vy)
            return
        vx %= w
        vy %= h
        self.V[0xF] = 0
        for row in range(n):
            py = (vy + row) % h
            spr = self.mem[(self.I + row) & 0xFFF]
            for col in range(8):
                px = (vx + col) % w
                if (spr >> (7 - col)) & 1:
                    if g[py][px]: self.V[0xF] = 1
                    g[py][px] ^= 1
        self.draw_flag = True

    def _draw16(self, vx, vy):
        g = self.gfx_hi
        vx %= SCHIP_WIDTH
        vy %= SCHIP_HEIGHT
        self.V[0xF] = 0
        for row in range(16):
            py = (vy + row) % SCHIP_HEIGHT
            word = (self.mem[(self.I + row*2) & 0xFFF] << 8) | self.mem[(self.I + row*2 + 1) & 0xFFF]
            for col in range(16):
                px = (vx + col) % SCHIP_WIDTH
                if (word >> (15 - col)) & 1:
                    if g[py][px]: self.V[0xF] = 1
                    g[py][px] ^= 1
        self.draw_flag = True

    def _scroll_d(self, n):
        g = self.gfx_hi if self.hires else self.gfx
        h, w = len(g), len(g[0])
        for y in range(h-1, n-1, -1): g[y] = g[y-n][:]
        for y in range(n): g[y] = [0]*w
        self.draw_flag = True

    def _scroll_r(self):
        g = self.gfx_hi if self.hires else self.gfx
        w = len(g[0])
        for row in g:
            for x in range(w-1, 3, -1): row[x] = row[x-4]
            for x in range(4): row[x] = 0
        self.draw_flag = True

    def _scroll_l(self):
        g = self.gfx_hi if self.hires else self.gfx
        w = len(g[0])
        for row in g:
            for x in range(w-4): row[x] = row[x+4]
            for x in range(w-4, w): row[x] = 0
        self.draw_flag = True

    def tick_timers(self):
        if self.DT > 0: self.DT -= 1
        if self.ST > 0: self.ST -= 1

    def key_down(self, k):
        if 0 <= k < 16:
            self.keys[k] = 1
            if self.wait_key:
                self.V[self.wait_reg] = k
                self.wait_key = False
                self.PC += 2

    def key_up(self, k):
        if 0 <= k < 16:
            self.keys[k] = 0

    def state(self) -> dict:
        return {
            'mem': bytes(self.mem), 'V': self.V[:], 'I': self.I, 'PC': self.PC,
            'stack': self.stack[:], 'SP': self.SP, 'DT': self.DT, 'ST': self.ST,
            'hires': self.hires, 'gfx': [r[:] for r in self.gfx],
            'gfx_hi': [r[:] for r in self.gfx_hi], 'cycles': self.cycles,
        }

    def restore(self, s):
        self.mem = bytearray(s['mem'])
        self.V = s['V'][:]
        self.I, self.PC = s['I'], s['PC']
        self.stack, self.SP = s['stack'][:], s['SP']
        self.DT, self.ST = s['DT'], s['ST']
        self.hires = s['hires']
        self.gfx = [r[:] for r in s['gfx']]
        self.gfx_hi = [r[:] for r in s['gfx_hi']]
        self.cycles = s.get('cycles', 0)
        self.draw_flag = True

    def disasm(self, addr: int) -> str:
        if addr >= MEMORY_SIZE - 1: return "???"
        op = (self.mem[addr] << 8) | self.mem[addr + 1]
        nnn, nn, n = op & 0xFFF, op & 0xFF, op & 0xF
        x, y, hi = (op >> 8) & 0xF, (op >> 4) & 0xF, (op >> 12) & 0xF
        if op == 0x00E0: return "CLS"
        if op == 0x00EE: return "RET"
        if hi == 1: return f"JP {nnn:03X}"
        if hi == 2: return f"CALL {nnn:03X}"
        if hi == 3: return f"SE V{x:X},{nn:02X}"
        if hi == 4: return f"SNE V{x:X},{nn:02X}"
        if hi == 6: return f"LD V{x:X},{nn:02X}"
        if hi == 7: return f"ADD V{x:X},{nn:02X}"
        if hi == 8:
            ops = {0:'LD',1:'OR',2:'AND',3:'XOR',4:'ADD',5:'SUB',6:'SHR',7:'SUBN',0xE:'SHL'}
            return f"{ops.get(n,'?')} V{x:X},V{y:X}"
        if hi == 0xA: return f"LD I,{nnn:03X}"
        if hi == 0xC: return f"RND V{x:X},{nn:02X}"
        if hi == 0xD: return f"DRW V{x:X},V{y:X},{n}"
        return f"{op:04X}"


# ============================================================================
# GUI
# ============================================================================

class MenuSystem:
    """Fixed dropdown menu system."""
    
    def __init__(self, font):
        self.font = font
        self.menus: List[Tuple[str, pygame.Rect, List[Tuple[str, Callable, str]]]] = []
        self.active = -1
        self.hover_item = -1
        
    def add(self, title: str, items: List[Tuple[str, Callable, str]]):
        x = 8 + sum(m[1].width + 8 for m in self.menus)
        ts, tr = self.font.render(title, TEXT)
        rect = pygame.Rect(x, 0, tr.width + 16, MENUBAR_H)
        self.menus.append((title, rect, items))
    
    def draw(self, surf):
        # Menu bar background
        pygame.draw.rect(surf, BG_MED, (0, 0, WINDOW_WIDTH, MENUBAR_H))
        pygame.draw.line(surf, BORDER, (0, MENUBAR_H-1), (WINDOW_WIDTH, MENUBAR_H-1))
        
        mouse = pygame.mouse.get_pos()
        
        for i, (title, rect, items) in enumerate(self.menus):
            # Highlight on hover or active
            is_hover = rect.collidepoint(mouse) and mouse[1] < MENUBAR_H
            is_active = i == self.active
            
            if is_active:
                pygame.draw.rect(surf, BG_ACTIVE, rect)
            elif is_hover:
                pygame.draw.rect(surf, BG_HOVER, rect)
            
            ts, _ = self.font.render(title, TEXT)
            surf.blit(ts, (rect.x + 8, 5))
            
            # Draw dropdown
            if is_active:
                self._draw_dropdown(surf, rect.x, items, mouse)
    
    def _draw_dropdown(self, surf, x: int, items, mouse):
        item_h = 28
        pad = 4
        w = 200
        h = len(items) * item_h + pad * 2
        
        # Shadow
        shadow = pygame.Rect(x + 3, MENUBAR_H + 3, w, h)
        pygame.draw.rect(surf, (0, 0, 0), shadow, border_radius=4)
        
        # Background
        dropdown = pygame.Rect(x, MENUBAR_H, w, h)
        pygame.draw.rect(surf, BG_MED, dropdown, border_radius=4)
        pygame.draw.rect(surf, BORDER, dropdown, 1, border_radius=4)
        
        self.hover_item = -1
        
        for i, (text, cb, shortcut) in enumerate(items):
            iy = MENUBAR_H + pad + i * item_h
            item_rect = pygame.Rect(x + pad, iy, w - pad*2, item_h)
            
            if text == "-":
                # Separator
                pygame.draw.line(surf, BORDER, (x + 12, iy + item_h//2), (x + w - 12, iy + item_h//2))
                continue
            
            # Hover highlight
            if item_rect.collidepoint(mouse):
                self.hover_item = i
                pygame.draw.rect(surf, ACCENT, item_rect, border_radius=3)
                fg = BG_DARK
                fg2 = BG_MED
            else:
                fg = TEXT
                fg2 = TEXT_DIM
            
            # Text
            ts, _ = self.font.render(text, fg)
            surf.blit(ts, (x + 14, iy + 6))
            
            # Shortcut
            if shortcut:
                ss, sr = self.font.render(shortcut, fg2)
                surf.blit(ss, (x + w - sr.width - 14, iy + 6))
    
    def handle(self, ev) -> bool:
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            # Click on menu title?
            for i, (_, rect, _) in enumerate(self.menus):
                if rect.collidepoint(ev.pos):
                    self.active = i if self.active != i else -1
                    return True
            
            # Click on dropdown item?
            if self.active >= 0:
                _, rect, items = self.menus[self.active]
                x = rect.x
                item_h = 28
                pad = 4
                
                for i, (text, cb, _) in enumerate(items):
                    if text == "-":
                        continue
                    iy = MENUBAR_H + pad + i * item_h
                    item_rect = pygame.Rect(x + pad, iy, 200 - pad*2, item_h)
                    if item_rect.collidepoint(ev.pos):
                        self.active = -1
                        if cb:
                            cb()
                        return True
                
                # Click outside = close
                self.active = -1
                return True
        
        elif ev.type == pygame.MOUSEMOTION:
            # Switch menus on hover when one is open
            if self.active >= 0:
                for i, (_, rect, _) in enumerate(self.menus):
                    if rect.collidepoint(ev.pos) and ev.pos[1] < MENUBAR_H:
                        self.active = i
                        return True
        
        return False
    
    def close(self):
        self.active = -1


class Toolbar:
    def __init__(self, font):
        self.font = font
        self.buttons: List[Tuple[str, pygame.Rect, Callable, bool]] = []
        self.x = 8
    
    def add(self, text: str, cb: Callable, w: int = 60):
        rect = pygame.Rect(self.x, MENUBAR_H + 4, w, 32)
        self.buttons.append((text, rect, cb, True))
        self.x += w + 6
    
    def sep(self):
        self.x += 10
    
    def draw(self, surf):
        pygame.draw.rect(surf, BG_MED, (0, MENUBAR_H, WINDOW_WIDTH, TOOLBAR_H))
        pygame.draw.line(surf, BORDER, (0, MENUBAR_H + TOOLBAR_H - 1), (WINDOW_WIDTH, MENUBAR_H + TOOLBAR_H - 1))
        
        mouse = pygame.mouse.get_pos()
        
        for text, rect, cb, enabled in self.buttons:
            hover = rect.collidepoint(mouse)
            
            if hover and enabled:
                bg = BG_HOVER
            else:
                bg = BG_LIGHT
            
            pygame.draw.rect(surf, bg, rect, border_radius=4)
            pygame.draw.rect(surf, BORDER, rect, 1, border_radius=4)
            
            ts, tr = self.font.render(text, TEXT if enabled else TEXT_DIM)
            surf.blit(ts, (rect.centerx - tr.width//2, rect.centery - tr.height//2))
    
    def handle(self, ev) -> bool:
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            for text, rect, cb, enabled in self.buttons:
                if rect.collidepoint(ev.pos) and enabled:
                    cb()
                    return True
        return False


class StatusBar:
    def __init__(self, font):
        self.font = font
        self.parts = {}
    
    def set(self, k, v):
        self.parts[k] = str(v)
    
    def draw(self, surf):
        y = WINDOW_HEIGHT - STATUSBAR_H
        pygame.draw.rect(surf, BG_MED, (0, y, WINDOW_WIDTH, STATUSBAR_H))
        pygame.draw.line(surf, BORDER, (0, y), (WINDOW_WIDTH, y))
        
        x = 12
        for k, v in self.parts.items():
            ts, tr = self.font.render(v, TEXT_DIM)
            surf.blit(ts, (x, y + 5))
            x += tr.width + 20


class DebugPanel:
    def __init__(self, font):
        self.font = font
        self.rect = pygame.Rect(DEBUG_X, DEBUG_Y, DEBUG_W, DEBUG_H)
        self.visible = True
        self.tab = 0
        self.mem_off = PROGRAM_START
    
    def draw(self, surf, cpu: CPU):
        if not self.visible:
            return
        
        # Background
        pygame.draw.rect(surf, BG_MED, self.rect, border_radius=6)
        pygame.draw.rect(surf, BORDER, self.rect, 1, border_radius=6)
        
        x, y = self.rect.x + 10, self.rect.y + 8
        
        # Title & tabs
        ts, _ = self.font.render("DEBUG", ACCENT)
        surf.blit(ts, (x, y))
        
        tabs = ["Regs", "Mem", "ASM"]
        tx = x + 70
        for i, t in enumerate(tabs):
            tw = 45
            tr = pygame.Rect(tx, y - 2, tw, 18)
            if i == self.tab:
                pygame.draw.rect(surf, BG_LIGHT, tr, border_radius=3)
            ts, _ = self.font.render(t, TEXT if i == self.tab else TEXT_DIM)
            surf.blit(ts, (tx + 6, y))
            tx += tw + 4
        
        y += 26
        
        if self.tab == 0:
            self._regs(surf, cpu, x, y)
        elif self.tab == 1:
            self._mem(surf, cpu, x, y)
        else:
            self._asm(surf, cpu, x, y)
    
    def _regs(self, surf, cpu, x, y):
        # V registers
        for i in range(16):
            col = YELLOW if i == 0xF else TEXT
            ts, _ = self.font.render(f"V{i:X}:{cpu.V[i]:02X}", col)
            surf.blit(ts, (x + (i % 4) * 60, y + (i // 4) * 16))
        y += 70
        
        # Special
        for i, (lbl, val, col) in enumerate([
            ("PC", f"{cpu.PC:04X}", GREEN),
            ("I", f"{cpu.I:04X}", GREEN),
            ("SP", f"{cpu.SP:X}", ACCENT),
            ("DT", f"{cpu.DT:02X}", YELLOW),
            ("ST", f"{cpu.ST:02X}", YELLOW),
        ]):
            ts, _ = self.font.render(f"{lbl}:{val}", col)
            surf.blit(ts, (x + (i % 3) * 78, y + (i // 3) * 18))
        y += 45
        
        # Current opcode
        if cpu.PC < MEMORY_SIZE - 1:
            op = (cpu.mem[cpu.PC] << 8) | cpu.mem[cpu.PC + 1]
            ts, _ = self.font.render(f"OP:{op:04X} = {cpu.disasm(cpu.PC)}", ACCENT)
            surf.blit(ts, (x, y))
        y += 22
        
        # Stack
        ts, _ = self.font.render("Stack:", TEXT_DIM)
        surf.blit(ts, (x, y))
        y += 16
        for i in range(min(cpu.SP, 4)):
            ts, _ = self.font.render(f"{i}:{cpu.stack[i]:04X}", TEXT)
            surf.blit(ts, (x + i * 70, y))
    
    def _mem(self, surf, cpu, x, y):
        lines = (self.rect.height - 50) // 14
        for i in range(lines):
            addr = self.mem_off + i * 8
            if addr >= MEMORY_SIZE: break
            col = ACCENT if addr <= cpu.PC < addr + 8 else TEXT_DIM
            ts, _ = self.font.render(f"{addr:04X}:", col)
            surf.blit(ts, (x, y + i * 14))
            hx = " ".join(f"{cpu.mem[addr+j]:02X}" for j in range(8) if addr+j < MEMORY_SIZE)
            ts, _ = self.font.render(hx, TEXT)
            surf.blit(ts, (x + 48, y + i * 14))
    
    def _asm(self, surf, cpu, x, y):
        lines = (self.rect.height - 50) // 15
        start = max(PROGRAM_START, cpu.PC - (lines // 2) * 2)
        for i in range(lines):
            addr = start + i * 2
            if addr >= MEMORY_SIZE - 1: break
            cur = addr == cpu.PC
            if cur:
                pygame.draw.rect(surf, BG_LIGHT, (x - 4, y + i * 15 - 1, self.rect.width - 12, 15))
            ts, _ = self.font.render(f"{addr:04X}", GREEN if cur else TEXT_DIM)
            surf.blit(ts, (x, y + i * 15))
            op = (cpu.mem[addr] << 8) | cpu.mem[addr + 1]
            ts, _ = self.font.render(f"{op:04X}", YELLOW if cur else TEXT)
            surf.blit(ts, (x + 45, y + i * 15))
            ts, _ = self.font.render(cpu.disasm(addr), ACCENT if cur else TEXT)
            surf.blit(ts, (x + 95, y + i * 15))
    
    def handle(self, ev) -> bool:
        if not self.visible:
            return False
        if ev.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(ev.pos):
            # Tab click
            if ev.pos[1] < self.rect.y + 28:
                tx = self.rect.x + 80
                for i in range(3):
                    if tx <= ev.pos[0] < tx + 45:
                        self.tab = i
                        return True
                    tx += 49
            # Scroll
            if self.tab == 1:
                if ev.button == 4: self.mem_off = max(0, self.mem_off - 8)
                elif ev.button == 5: self.mem_off = min(MEMORY_SIZE - 64, self.mem_off + 8)
                return True
        return False


# ============================================================================
# MAIN EMULATOR
# ============================================================================

class Emulator:
    def __init__(self):
        pygame.init()
        pygame.mixer.init(44100, -16, 2, 512)
        pygame.freetype.init()
        
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Cat's CHIP8 EMU - Project 64 0.1")
        
        # Fonts
        self.font = pygame.freetype.SysFont("Consolas,Monaco,monospace", 12)
        self.font_lg = pygame.freetype.SysFont("Arial,Helvetica", 13, bold=True)
        
        # Core
        self.cpu = CPU()
        self.sound = Sound()
        self.clock = pygame.time.Clock()
        
        # State
        self.running = True
        self.paused = True
        self.speed = 12
        self.fps = 0
        self.frames = 0
        self.last_sec = time.time()
        self.timer_acc = 0.0
        self.saves = {}
        self.pix_on = PIX_ON
        self.pix_off = PIX_OFF
        self.drag_hover = False
        
        # GUI
        self.menu = MenuSystem(self.font)
        self.menu.add("File", [
            ("Open ROM...", self._open, "Ctrl+O"),
            ("Close ROM", self._close, ""),
            ("-", None, ""),
            ("Save State", self._save, "F5"),
            ("Load State", self._load, "F6"),
            ("-", None, ""),
            ("Exit", self._quit, "Esc"),
        ])
        self.menu.add("Emulation", [
            ("Run", self._run, "F2"),
            ("Pause", self._pause, "F3"),
            ("Reset", self._reset, "F4"),
            ("-", None, ""),
            ("Step", self._step, "F10"),
        ])
        self.menu.add("Options", [
            ("Speed: Slow (6)", lambda: self._set_speed(6), ""),
            ("Speed: Normal (12)", lambda: self._set_speed(12), ""),
            ("Speed: Fast (24)", lambda: self._set_speed(24), ""),
            ("Speed: Turbo (50)", lambda: self._set_speed(50), ""),
            ("-", None, ""),
            ("Color: Green", lambda: self._colors((45,255,120), (8,10,14)), ""),
            ("Color: Amber", lambda: self._colors((255,176,0), (18,10,0)), ""),
            ("Color: White", lambda: self._colors((255,255,255), (0,0,0)), ""),
            ("Color: Blue", lambda: self._colors((90,170,255), (4,8,18)), ""),
        ])
        self.menu.add("Debug", [
            ("Toggle Panel", self._toggle_debug, "F12"),
            ("-", None, ""),
            ("Dump Regs", self._dump, ""),
        ])
        self.menu.add("Help", [
            ("Controls...", self._controls, "F1"),
            ("About...", self._about, ""),
        ])
        
        self.toolbar = Toolbar(self.font)
        self.toolbar.add("Open", self._open, 55)
        self.toolbar.add("Run", self._run, 45)
        self.toolbar.add("Pause", self._pause, 55)
        self.toolbar.add("Reset", self._reset, 55)
        self.toolbar.add("Step", self._step, 50)
        self.toolbar.sep()
        self.toolbar.add("Save", self._save, 50)
        self.toolbar.add("Load", self._load, 50)
        
        self.status = StatusBar(self.font)
        self.status.set('s', 'Ready')
        self.status.set('r', 'No ROM - Drag & Drop to load')
        self.status.set('f', '0 FPS')
        
        self.debug = DebugPanel(self.font)
        self.debug.visible = False
        
        # Pure pygame dialogs (no tkinter!)
        self.file_browser = FileBrowser(self.screen, self.font)
        self.msg_box = MessageBox(self.screen, self.font)

    # Actions
    def _open(self):
        self.file_browser.open()
    
    def _load_rom(self, path: str):
        if self.cpu.load(path):
            self.paused = False
            self.status.set('r', self.cpu.rom_name)
            self.status.set('s', 'Running')
    
    def _close(self):
        self.cpu.reset()
        self.paused = True
        self.status.set('r', 'No ROM')
        self.status.set('s', 'Ready')
    
    def _run(self):
        if self.cpu.loaded:
            self.paused = False
            self.status.set('s', 'Running')
    
    def _pause(self):
        self.paused = True
        self.status.set('s', 'Paused')
    
    def _reset(self):
        path = self.cpu.rom_path
        if path and os.path.exists(path):
            self.cpu.load(path)
            self.status.set('s', 'Reset')
        else:
            self.cpu.reset()
    
    def _step(self):
        self.paused = True
        self.cpu.step()
        self.status.set('s', 'Step')
    
    def _save(self):
        if self.cpu.loaded:
            self.saves[0] = self.cpu.state()
            self.status.set('s', 'Saved')
    
    def _load(self):
        if 0 in self.saves:
            self.cpu.restore(self.saves[0])
            self.status.set('s', 'Loaded')
    
    def _set_speed(self, s):
        self.speed = s
        self.status.set('s', f'Speed: {s}')
    
    def _colors(self, on, off):
        self.pix_on = on
        self.pix_off = off
    
    def _toggle_debug(self):
        self.debug.visible = not self.debug.visible
    
    def _dump(self):
        print(f"\nPC:{self.cpu.PC:04X} I:{self.cpu.I:04X} SP:{self.cpu.SP}")
        print("V:", " ".join(f"{v:02X}" for v in self.cpu.V))
    
    def _controls(self):
        msg = """CHIP-8 KEYPAD -> KEYBOARD

1 2 3 C      1 2 3 4
4 5 6 D  ->  Q W E R
7 8 9 E      A S D F
A 0 B F      Z X C V

DRAG & DROP ROM files to load!

F1=Help F2=Run F3=Pause F4=Reset
F5=Save F6=Load F10=Step F12=Debug
Ctrl+O=Open  ESC=Quit"""
        self.msg_box.show("Controls", msg)
    
    def _about(self):
        msg = """Cat's CHIP8 EMU v0.1
Project 64 Style GUI

Complete Chip-8 & Super Chip-8 emulator.
Drag & Drop ROM files to play!

(c) 2025 Cat's Emulation Team"""
        self.msg_box.show("About", msg)
    
    def _quit(self):
        self.running = False

    # Main loop
    def _events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.running = False
                return
            
            # Message box has priority
            if self.msg_box.active:
                self.msg_box.handle(ev)
                continue
            
            # File browser has priority
            if self.file_browser.active:
                result = self.file_browser.handle(ev)
                if result:
                    self._load_rom(result)
                continue
            
            # Drag & Drop
            if ev.type == pygame.DROPFILE:
                path = ev.file
                if path.lower().endswith(('.ch8', '.c8', '.rom', '.bin')):
                    self._load_rom(path)
                self.drag_hover = False
            
            # Menu
            if self.menu.handle(ev):
                continue
            
            # Close menu on outside click
            if ev.type == pygame.MOUSEBUTTONDOWN:
                self.menu.close()
            
            # Toolbar
            if self.toolbar.handle(ev):
                continue
            
            # Debug
            if self.debug.handle(ev):
                continue
            
            # Keys
            if ev.type == pygame.KEYDOWN:
                m = pygame.key.get_mods()
                if ev.key == pygame.K_ESCAPE: self._quit()
                elif ev.key == pygame.K_F1: self._controls()
                elif ev.key == pygame.K_F2: self._run()
                elif ev.key == pygame.K_F3: self._pause()
                elif ev.key == pygame.K_F4: self._reset()
                elif ev.key == pygame.K_F5: self._save()
                elif ev.key == pygame.K_F6: self._load()
                elif ev.key == pygame.K_F10: self._step()
                elif ev.key == pygame.K_F12: self._toggle_debug()
                elif ev.key == pygame.K_o and m & pygame.KMOD_CTRL: self._open()
                elif ev.key in KEY_MAP: self.cpu.key_down(KEY_MAP[ev.key])
            elif ev.type == pygame.KEYUP:
                if ev.key in KEY_MAP: self.cpu.key_up(KEY_MAP[ev.key])

    def _update(self, dt):
        if self.paused or not self.cpu.loaded:
            return
        for _ in range(self.speed):
            self.cpu.step()
        self.timer_acc += dt
        while self.timer_acc >= 1000 / TIMER_HZ:
            self.cpu.tick_timers()
            self.timer_acc -= 1000 / TIMER_HZ
        if self.cpu.ST > 0:
            self.sound.play()
        else:
            self.sound.stop()

    def _render(self):
        self.screen.fill(BG_DARK)
        
        # Toolbar first (under menu)
        self.toolbar.draw(self.screen)
        
        # Display
        self._render_display()
        
        # HUD below display
        self._render_hud()
        
        # Debug panel
        self.debug.draw(self.screen, self.cpu)
        
        # Status bar
        self._update_status()
        self.status.draw(self.screen)
        
        # Menu bar last (on top)
        self.menu.draw(self.screen)
        
        # Dialogs on very top
        self.file_browser.draw()
        self.msg_box.draw()
        
        pygame.display.flip()

    def _render_display(self):
        # Border
        br = pygame.Rect(DISPLAY_X - 3, DISPLAY_Y - 3, DISPLAY_W + 6, DISPLAY_H + 6)
        pygame.draw.rect(self.screen, BORDER, br, 2, border_radius=4)
        
        # Background
        dr = pygame.Rect(DISPLAY_X, DISPLAY_Y, DISPLAY_W, DISPLAY_H)
        pygame.draw.rect(self.screen, self.pix_off, dr)
        
        # Pixels
        g = self.cpu.display()
        w, h = self.cpu.size()
        sx, sy = DISPLAY_W / w, DISPLAY_H / h
        
        for y in range(h):
            for x in range(w):
                if g[y][x]:
                    pr = pygame.Rect(
                        DISPLAY_X + int(x * sx),
                        DISPLAY_Y + int(y * sy),
                        int(sx) + 1,
                        int(sy) + 1
                    )
                    pygame.draw.rect(self.screen, self.pix_on, pr)
        
        # "No ROM" overlay
        if not self.cpu.loaded:
            overlay = pygame.Surface((DISPLAY_W, DISPLAY_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (DISPLAY_X, DISPLAY_Y))
            
            ts, tr = self.font_lg.render("Drag & Drop ROM here", TEXT)
            self.screen.blit(ts, (DISPLAY_X + DISPLAY_W//2 - tr.width//2, DISPLAY_Y + DISPLAY_H//2 - 20))
            ts, tr = self.font.render("or press Ctrl+O / File > Open", TEXT_DIM)
            self.screen.blit(ts, (DISPLAY_X + DISPLAY_W//2 - tr.width//2, DISPLAY_Y + DISPLAY_H//2 + 10))

    def _render_hud(self):
        x = DISPLAY_X
        y = DISPLAY_Y + DISPLAY_H + 12
        
        # Title
        title = f"Cat's CHIP8 EMU"
        if self.cpu.loaded:
            title += f" - {self.cpu.rom_name}"
        ts, _ = self.font_lg.render(title, TEXT)
        self.screen.blit(ts, (x, y))
        
        y += 22
        
        # Keypad hint
        ts, _ = self.font.render("Keys: 1234 QWER ASDF ZXCV = Chip-8 pad", TEXT_DIM)
        self.screen.blit(ts, (x, y))
        
        # Active keys
        pressed = [f"{k:X}" for k in range(16) if self.cpu.keys[k]]
        if pressed:
            ts, _ = self.font.render("Active: " + " ".join(pressed), GREEN)
            self.screen.blit(ts, (x + 300, y))
        
        y += 18
        
        # CPU info
        if self.cpu.loaded:
            info = f"PC:{self.cpu.PC:04X}  I:{self.cpu.I:04X}  Cycles:{self.cpu.cycles}"
            if self.paused:
                info += "  [PAUSED]"
            elif self.cpu.halted:
                info += "  [HALTED]"
            elif self.cpu.wait_key:
                info += "  [WAIT KEY]"
            ts, _ = self.font.render(info, ACCENT)
            self.screen.blit(ts, (x, y))

    def _update_status(self):
        self.frames += 1
        now = time.time()
        if now - self.last_sec >= 1.0:
            self.fps = self.frames
            self.frames = 0
            self.last_sec = now
        self.status.set('f', f'{self.fps} FPS')

    def run(self):
        print("""
╔═══════════════════════════════════════════════════╗
║        Cat's CHIP8 EMU - Project 64 0.1           ║
║     Complete Chip-8 Emulator with Full GUI        ║
╠═══════════════════════════════════════════════════╣
║  Drag & Drop ROM files onto the window to play!   ║
║  Press F1 for controls, Ctrl+O to browse files.   ║
╚═══════════════════════════════════════════════════╝
""")
        
        while self.running:
            dt = self.clock.tick(60)
            self._events()
            self._update(dt)
            self._render()
        
        self.sound.stop()
        pygame.quit()


# ============================================================================
# TEST ROM
# ============================================================================

def test_rom() -> bytes:
    return bytes([
        0x60, 0x08, 0x61, 0x04, 0xA2, 0x20, 0xD0, 0x18,
        0x60, 0x18, 0xD0, 0x18, 0x60, 0x28, 0xD0, 0x18,
        0x60, 0x38, 0xD0, 0x18,
        0xF0, 0x0A, 0x00, 0xE0, 0x12, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        # Cat sprite
        0b00100100,
        0b00100100,
        0b00000000,
        0b10000001,
        0b10100101,
        0b10011001,
        0b01000010,
        0b00111100,
    ])


# ============================================================================
# ENTRY
# ============================================================================

def main():
    import argparse
    p = argparse.ArgumentParser(description="Cat's CHIP8 EMU")
    p.add_argument('rom', nargs='?', help='ROM file')
    p.add_argument('--test', action='store_true', help='Load test ROM')
    p.add_argument('--debug', action='store_true', help='Show debug panel')
    p.add_argument('--speed', type=int, default=12, help='Cycles/frame')
    args = p.parse_args()
    
    emu = Emulator()
    emu.speed = args.speed
    emu.debug.visible = args.debug
    
    if args.test:
        emu.cpu.load_bytes(test_rom(), "Test ROM")
        emu.paused = False
        emu.status.set('r', 'Test ROM')
        emu.status.set('s', 'Running')
    elif args.rom:
        emu._load_rom(args.rom)
    
    emu.run()


if __name__ == '__main__':
    main()
