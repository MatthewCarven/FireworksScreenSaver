# Fireworks12g.scr - ID/Error - Matthew Carven - Google Gemini
# Simplified AFK Logic:
# - Removed Wall Drift/Edge Detection.
# - Added AFK Teleport: If mouse is static for 30s, it teleports to a random spot.
# - Safe Timer & Kill Streak only reset on PHYSICAL HITS.

import pygame
import random
import math
import sys
import ctypes
import json
import os
import tkinter as tk
from tkinter import messagebox

# --- Configuration Paths ---
CONFIG_DIR = r"C:\screensaverconfigs"
CONFIG_FILE = "fireworks_config4g.json"
CONFIG_PATH = os.path.join(CONFIG_DIR, CONFIG_FILE)

DEFAULT_CONFIG = {
    "gravity": 0.05,
    "wind": 0,
    "cursor_pusher_enabled": True,
    "trail_length": 40,
    "pusher_force": 1000,
    "sparks_chaser": 200,
    "sparks_rocket": 100,
    "punishment_mode": False,
    "high_score_time": 0.0,
    "high_score_chasers": 0
}

# --- Global Game State ---
LAST_HIT_TIME = 0
CHASER_SCORE = 0

def load_config():
    try:
        with open(CONFIG_PATH, 'r') as f:
            data = json.load(f)
            for key, value in DEFAULT_CONFIG.items():
                if key not in data:
                    data[key] = value
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return DEFAULT_CONFIG

def save_config(config_data):
    try:
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config_data, f, indent=4)
    except PermissionError:
        pass 
    except Exception as e:
        print(f"Save error: {e}")

# --- Helper to Update High Scores ---
def check_and_save_high_scores():
    global LAST_HIT_TIME, CHASER_SCORE, active_config
    
    current_duration = (pygame.time.get_ticks() - LAST_HIT_TIME) / 1000.0
    changed = False
    
    # Check Time
    if current_duration > active_config["high_score_time"]:
        active_config["high_score_time"] = round(current_duration, 1)
        changed = True
        
    # Check Kills
    if CHASER_SCORE > active_config["high_score_chasers"]:
        active_config["high_score_chasers"] = CHASER_SCORE
        changed = True
        
    if changed:
        save_config(active_config)


def open_settings_window():
    current_config = load_config()
    root = tk.Tk()
    root.title("Fireworks Settings")
    root.geometry("400x550") 
    
    gravity_var = tk.DoubleVar(value=current_config.get("gravity", 0.05))
    wind_var = tk.IntVar(value=current_config.get("wind", 0))
    pusher_var = tk.BooleanVar(value=current_config.get("cursor_pusher_enabled", True))
    trail_var = tk.IntVar(value=current_config.get("trail_length", 60))
    force_var = tk.IntVar(value=current_config.get("pusher_force", 3000))
    chaser_sparks_var = tk.IntVar(value=current_config.get("sparks_chaser", 200))
    rocket_sparks_var = tk.IntVar(value=current_config.get("sparks_rocket", 100))
    punish_var = tk.BooleanVar(value=current_config.get("punishment_mode", False))

    tk.Label(root, text="Gravity (0.01 - 0.2):").pack(pady=2)
    tk.Scale(root, variable=gravity_var, from_=0.01, to=0.2, resolution=0.01, orient=tk.HORIZONTAL, length=300).pack()
    tk.Label(root, text="Wind (-5 to 5):").pack(pady=2)
    tk.Scale(root, variable=wind_var, from_=-5, to=5, orient=tk.HORIZONTAL, length=300).pack()
    tk.Label(root, text="Pusher Force (1000 - 10000):").pack(pady=2)
    tk.Scale(root, variable=force_var, from_=1000, to=10000, resolution=100, orient=tk.HORIZONTAL, length=300).pack()
    tk.Label(root, text="Max Sparks (Chaser):").pack(pady=2)
    tk.Scale(root, variable=chaser_sparks_var, from_=50, to=500, orient=tk.HORIZONTAL, length=300).pack()
    tk.Label(root, text="Max Sparks (Standard):").pack(pady=2)
    tk.Scale(root, variable=rocket_sparks_var, from_=10, to=300, orient=tk.HORIZONTAL, length=300).pack()
    
    tk.Checkbutton(root, text="Enable Cursor Pushers (Unruly Mode)", variable=pusher_var).pack(pady=5)
    tk.Checkbutton(root, text="Punishment Mode (All Explosions Push)", variable=punish_var, fg="red").pack(pady=5)
    
    best_time = current_config.get("high_score_time", 0)
    best_kills = current_config.get("high_score_chasers", 0)
    tk.Label(root, text=f"Best Time: {best_time}s | Best Kills: {best_kills}", font=("Arial", 10, "bold"), fg="blue").pack(pady=10)
    
    tk.Label(root, text=f"Config location: {CONFIG_PATH}", font=("Arial", 8), fg="gray").pack(pady=5)

    def on_save():
        new_config = {
            "gravity": round(gravity_var.get(), 3),
            "wind": wind_var.get(),
            "cursor_pusher_enabled": pusher_var.get(),
            "trail_length": trail_var.get(),
            "pusher_force": force_var.get(),
            "sparks_chaser": chaser_sparks_var.get(),
            "sparks_rocket": rocket_sparks_var.get(),
            "punishment_mode": punish_var.get(),
            "high_score_time": best_time,       
            "high_score_chasers": best_kills
        }
        save_config(new_config)
        messagebox.showinfo("Saved", f"Settings saved to:\n{CONFIG_PATH}")
        root.destroy()

    tk.Button(root, text="Save & Close", command=on_save, height=2, width=20).pack(pady=5)
    root.mainloop()

# --- 1. Windows Screensaver Argument Handling ---
if len(sys.argv) > 1:
    arg = sys.argv[1].lower()
    if "/p" in arg: pass 
    if "/c" in arg: 
        open_settings_window()
        sys.exit()
    if "/s" in arg: pass

# --- 2. Load Config & Init ---
active_config = load_config()

pygame.init()
screen_info = pygame.display.Info()
WIDTH = screen_info.current_w
HEIGHT = screen_info.current_h

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Fireworks Screensaver")
clock = pygame.time.Clock()

FPS = 60
BLACK = (0, 0, 0)

# Apply Config
GRAVITY = active_config.get("gravity", 0.05)
WIND = active_config.get("wind", 0)
PUSHER_ENABLED = active_config.get("cursor_pusher_enabled", True)
TRAIL_ALPHA = active_config.get("trail_length", 60)
PUSHER_FORCE = active_config.get("pusher_force", 1000)
SPARKS_CHASER_MAX = active_config.get("sparks_chaser", 200)
SPARKS_ROCKET_MAX = active_config.get("sparks_rocket", 100)
PUNISHMENT_MODE = active_config.get("punishment_mode", False)

TYPE_ROCKET = 0
TYPE_SPARK = 1
TYPE_CHASER = 2 
TYPE_CLUSTER = 3
TYPE_TRAIL = 4 
TYPE_CURSOR_PUSHER = 5 

def random_color():
    c = [random.randint(50, 255), random.randint(50, 255), random.randint(50, 255)]
    c[random.randint(0, 2)] = 255
    return c

# --- Classes ---

class Particle:
    def __init__(self, x, y, color, p_type, vx=0, vy=0, source_type=None):
        self.x = x
        self.y = y
        self.color = list(color) 
        self.p_type = p_type
        self.alive = True
        self.vx = vx
        self.vy = vy
        self.source_type = source_type 
        
        if self.p_type == TYPE_SPARK or self.p_type == TYPE_TRAIL:
            if self.vx == 0 and self.vy == 0:
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(2, 12)
                self.vx = math.cos(angle) * speed
                self.vy = math.sin(angle) * speed
            self.radius = random.randint(2, 4)
            self.decay = random.uniform(0.02, 0.05) 
            
        elif self.p_type == TYPE_CHASER:
            self.radius = 6
            self.decay = 0
            self.fuel = random.randint(600, 900)
            self.max_speed = random.uniform(8, 21) 

        elif self.p_type == TYPE_CURSOR_PUSHER:
            self.radius = 0 
            self.decay = 0
            self.life = 60 
            
        else: 
            self.radius = 4
            self.decay = 0

    def move(self):
        global LAST_HIT_TIME, CHASER_SCORE

        # Gravity
        if self.p_type != TYPE_CHASER and self.p_type != TYPE_CURSOR_PUSHER:
            self.vy += GRAVITY
        
        # Type Specific Logic
        if self.p_type == TYPE_SPARK:
            self.vx += WIND * 0.02
            self.vx *= 0.92 
            self.vy *= 0.92 
            self.color[0] = max(0, self.color[0] * 0.99)
            self.color[1] = max(0, self.color[1] * 0.99)
            self.color[2] = max(0, self.color[2] * 0.99)
            self.radius -= self.decay
            if self.radius <= 0 or sum(self.color) < 10:
                self.alive = False

        elif self.p_type == TYPE_TRAIL:
            self.vx += WIND * 0.02
            self.vx *= 0.96 
            self.vy *= 0.96 
            self.color[0] = max(0, self.color[0] * 0.98)
            self.color[1] = max(0, self.color[1] * 0.98)
            self.color[2] = max(0, self.color[2] * 0.98)
            self.radius -= self.decay
            if self.radius <= 0 or sum(self.color) < 10:
                self.alive = False

        elif self.p_type == TYPE_CHASER:
            mx, my = pygame.mouse.get_pos()
            dx = mx - self.x
            dy = my - self.y
            angle = math.atan2(dy, dx)
            
            thrust_power = 0.4 
            self.vx += math.cos(angle) * thrust_power
            self.vy += math.sin(angle) * thrust_power
            
            current_speed = math.hypot(self.vx, self.vy)
            if current_speed > self.max_speed:
                scale = self.max_speed / current_speed
                self.vx *= scale
                self.vy *= scale
            
            self.fuel -= 1 
            if self.fuel < 100 and random.randint(0, 10) == 0:
                 self.vx *= 0.9
                 self.vy *= 0.9

        elif self.p_type == TYPE_CURSOR_PUSHER:
            mx, my = pygame.mouse.get_pos()
            new_mx = mx + self.vx
            new_my = my + self.vy
            
            # Bound checking
            new_mx = max(0, min(WIDTH, new_mx))
            new_my = max(0, min(HEIGHT, new_my))
            
            # --- HIT REGISTRATION ---
            force_applied = math.hypot(self.vx, self.vy)
            HIT_THRESHOLD = 3.0 
            
            if force_applied > 0:
                 pygame.mouse.set_pos(new_mx, new_my)

            if force_applied > HIT_THRESHOLD:
                # 1. SAVE HIGH SCORES BEFORE RESETTING
                check_and_save_high_scores()
                
                # 2. ALWAYS RESET TIMER ON PHYSICAL HIT
                LAST_HIT_TIME = pygame.time.get_ticks()

                # 3. RESET SCORE (Only if Chaser)
                if self.source_type == TYPE_CHASER:
                    CHASER_SCORE = 0

            self.vx *= 0.9
            self.vy *= 0.9
            if abs(self.vx) < 0.1 and abs(self.vy) < 0.1:
                self.alive = False
        
        if self.p_type != TYPE_CURSOR_PUSHER:
            self.x += self.vx
            self.y += self.vy

    def draw(self, surface):
        if self.alive and self.radius > 0:
            draw_color = (int(self.color[0]), int(self.color[1]), int(self.color[2]))
            pygame.draw.circle(surface, draw_color, (int(self.x), int(self.y)), int(self.radius))


class Firework:
    def __init__(self, x=None, y=None, p_type=TYPE_ROCKET):
        self.color = random_color()
        self.particles = []
        self.exploded = False
        self.p_type = p_type
        
        if self.p_type == TYPE_CLUSTER:
            self.fuse = random.randint(20, 50)
            self.is_special = False
            angle = random.uniform(math.pi + 0.5, 2 * math.pi - 0.5) 
            speed = random.uniform(6, 14)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self.rocket = Particle(x, y, self.color, TYPE_CLUSTER, vx=vx, vy=vy)
            
        elif self.p_type == TYPE_CHASER:
            self.fuse = 99999 
            self.is_special = (random.randint(1, 25) == 1) # 4% Chance
            
            if x is not None and y is not None:
                start_x, start_y = x, y
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(6, 15) 
                start_vx = math.cos(angle) * speed
                start_vy = math.sin(angle) * speed
            else:
                start_vx = 0
                start_vy = 0
                side = random.randint(0, 3)
                if side == 0: 
                    start_x = random.randint(0, WIDTH)
                    start_y = -10
                elif side == 1: 
                    start_x = random.randint(0, WIDTH)
                    start_y = HEIGHT + 10
                elif side == 2: 
                    start_x = -10
                    start_y = random.randint(0, HEIGHT)
                elif side == 3: 
                    start_x = WIDTH + 10
                    start_y = random.randint(0, HEIGHT)

            self.rocket = Particle(start_x, start_y, self.color, TYPE_CHASER, vx=start_vx, vy=start_vy)
            
        else:
            self.fuse = random.randint(30, 70)
            self.is_special = (random.randint(1, 5) == 1)
            start_x = random.randint(100, WIDTH - 100)
            start_y = HEIGHT
            launch_power = -1 * ((HEIGHT / 3) / 45) - random.uniform(3, 6)
            start_vx = random.uniform(-1, 1)
            self.rocket = Particle(start_x, start_y, self.color, TYPE_ROCKET, vx=start_vx, vy=launch_power)

        self.age = 0

    def update(self):
        new_borns = []
        
        if not self.exploded:
            self.rocket.move()
            self.age += 1
            
            if self.p_type == TYPE_CHASER:
                if self.age % 2 == 0: 
                    trail_spark = Particle(self.rocket.x, self.rocket.y, self.color, TYPE_TRAIL)
                    trail_spark.vx = random.uniform(-1, 1)
                    trail_spark.vy = random.uniform(0, 2)
                    self.particles.append(trail_spark)

                mx, my = pygame.mouse.get_pos()
                dist_to_mouse = math.hypot(mx - self.rocket.x, my - self.rocket.y)
                
                # Minimum Flight Time Check
                if self.rocket.fuel <= 0 or (dist_to_mouse < 30 and self.age > 30):
                    new_borns = self.explode()
            else:
                if self.age >= self.fuse or self.rocket.y > HEIGHT:
                    new_borns = self.explode()

        for particle in self.particles:
            particle.move()
            
        self.particles = [p for p in self.particles if p.alive]
        
        return new_borns

    def explode(self):
        global CHASER_SCORE
        self.exploded = True
        new_fireworks = []
        
        if self.is_special and self.p_type == TYPE_ROCKET:
            amount = random.randint(8, 15)
            for _ in range(amount):
                baby = Firework(self.rocket.x, self.rocket.y, p_type=TYPE_CLUSTER)
                new_fireworks.append(baby)
        else:
            mx, my = pygame.mouse.get_pos()
            dx = mx - self.rocket.x
            dy = my - self.rocket.y
            dist = math.hypot(dx, dy)
            if dist < 1: dist = 1
            dir_x = dx / dist
            dir_y = dy / dist
            
            def create_pusher():
                force = PUSHER_FORCE
                if self.p_type == TYPE_CLUSTER:
                    force = force / 5
                
                force_magnitude = force / (dist + 20)
                push_vx = dir_x * force_magnitude
                push_vy = dir_y * force_magnitude
                return Particle(0, 0, self.color, TYPE_CURSOR_PUSHER, vx=push_vx, vy=push_vy, source_type=self.p_type)

            if self.p_type == TYPE_CHASER:
                # INCREMENT SCORE
                CHASER_SCORE += 1
                
                if self.is_special:
                    for _ in range(3):
                        new_fireworks.append(Firework(self.rocket.x, self.rocket.y, p_type=TYPE_CHASER))

                if PUSHER_ENABLED:
                    self.particles.append(create_pusher())
                
                amount = random.randint(SPARKS_CHASER_MAX // 2, SPARKS_CHASER_MAX)
                for _ in range(amount):
                    p = Particle(self.rocket.x, self.rocket.y, self.color, TYPE_SPARK)
                    self.particles.append(p)

            else:
                amount = random.randint(SPARKS_ROCKET_MAX // 2, SPARKS_ROCKET_MAX)
                if PUNISHMENT_MODE and PUSHER_ENABLED:
                    self.particles.append(create_pusher())

            for _ in range(amount):
                p = Particle(self.rocket.x, self.rocket.y, self.color, TYPE_SPARK)
                self.particles.append(p)
                
        return new_fireworks

    def draw(self, surface):
        if not self.exploded:
            self.rocket.draw(surface)
        
        for particle in self.particles:
            particle.draw(surface)

    def is_finished(self):
        return self.exploded and len(self.particles) == 0

# --- Main Loop ---

def main():
    global WIND
    global LAST_HIT_TIME, CHASER_SCORE
    
    fireworks = []
    font = pygame.font.SysFont("Arial", 24)
    timer_font = pygame.font.SysFont("Consolas", 32, bold=True)
    score_font = pygame.font.SysFont("Consolas", 32, bold=True)
    small_font = pygame.font.SysFont("Consolas", 18)
    
    # Init Mouse State for AFK Tracking
    last_mouse_pos = pygame.mouse.get_pos()
    last_move_time = pygame.time.get_ticks()
    
    LAST_HIT_TIME = pygame.time.get_ticks()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                check_and_save_high_scores() 
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                check_and_save_high_scores() 
                running = False
                
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_q, pygame.K_ESCAPE]:
                    check_and_save_high_scores() 
                    running = False
                
                if event.key == pygame.K_SPACE:
                    fireworks.append(Firework(p_type=TYPE_ROCKET))
                if event.key == pygame.K_c:
                    fireworks.append(Firework(p_type=TYPE_CHASER))
                if event.key == pygame.K_BACKSLASH:
                    for _ in range(10): fireworks.append(Firework(p_type=TYPE_ROCKET))
                if event.key == pygame.K_F12:
                    for _ in range(30): fireworks.append(Firework(p_type=TYPE_ROCKET))
                
                if event.key == pygame.K_RIGHT:
                    WIND += 1
                if event.key == pygame.K_LEFT:
                    WIND -= 1

        # --- AFK / IDLE LOGIC ---
        mx, my = pygame.mouse.get_pos()
        dist_moved = math.hypot(mx - last_mouse_pos[0], my - last_mouse_pos[1])
        
        # If moved significantly (>3px), reset idle timer
        if dist_moved > 3:
            last_mouse_pos = (mx, my)
            last_move_time = pygame.time.get_ticks()
            
        # Check if idle for > 30 seconds
        if pygame.time.get_ticks() - last_move_time > 30000:
            # Teleport!
            new_x = random.randint(50, WIDTH - 50)
            new_y = random.randint(50, HEIGHT - 50)
            pygame.mouse.set_pos(new_x, new_y)
            
            # Reset trackers to the new position so we don't loop teleport
            last_mouse_pos = (new_x, new_y)
            last_move_time = pygame.time.get_ticks()

        # Auto-launch
        if random.randint(1, 30) == 1:
            if random.randint(1, 10) == 1:
                fireworks.append(Firework(p_type=TYPE_CHASER))
            else:
                fireworks.append(Firework(p_type=TYPE_ROCKET))

        current_fireworks = fireworks[:] 
        new_additions = []
        for fw in current_fireworks:
            babies = fw.update()
            if babies:
                new_additions.extend(babies)
        fireworks.extend(new_additions)
        fireworks = [fw for fw in fireworks if not fw.is_finished()]

        # Draw Trail
        trail_surface = pygame.Surface((WIDTH, HEIGHT))
        trail_surface.set_alpha(TRAIL_ALPHA) 
        trail_surface.fill(BLACK)
        screen.blit(trail_surface, (0, 0))

        for fw in fireworks:
            fw.draw(screen)

        # --- UI OVERLAYS ---
        
        # 1. Wind
        if WIND != 0:
            wind_text = f"Wind: {WIND}"
            text_surface = font.render(wind_text, True, (255, 255, 255))
            screen.blit(text_surface, (20, 20))

        # 2. Survival Timer & Score (Not in Punishment Mode)
        if not PUNISHMENT_MODE:
            current_time = pygame.time.get_ticks()
            elapsed_seconds = (current_time - LAST_HIT_TIME) / 1000.0
            
            # Show timer if safe for > 30s
            if elapsed_seconds > 30:
                time_str = f"Safe Time: {elapsed_seconds:.1f}s"
                time_surf = timer_font.render(time_str, True, (0, 255, 0)) # Green text
                screen.blit(time_surf, (WIDTH - time_surf.get_width() - 20, 20))
                
                # Show Best Time
                best_time = active_config.get("high_score_time", 0.0)
                best_time_str = f"Best: {best_time}s"
                best_time_surf = small_font.render(best_time_str, True, (100, 100, 100))
                screen.blit(best_time_surf, (WIDTH - best_time_surf.get_width() - 20, 55))
            
            # Show score if > 0
            if CHASER_SCORE > 0:
                score_str = f"Chasers Survived: {CHASER_SCORE}"
                score_surf = score_font.render(score_str, True, (255, 50, 50)) # Red text
                
                y_pos = 80 if elapsed_seconds > 30 else 20
                screen.blit(score_surf, (WIDTH - score_surf.get_width() - 20, y_pos))
                
                # Show Best Score
                best_score = active_config.get("high_score_chasers", 0)
                best_score_str = f"Best: {best_score}"
                best_score_surf = small_font.render(best_score_str, True, (100, 100, 100))
                screen.blit(best_score_surf, (WIDTH - best_score_surf.get_width() - 20, y_pos + 35))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()