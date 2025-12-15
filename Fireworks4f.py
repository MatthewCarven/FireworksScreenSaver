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
CONFIG_FILE = "fireworks_config.json"
CONFIG_PATH = os.path.join(CONFIG_DIR, CONFIG_FILE)

DEFAULT_CONFIG = {
    "gravity": 0.05,
    "wind": 0,
    "cursor_pusher_enabled": True,
    "trail_length": 60,
    "pusher_force": 3000,
    "sparks_chaser": 200,
    "sparks_rocket": 100,
    "punishment_mode": False 
}

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
        ctypes.windll.user32.MessageBoxW(None, f"Permission Denied: Cannot write to {CONFIG_DIR}. Try running as Administrator once to create the folder.", "Save Error", 0)
    except Exception as e:
        ctypes.windll.user32.MessageBoxW(None, f"Error saving settings: {e}", "Error", 0)

def open_settings_window():
    current_config = load_config()
    root = tk.Tk()
    root.title("Fireworks Settings")
    root.geometry("400x520") 
    
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
    tk.Scale(root, variable=force_var, from_=10, to=1000, resolution=10, orient=tk.HORIZONTAL, length=300).pack()
    tk.Label(root, text="Max Sparks (Chaser):").pack(pady=2)
    tk.Scale(root, variable=chaser_sparks_var, from_=50, to=500, orient=tk.HORIZONTAL, length=300).pack()
    tk.Label(root, text="Max Sparks (Standard):").pack(pady=2)
    tk.Scale(root, variable=rocket_sparks_var, from_=10, to=300, orient=tk.HORIZONTAL, length=300).pack()
    
    tk.Checkbutton(root, text="Enable Cursor Pushers (Unruly Mode)", variable=pusher_var).pack(pady=5)
    tk.Checkbutton(root, text="Punishment Mode (All Explosions Push)", variable=punish_var, fg="red").pack(pady=5)
    
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
            "punishment_mode": punish_var.get()
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
PUSHER_FORCE = active_config.get("pusher_force", 250)
SPARKS_CHASER_MAX = active_config.get("sparks_chaser", 200)
SPARKS_ROCKET_MAX = active_config.get("sparks_rocket", 100)
PUNISHMENT_MODE = active_config.get("punishment_mode", False)
DRIFT_ACTIVE = False  # Global State

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
    def __init__(self, x, y, color, p_type, vx=0, vy=0):
        self.x = x
        self.y = y
        self.color = list(color) 
        self.p_type = p_type
        self.alive = True
        self.vx = vx
        self.vy = vy
        
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
            self.max_speed = random.uniform(7, 20) 

        elif self.p_type == TYPE_CURSOR_PUSHER:
            self.radius = 0 
            self.decay = 0
            self.life = 60 
            
        else: 
            self.radius = 4
            self.decay = 0

    def move(self):
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
            new_mx = max(0, min(WIDTH, new_mx))
            new_my = max(0, min(HEIGHT, new_my))
            pygame.mouse.set_pos(new_mx, new_my)
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
        self.exploded = True
        new_fireworks = []
        
        if self.is_special and self.p_type == TYPE_ROCKET:
            amount = random.randint(8, 15)
            for _ in range(amount):
                baby = Firework(self.rocket.x, self.rocket.y, p_type=TYPE_CLUSTER)
                new_fireworks.append(baby)
        else:
            # Common Pusher Calculation for all types
            mx, my = pygame.mouse.get_pos()
            dx = mx - self.rocket.x
            dy = my - self.rocket.y
            dist = math.hypot(dx, dy)
            if dist < 1: dist = 1
            dir_x = dx / dist
            dir_y = dy / dist
            
            def create_pusher():
                force_magnitude = PUSHER_FORCE / (dist + 20)
                push_vx = dir_x * force_magnitude
                push_vy = dir_y * force_magnitude
                return Particle(0, 0, self.color, TYPE_CURSOR_PUSHER, vx=push_vx, vy=push_vy)

            if self.p_type == TYPE_CHASER:
                if self.is_special:
                    for _ in range(3):
                        new_fireworks.append(Firework(self.rocket.x, self.rocket.y, p_type=TYPE_CHASER))

                # Safety check (Don't push if drifting)
                if PUSHER_ENABLED and not DRIFT_ACTIVE:
                    self.particles.append(create_pusher())
                
                amount = random.randint(SPARKS_CHASER_MAX // 2, SPARKS_CHASER_MAX)
                for _ in range(amount):
                    p = Particle(self.rocket.x, self.rocket.y, self.color, TYPE_SPARK)
                    self.particles.append(p)

            else:
                # --- STANDARD EXPLOSION ---
                amount = random.randint(SPARKS_ROCKET_MAX // 2, SPARKS_ROCKET_MAX)
                
                # --- PUNISHMENT MODE LOGIC & SAFETY CHECK ---
                if PUNISHMENT_MODE and PUSHER_ENABLED and not DRIFT_ACTIVE:
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
    global DRIFT_ACTIVE # Allow modification of the global
    
    fireworks = []
    font = pygame.font.SysFont("Arial", 24)
    
    # --- New Drift Variables ---
    drift_accum = 0.0
    pygame.mouse.get_rel() # Clear relative movement buffer

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                running = False
                
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_q, pygame.K_ESCAPE]:
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

        # --- USER INTERRUPTION CHECK ---
        # If the mouse moves more than 1 pixel (meaning it wasn't our drift), reset everything
        rel_x, rel_y = pygame.mouse.get_rel()
        if DRIFT_ACTIVE:
            if abs(rel_x) > 1 or abs(rel_y) > 1:
                DRIFT_ACTIVE = False

        # --- EDGE / STUCK CHECK LOGIC ---
        mx, my = pygame.mouse.get_pos()
        # Trigger Drift immediately if in 5px border
        if mx <= 5 or mx >= WIDTH - 6 or my <= 5 or my >= HEIGHT - 6:
             DRIFT_ACTIVE = True
            
        # --- DRIFT LOGIC (10px per second) ---
        if DRIFT_ACTIVE:
            # --- NEW: Safe Zone Check (10% center) ---
            cx, cy = WIDTH // 2, HEIGHT // 2
            safe_w = WIDTH * 0.1
            safe_h = HEIGHT * 0.1
            
            # If within Safe Zone, stop drifting
            if abs(mx - cx) < safe_w and abs(my - cy) < safe_h:
                DRIFT_ACTIVE = False
            else:
                # Drift normally
                drift_accum += 10.0 / FPS  
                if drift_accum >= 1.0:
                    drift_accum -= 1.0
                    
                    new_mx, new_my = mx, my
                    if mx < cx: new_mx += 4
                    elif mx > cx: new_mx -= 4
                    
                    if my < cy: new_my += 2
                    elif my > cy: new_my -= 2
                    
                    pygame.mouse.set_pos(new_mx, new_my)


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

        if WIND != 0:
            wind_text = f"Wind: {WIND}"
            text_surface = font.render(wind_text, True, (255, 255, 255))
            screen.blit(text_surface, (20, 20))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()