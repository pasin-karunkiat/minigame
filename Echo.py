import pygame
import random
import sys
import math
import struct

pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)

# --- การตั้งค่าหน้าจอ (ปรับขยายใหญ่ขึ้น) ---
WIDTH, HEIGHT = 1024, 720
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Eco Hero: Ultra Thai Edition")

# --- สี ---
WHITE, OFF_WHITE, BLACK = (255, 255, 255), (240, 240, 245), (15, 15, 25)
SHADOW = (0, 0, 0, 60)
SKY_TOP, SKY_BOTTOM = (10, 45, 60), (50, 120, 150)
GRASS_DEEP, GRASS_LIGHT, GOLD = (15, 45, 15), (40, 95, 40), (255, 215, 0)

# ถังขยะ
BIN_COLORS = {
    'organic': {'base': (76, 175, 80), 'light': (165, 214, 167), 'dark': (35, 90, 35), 'glow': (100, 255, 100), 'icon': (50, 120, 50)},
    'recycle': {'base': (255, 193, 7), 'light': (255, 235, 150), 'dark': (180, 130, 0), 'glow': (255, 255, 150), 'icon': (150, 110, 0)},
    'general': {'base': (33, 150, 243), 'light': (144, 202, 249), 'dark': (15, 80, 160), 'glow': (150, 200, 255), 'icon': (10, 60, 140)},
    'hazardous': {'base': (244, 67, 54), 'light': (239, 154, 154), 'dark': (183, 28, 28), 'glow': (255, 100, 100), 'icon': (130, 10, 10)}
}

# ขยะประเภทต่างๆ
TRASH_TYPES = [
    ("ขวดพลาสติก", "recycle", (200, 240, 255), "bottle"),
    ("กระป๋องโคล่า", "recycle", (220, 50, 50), "can"),
    ("แก้วน้ำเย็น", "recycle", (230, 245, 255, 150), "cup"), 
    ("แกนแอปเปิ้ล", "organic", (230, 80, 80), "food_waste"),
    ("ใบไม้แห้ง", "organic", (160, 100, 40), "leaf"),
    ("เปลือกกล้วย", "organic", (255, 220, 40), "banana"),
    ("ซองมันฝรั่ง", "general", (255, 140, 50), "bag"),
    ("กล่องโฟม", "general", (245, 245, 250), "foam"),
    ("ทิชชู่ยับๆ", "general", (220, 220, 220), "tissue"),
    ("ถ่านไฟฉาย", "hazardous", (50, 50, 50), "battery"),
    ("หลอดไฟ", "hazardous", (255, 255, 255), "lightbulb")
]

# --- ระบบเสียงสังเคราะห์ ---
def create_sound(frequency, duration, volume=0.1, type='sine'):
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    samples = []
    for i in range(n_samples):
        t = i / sample_rate
        if type == 'sine': val = math.sin(2.0 * math.pi * frequency * t)
        elif type == 'square': val = 1.0 if math.sin(2.0 * math.pi * frequency * t) > 0 else -1.0
        else: val = random.uniform(-1, 1)
        envelope = (n_samples - i) / n_samples
        samples.append(int(val * 32767 * volume * envelope))
    return pygame.mixer.Sound(buffer=struct.pack('<' + ('h' * len(samples)), *samples))

try: 
    snd_correct = create_sound(880, 0.3)
    snd_wrong = create_sound(110, 0.4, type='square')
    snd_drag = create_sound(660, 0.05, 0.02)
except: 
    snd_correct = snd_wrong = snd_drag = None

# --- ฟอนต์ระบบ ---
def get_thai_font(size):
    font_names = ['tahoma', 'leelawadee', 'thonburi', 'notosans']
    matched = pygame.font.match_font(','.join(font_names))
    return pygame.font.Font(matched, size) if matched else pygame.font.Font(None, size)

font_xl = get_thai_font(90)
font_lg = get_thai_font(55)
font_md = get_thai_font(32)
font_sm = get_thai_font(24)
font_tiny = get_thai_font(18)

# --- Helper Functions ---
def draw_text_with_shadow(surface, text, font, color, pos_center, shadow_offset=(2,2)):
    shadow_surf = font.render(text, True, SHADOW)
    surface.blit(shadow_surf, shadow_surf.get_rect(center=(pos_center[0]+shadow_offset[0], pos_center[1]+shadow_offset[1])))
    text_surf = font.render(text, True, color)
    surface.blit(text_surf, text_surf.get_rect(center=pos_center))

def draw_beveled_rect(surface, rect, color, radius=15, bevel=5):
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    hl = [min(c + 40, 255) for c in color]
    sh = [max(c - 40, 0) for c in color]
    pygame.draw.rect(surface, hl, (rect.x, rect.y, rect.width, bevel), border_top_left_radius=radius, border_top_right_radius=radius)
    pygame.draw.rect(surface, hl, (rect.x, rect.y, bevel, rect.height), border_top_left_radius=radius, border_bottom_left_radius=radius)
    pygame.draw.rect(surface, sh, (rect.x, rect.bottom-bevel, rect.width, bevel), border_bottom_left_radius=radius, border_bottom_right_radius=radius)
    pygame.draw.rect(surface, sh, (rect.right-bevel, rect.y, bevel, rect.height), border_top_right_radius=radius, border_bottom_right_radius=radius)
    pygame.draw.rect(surface, color, (rect.x+bevel, rect.y+bevel, rect.width-bevel*2, rect.height-bevel*2), border_radius=max(0, radius-bevel))

class Particle:
    def __init__(self, x, y, color):
        self.x, self.y, self.color = x, y, color
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(3, 8)
        self.vx, self.vy = math.cos(angle) * speed, math.sin(angle) * speed
        self.life, self.size = 255, random.randint(6, 12)
        
    def update(self):
        self.vx *= 0.95
        self.vy += 0.2
        self.x += self.vx
        self.y += self.vy
        self.life -= 8
        self.size *= 0.95
        
    def draw(self, surface):
        if self.life > 0 and self.size > 1:
            s = pygame.Surface((int(self.size*2), int(self.size*2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, self.life), (int(self.size), int(self.size)), int(self.size))
            surface.blit(s, (self.x-self.size, self.y-self.size))

class TrashItem:
    def __init__(self):
        self.angle = 0
        # ขยับตำแหน่งเกิดไอเทมลงมาให้สมดุลกับจอใหญ่
        self.base_y = 250
        self.rect = pygame.Rect(WIDTH//2 - 45, self.base_y, 90, 90)
        self.is_dragging = False

    def load_item(self, data):
        self.name, self.type, self.color, self.shape = data
        self.is_dragging = False
        self.rect.topleft = (WIDTH//2 - 45, self.base_y)
        self.model_surf = pygame.Surface((100, 100), pygame.SRCALPHA)
        self.draw_to_surface(self.model_surf, self.color)
        self.rot_speed = random.uniform(-2, 2)
        if abs(self.rot_speed) < 0.5: self.rot_speed = 1.5

    def draw_to_surface(self, surf, color):
        if self.shape == "bottle":
            pygame.draw.rect(surf, (30, 100, 200), (40, 10, 20, 12), border_radius=3)
            pygame.draw.rect(surf, color, (43, 22, 14, 15))
            pygame.draw.rect(surf, color, (32, 35, 36, 55), border_radius=10)
            pygame.draw.rect(surf, (255, 80, 80), (32, 50, 36, 20))
            pygame.draw.line(surf, (255, 255, 255), (38, 40), (38, 80), 3)
            
        elif self.shape == "can":
            pygame.draw.rect(surf, color, (30, 25, 40, 55), border_radius=5)
            pygame.draw.rect(surf, (180, 180, 180), (30, 20, 40, 8), border_radius=3)
            pygame.draw.rect(surf, (180, 180, 180), (30, 75, 40, 8), border_radius=3)
            pygame.draw.polygon(surf, (255, 255, 255), [(30, 45), (70, 35), (70, 50), (30, 60)])
            pygame.draw.line(surf, (255, 200, 200), (38, 30), (38, 70), 4)
            
        elif self.shape == "cup":
            pygame.draw.polygon(surf, color, [(30, 35), (70, 35), (60, 80), (40, 80)])
            pygame.draw.arc(surf, (200, 200, 200), (30, 15, 40, 40), 0, math.pi, 3)
            pygame.draw.line(surf, (220, 50, 50), (50, 35), (65, 5), 4)
            pygame.draw.circle(surf, (80, 180, 80), (50, 55), 10)
            
        elif self.shape == "food_waste":
            pygame.draw.rect(surf, (240, 230, 180), (42, 30, 16, 40), border_radius=8)
            pygame.draw.ellipse(surf, color, (30, 15, 40, 25))
            pygame.draw.ellipse(surf, color, (30, 60, 40, 25))
            pygame.draw.line(surf, (100, 50, 20), (50, 15), (55, 0), 3)
            pygame.draw.circle(surf, (50, 20, 10), (47, 45), 2)
            pygame.draw.circle(surf, (50, 20, 10), (53, 55), 2)
            
        elif self.shape == "banana":
            pygame.draw.polygon(surf, color, [(20, 25), (45, 75), (80, 85), (85, 70), (55, 55), (35, 15)])
            pygame.draw.polygon(surf, (120, 150, 50), [(20, 25), (35, 15), (25, 10), (15, 18)])
            pygame.draw.line(surf, (160, 120, 20), (35, 30), (55, 60), 2)
            pygame.draw.circle(surf, (139, 69, 19), (60, 70), 3)
            pygame.draw.circle(surf, (139, 69, 19), (45, 45), 2)
            
        elif self.shape == "leaf":
            pygame.draw.ellipse(surf, color, (20, 20, 60, 50))
            pygame.draw.line(surf, (90, 60, 20), (10, 45), (80, 45), 3)
            pygame.draw.line(surf, (90, 60, 20), (40, 45), (50, 30), 2)
            pygame.draw.line(surf, (90, 60, 20), (50, 45), (60, 60), 2)
            pygame.draw.line(surf, (90, 60, 20), (60, 45), (70, 35), 2)
            
        elif self.shape == "bag":
            for i in range(5):
                pygame.draw.polygon(surf, color, [(25+(i*10), 25), (30+(i*10), 20), (35+(i*10), 25)])
                pygame.draw.polygon(surf, color, [(25+(i*10), 75), (30+(i*10), 80), (35+(i*10), 75)])
            pygame.draw.rect(surf, color, (25, 25, 50, 50))
            pygame.draw.circle(surf, (255, 220, 50), (50, 50), 15)
            pygame.draw.line(surf, (255, 255, 255), (30, 30), (30, 70), 3)
            
        elif self.shape == "battery":
            pygame.draw.rect(surf, (40, 40, 40), (35, 25, 30, 50), border_radius=4)
            pygame.draw.rect(surf, (220, 180, 40), (35, 25, 30, 15), border_top_left_radius=4, border_top_right_radius=4)
            pygame.draw.rect(surf, (180, 180, 180), (45, 18, 10, 7))
            pygame.draw.rect(surf, (100, 100, 100), (38, 25, 5, 50))
            pygame.draw.line(surf, (0,0,0), (46, 32), (54, 32), 2)
            pygame.draw.line(surf, (0,0,0), (50, 28), (50, 36), 2)
            pygame.draw.line(surf, (255,255,255), (46, 60), (54, 60), 2)
            
        elif self.shape == "lightbulb":
            pygame.draw.circle(surf, color, (50, 40), 22)
            pygame.draw.line(surf, (255, 200, 0), (45, 40), (50, 30), 2)
            pygame.draw.line(surf, (255, 200, 0), (50, 30), (55, 40), 2)
            pygame.draw.line(surf, (100, 100, 100), (45, 40), (45, 55), 2)
            pygame.draw.line(surf, (100, 100, 100), (55, 40), (55, 55), 2)
            pygame.draw.rect(surf, (160, 160, 160), (40, 58, 20, 18), border_radius=3)
            pygame.draw.line(surf, (100, 100, 100), (40, 62), (60, 62), 2)
            pygame.draw.line(surf, (100, 100, 100), (40, 68), (60, 68), 2)
            pygame.draw.rect(surf, (50, 50, 50), (45, 76, 10, 6), border_radius=2)
            pygame.draw.arc(surf, (255, 255, 255), (32, 22, 36, 36), 1.5, 3.0, 3)
            
        else: 
            pts = [(25, 30), (48, 22), (73, 33), (80, 65), (52, 78), (22, 68)]
            pygame.draw.polygon(surf, color, pts)
            pygame.draw.line(surf, (180, 180, 180), (25, 30), (52, 50), 2)
            pygame.draw.line(surf, (180, 180, 180), (48, 22), (52, 50), 2)
            pygame.draw.line(surf, (180, 180, 180), (73, 33), (52, 50), 2)
            pygame.draw.line(surf, (180, 180, 180), (80, 65), (52, 50), 2)

    def draw(self, surface, paused=False):
        if not paused:
            if not self.is_dragging:
                self.rect.y = self.base_y + math.sin(pygame.time.get_ticks() * 0.004) * 15
                self.angle = (self.angle + self.rot_speed) % 360
            else:
                glow = pygame.Surface((150, 150), pygame.SRCALPHA)
                pygame.draw.circle(glow, (255,255,200,50), (75,75), 60)
                surface.blit(glow, (self.rect.centerx-75, self.rect.centery-75))
                self.angle = (self.angle + self.rot_speed * 3) % 360

        pygame.draw.ellipse(surface, (0,0,0,40), (self.rect.x+15, self.base_y + 90, 60, 15))
        rotated_image = pygame.transform.rotate(self.model_surf, self.angle)
        new_rect = rotated_image.get_rect(center=self.rect.center)
        surface.blit(rotated_image, new_rect.topleft)
        lbl_y = new_rect.top - 15 if not self.is_dragging else self.rect.y - 30
        draw_text_with_shadow(surface, self.name, font_sm, WHITE, (self.rect.centerx, lbl_y))

# Cache จำภาพคิวล่วงหน้า
PREVIEW_CACHE = {}
def get_preview_surf(data):
    cache_key = (data[3], data[2]) 
    if cache_key not in PREVIEW_CACHE:
        surf = pygame.Surface((100, 100), pygame.SRCALPHA)
        dummy = TrashItem()
        dummy.shape = data[3]
        dummy.draw_to_surface(surf, data[2])
        PREVIEW_CACHE[cache_key] = pygame.transform.scale(surf, (45, 45))
    return PREVIEW_CACHE[cache_key]

class Bin:
    def __init__(self, x, y, type_key, name):
        self.rect = pygame.Rect(x, y, 170, 220)
        self.type = type_key
        self.name = name
        self.colors = BIN_COLORS[type_key]
        self.lid_offset = 0

    def draw(self, surface, hover=False, paused=False):
        target_offset = -15 if hover and not paused else 0
        if not paused: 
            self.lid_offset += (target_offset - self.lid_offset) * 0.2

        if hover and not paused:
            glow = pygame.Surface((220, 270), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*self.colors['glow'], 60), (0,0,220,270), border_radius=30)
            surface.blit(glow, (self.rect.x-25, self.rect.y-25 + self.lid_offset))

        draw_beveled_rect(surface, pygame.Rect(self.rect.x, self.rect.y + 40, 170, 180), self.colors['dark'], radius=15, bevel=6)
        front_rect = pygame.Rect(self.rect.x+15, self.rect.y + 70, 140, 130)
        draw_beveled_rect(surface, front_rect, self.colors['base'], radius=10, bevel=4)
        lid_rect = pygame.Rect(self.rect.x-5, self.rect.y + self.lid_offset, 180, 45)
        draw_beveled_rect(surface, lid_rect, self.colors['dark'], radius=10, bevel=5)
        pygame.draw.rect(surface, self.colors['base'], (self.rect.centerx-25, lid_rect.y+5, 50, 10), border_radius=5)

        ic_col, ic_x, ic_y = self.colors['icon'], front_rect.centerx, front_rect.centery - 15
        if self.type == 'organic': 
            pygame.draw.circle(surface, ic_col, (ic_x-8, ic_y), 12)
            pygame.draw.circle(surface, ic_col, (ic_x+8, ic_y), 12)
            pygame.draw.polygon(surface, ic_col, [(ic_x-18, ic_y+5), (ic_x+18, ic_y+5), (ic_x, ic_y+25)])
        elif self.type == 'recycle': 
            pygame.draw.arc(surface, ic_col, (ic_x-15, ic_y-15, 30, 30), 0, math.pi*1.5, 5)
            pygame.draw.polygon(surface, ic_col, [(ic_x+15, ic_y), (ic_x+5, ic_y-10), (ic_x+25, ic_y-10)])
        elif self.type == 'general': 
            pygame.draw.rect(surface, ic_col, (ic_x-12, ic_y-5, 24, 30))
            pygame.draw.rect(surface, ic_col, (ic_x-15, ic_y-10, 30, 5))
        elif self.type == 'hazardous':
             pygame.draw.line(surface, ic_col, (ic_x-15, ic_y-10), (ic_x+15, ic_y+15), 4)
             pygame.draw.line(surface, ic_col, (ic_x-15, ic_y+15), (ic_x+15, ic_y-10), 4)
             pygame.draw.circle(surface, ic_col, (ic_x, ic_y-5), 10)
             pygame.draw.rect(surface, ic_col, (ic_x-6, ic_y+2, 12, 6))

        draw_text_with_shadow(surface, self.name, font_md, WHITE, (self.rect.centerx, self.rect.bottom - 30))

def draw_bg(surface, clouds, shift_x, paused=False):
    for y in range(HEIGHT):
        r = SKY_TOP[0] + (SKY_BOTTOM[0] - SKY_TOP[0]) * (y / HEIGHT)
        g = SKY_TOP[1] + (SKY_BOTTOM[1] - SKY_TOP[1]) * (y / HEIGHT)
        b = SKY_TOP[2] + (SKY_BOTTOM[2] - SKY_TOP[2]) * (y / HEIGHT)
        pygame.draw.line(surface, (int(r), int(g), int(b)), (0, y), (WIDTH, y))
    
    pygame.draw.ellipse(surface, (40, 90, 110), (-100 + shift_x*0.2, HEIGHT-220, WIDTH+200, 180))
    pygame.draw.ellipse(surface, (50, 100, 120), (200 + shift_x*0.1, HEIGHT-190, WIDTH+200, 150))
    for c in clouds:
        if not paused: c.x += 0.3
        if c.x > WIDTH + 100: c.x = -200
        pygame.draw.circle(surface, (255,255,255,180), (int(c.x), c.y), 40)
        pygame.draw.circle(surface, (255,255,255,180), (int(c.x)+35, c.y-10), 50)
        pygame.draw.circle(surface, (255,255,255,180), (int(c.x)-35, c.y+5), 35)
    
    pygame.draw.rect(surface, GRASS_DEEP, (0, HEIGHT-120, WIDTH, 120))
    pygame.draw.rect(surface, GRASS_LIGHT, (0, HEIGHT-135, WIDTH, 30), border_radius=15)

def main():
    clock = pygame.time.Clock()
    score, time_left, game_state = 0, 60.0, "START"
    clouds = [type('Cloud', (), {'x': random.randint(0, WIDTH), 'y': random.randint(50, 150)})() for _ in range(7)]
    
    # วางถัง 4 ใบให้กระจายพอดีหน้าจอ 1024px (ตั้ง y ต่ำลงเพื่อให้บาลานซ์)
    bins = [Bin(75, 480, "organic", "ขยะเปียก"), 
            Bin(310, 480, "recycle", "รีไซเคิล"), 
            Bin(545, 480, "general", "ทั่วไป"), 
            Bin(780, 480, "hazardous", "อันตราย")]
    
    trash, particles, upcoming_trash, bg_shift = TrashItem(), [], [], 0
    
    # ปุ่มหน้าเริ่มเกม (จัดตำแหน่งใหม่)
    btn_start = pygame.Rect(WIDTH//2-130, 400, 260, 70)
    btn_knowledge = pygame.Rect(WIDTH//2-130, 490, 260, 70)
    btn_back = pygame.Rect(80, 30, 120, 45)
    btn_pause = pygame.Rect(15, 10, 50, 50)
    
    # ปุ่มหน้าหยุดเกม
    btn_resume = pygame.Rect(WIDTH//2-125, 280, 250, 60)
    btn_restart = pygame.Rect(WIDTH//2-125, 360, 250, 60)
    btn_exit = pygame.Rect(WIDTH//2-125, 440, 250, 60)

    while True:
        mx, my = pygame.mouse.get_pos()
        if game_state == "PLAYING": bg_shift -= 0.5 

        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                pygame.quit()
                sys.exit()
            
            if game_state == "START":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if btn_start.collidepoint(event.pos): 
                        game_state, time_left, score = "PLAYING", 60, 0
                        upcoming_trash = [random.choice(TRASH_TYPES) for _ in range(3)]
                        trash.load_item(upcoming_trash.pop(0))
                        upcoming_trash.append(random.choice(TRASH_TYPES))
                    if btn_knowledge.collidepoint(event.pos): 
                        game_state = "KNOWLEDGE"
            
            elif game_state == "KNOWLEDGE":
                if event.type == pygame.MOUSEBUTTONDOWN and btn_back.collidepoint(event.pos): 
                    game_state = "START"
            
            elif game_state == "PLAYING":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if btn_pause.collidepoint(event.pos): 
                        game_state = "PAUSED"
                    elif trash.rect.collidepoint(event.pos):
                        trash.is_dragging = True
                        off_x, off_y = trash.rect.x - mx, trash.rect.y - my
                        if snd_drag: snd_drag.play()
                
       # --- นำโค้ดชุดนี้ไปวางแทนที่ ---
                elif event.type == pygame.MOUSEBUTTONUP and trash.is_dragging:
                    trash.is_dragging = False
                    found = False
                    for b in bins:
                        if b.rect.colliderect(trash.rect):
                            if b.type == trash.type:
                                score += 20
                                if snd_correct: snd_correct.play()
                                for _ in range(25): particles.append(Particle(trash.rect.centerx, trash.rect.centery, b.colors['light']))
                                trash.load_item(upcoming_trash.pop(0))
                                upcoming_trash.append(random.choice(TRASH_TYPES))
                            else:
                                time_left -= 8
                                trash.rect.topleft = (WIDTH//2 - 45, trash.base_y) 
                                if snd_wrong: snd_wrong.play()
                            found = True
                            break
                    if not found: 
                        trash.rect.topleft = (WIDTH//2 - 45, trash.base_y)
                
                elif event.type == pygame.MOUSEMOTION and trash.is_dragging:
                    trash.rect.x, trash.rect.y = mx + off_x, my + off_y
                    
            elif game_state == "PAUSED":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if btn_resume.collidepoint(event.pos): 
                        game_state = "PLAYING"
                    elif btn_restart.collidepoint(event.pos):
                        score, time_left, game_state = 0, 60, "PLAYING"
                        upcoming_trash = [random.choice(TRASH_TYPES) for _ in range(3)]
                        trash.load_item(upcoming_trash.pop(0))
                        upcoming_trash.append(random.choice(TRASH_TYPES))
                    elif btn_exit.collidepoint(event.pos): 
                        game_state = "START"
            
            elif game_state == "GAMEOVER":
                if event.type == pygame.MOUSEBUTTONDOWN: 
                    game_state = "START"

        # --- DRAWING ---
        is_paused = (game_state == "PAUSED")
        draw_bg(SCREEN, clouds, bg_shift, paused=is_paused)
        
        if game_state == "START":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0,10,30,180))
            SCREEN.blit(overlay, (0,0))
            draw_text_with_shadow(SCREEN, "ฮีโร่รักษ์โลก", font_xl, GOLD, (WIDTH//2, 220), (5,5))
            draw_beveled_rect(SCREEN, btn_start, (46, 180, 80) if btn_start.collidepoint(mx,my) else (36, 140, 60), 25)
            draw_text_with_shadow(SCREEN, "เริ่มภารกิจ", font_lg, WHITE, btn_start.center)
            draw_beveled_rect(SCREEN, btn_knowledge, (30, 120, 220) if btn_knowledge.collidepoint(mx,my) else (20, 90, 180), 25)
            draw_text_with_shadow(SCREEN, "ศูนย์การเรียนรู้", font_lg, WHITE, btn_knowledge.center)
            
        elif game_state == "KNOWLEDGE":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0,15,40,230))
            SCREEN.blit(overlay, (0,0))
            
            # --- ปรับปรุงหน้าต่าง Knowledge UI ใหม่ ---
            panel = pygame.Rect(80, 100, 864, 568) # ขยาย Panel
            draw_beveled_rect(SCREEN, panel, (245, 250, 255), 35, 8)
            draw_text_with_shadow(SCREEN, "ศูนย์การเรียนรู้เรื่องขยะ", font_lg, (20, 50, 100), (WIDTH//2, 150))
            
            btn_back.topleft = (100, 120)
            draw_beveled_rect(SCREEN, btn_back, (220, 60, 60) if btn_back.collidepoint(mx,my) else (180, 50, 50), 10)
            draw_text_with_shadow(SCREEN, "ย้อนกลับ", font_sm, WHITE, btn_back.center)

         # --- นำโค้ดชุดนี้ไปวางแทนที่ ---
            k_data = [
                {"type": "organic", "title": "ขยะเปียก (Organic)", "info": "เศษอาหาร, กล้วย, ใบไม้", "use": ["นำไปทำปุ๋ยหมัก", "หรือก๊าซชีวภาพ"]},
                {"type": "recycle", "title": "รีไซเคิล (Recycle)", "info": "ขวดพลาสติก, กระป๋องแก้ว", "use": ["นำไปแปรรูปเพื่อ", "นำกลับมาใช้ใหม่"]},
                {"type": "general", "title": "ทั่วไป (General)", "info": "ถุงพลาสติก, โฟม, ทิชชู่", "use": ["ฝังกลบหรือกำจัด", "อย่างถูกวิธี"]},
                {"type": "hazardous", "title": "อันตราย (Hazardous)", "info": "ถ่านไฟฉาย,หลอดไฟ", "use": ["คัดแยกเพื่อป้องกัน", "สารพิษรั่วไหล"]}
            ]
            
            for i, d in enumerate(k_data):
                col, row = i % 2, i // 2
                x, y = 112 + (col * 420), 220 + (row * 210)
                c_rect = pygame.Rect(x, y, 380, 180) 
                color = BIN_COLORS[d['type']]
                
                pygame.draw.rect(SCREEN, WHITE, c_rect, border_radius=15)
                pygame.draw.rect(SCREEN, color['base'], c_rect, 4, border_radius=15)
                pygame.draw.rect(SCREEN, color['base'], (x, y, 380, 45), border_top_left_radius=15, border_top_right_radius=15)
                draw_text_with_shadow(SCREEN, d['title'], font_md, WHITE, (x + 190, y + 22), (1,1))
                
                SCREEN.blit(font_sm.render(f"ตัวอย่าง:", True, (100,100,100)), (x + 20, y + 65))
                SCREEN.blit(font_sm.render(d['info'], True, BLACK), (x + 110, y + 65))
                
                SCREEN.blit(font_sm.render(f"วิธีจัดการ:", True, (100,100,100)), (x + 20, y + 105))
                
                for line_idx, line_text in enumerate(d['use']):
                    SCREEN.blit(font_sm.render(line_text, True, BLACK), (x + 110, y + 105 + (line_idx * 28)))

        elif game_state in ["PLAYING", "PAUSED"]:
            for b in bins: 
                b.draw(SCREEN, b.rect.colliderect(trash.rect), paused=is_paused)
            for p in particles[:]:
                if not is_paused: p.update()
                if p.life <= 0: particles.remove(p)
                else: p.draw(SCREEN)
            trash.draw(SCREEN, paused=is_paused)
            
            ui_rect = pygame.Rect(0,0,WIDTH,70)
            pygame.draw.rect(SCREEN, (0,0,0, 150), ui_rect)
            pygame.draw.line(SCREEN, GOLD, (0,70), (WIDTH,70), 3)
            
            draw_beveled_rect(SCREEN, btn_pause, (200, 60, 60) if btn_pause.collidepoint(mx,my) else (150, 40, 40), 10)
            pygame.draw.rect(SCREEN, WHITE, (btn_pause.x + 15, btn_pause.y + 12, 6, 26))
            pygame.draw.rect(SCREEN, WHITE, (btn_pause.x + 29, btn_pause.y + 12, 6, 26))
            
            draw_text_with_shadow(SCREEN, f"คะแนน: {score}", font_md, GOLD, (160, 35))
            time_col = WHITE if time_left > 10 else (255, 50, 50)
            draw_text_with_shadow(SCREEN, f"เวลา: {int(max(0, time_left))}", font_md, time_col, (WIDTH//2 - 20, 35))
            
            draw_text_with_shadow(SCREEN, "ถัดไป:", font_sm, WHITE, (WIDTH - 220, 35))
            for i, data in enumerate(upcoming_trash):
                box_rect = pygame.Rect(WIDTH - 170 + (i * 55), 12, 46, 46)
                draw_beveled_rect(SCREEN, box_rect, (40, 40, 60), 8)
                SCREEN.blit(get_preview_surf(data), (box_rect.x, box_rect.y))
            
            if not is_paused:
                time_left -= 1/60
                if time_left <= 0: game_state = "GAMEOVER"
                
            if is_paused:
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0,0,0,200))
                SCREEN.blit(overlay, (0,0))
                draw_text_with_shadow(SCREEN, "หยุดพัก", font_xl, WHITE, (WIDTH//2, 160), (4,4))
                draw_beveled_rect(SCREEN, btn_resume, (46, 180, 80) if btn_resume.collidepoint(mx,my) else (36, 140, 60), 20)
                draw_text_with_shadow(SCREEN, "ทำต่อ (Resume)", font_md, WHITE, btn_resume.center)
                draw_beveled_rect(SCREEN, btn_restart, (255, 140, 0) if btn_restart.collidepoint(mx,my) else (200, 100, 0), 20)
                draw_text_with_shadow(SCREEN, "เริ่มใหม่ (Restart)", font_md, WHITE, btn_restart.center)
                draw_beveled_rect(SCREEN, btn_exit, (220, 60, 60) if btn_exit.collidepoint(mx,my) else (180, 50, 50), 20)
                draw_text_with_shadow(SCREEN, "ออก (Exit)", font_md, WHITE, btn_exit.center)

        elif game_state == "GAMEOVER":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0,0,0,220))
            SCREEN.blit(overlay, (0,0))
            draw_text_with_shadow(SCREEN, "จบภารกิจ!", font_xl, (255, 80, 80), (WIDTH//2, 280), (4,4))
            draw_text_with_shadow(SCREEN, f"คะแนนรวม: {score}", font_xl, GOLD, (WIDTH//2, 380), (4,4))
            if pygame.time.get_ticks() % 1000 < 500:
                draw_text_with_shadow(SCREEN, "- คลิกเพื่อเริ่มใหม่ -", font_sm, OFF_WHITE, (WIDTH//2, 520))

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()