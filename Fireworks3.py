import pygame
import random
import math
import sys  # Needed for command line arguments
import ctypes # Needed for the message box in Config mode

# --- 1. Windows Screensaver Argument Handling ---
# Windows passes /s, /c, or /p command line arguments.
if len(sys.argv) > 1:
    arg = sys.argv[1].lower()
    
    # PREVIEW MODE (/p): Windows wants us to draw inside a mini-window in the Settings.
    # This is very hard in Pygame, so we just exit to avoid errors.
    if "/p" in arg:
        sys.exit()
        
    # CONFIG MODE (/c): The user clicked "Settings".
    if "/c" in arg:
        # Simple Windows Message Box
        try:
            MessageBox = ctypes.windll.user32.MessageBoxW
            MessageBox(None, "No configuration options available.", "Fireworks Screensaver", 0)
        except:
            pass
        sys.exit()

# If arg is /s (Show) or no arg is provided, the script continues below...

# --- 2. Init & Config ---
pygame.init()
screen_info = pygame.display.Info()
WIDTH = screen_info.current_w
HEIGHT = screen_info.current_h

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Fireworks Screensaver")
clock = pygame.time.Clock()

FPS = 60
BLACK = (0, 0, 0)
GRAVITY = 0.05
WIND = 0 

def random_color():
    # 1. Generate random base colors
    c = [random.randint(50, 255), random.randint(50, 255), random.randint(50, 255)]
    # 2. Force at least one channel to MAX (255) for vibrancy
    c[random.randint(0, 2)] = 255
    return c

# --- Classes ---

class Particle:
    def __init__(self, x, y, color, is_rocket=False, vx=0, vy=0):
        self.x = x
        self.y = y
        self.color = list(color) 
        self.is_rocket = is_rocket
        self.alive = True
        
        self.vx = vx
        self.vy = vy
        
        if not is_rocket:
            if self.vx == 0 and self.vy == 0:
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(2, 12)
                self.vx = math.cos(angle) * speed
                self.vy = math.sin(angle) * speed
            
            self.radius = random.randint(2, 4)
            self.decay = random.uniform(0.02, 0.05) 
        else:
            self.radius = 4
            self.decay = 0

    def move(self):
        self.vy += GRAVITY
        
        # Apply Wind to sparks only
        if not self.is_rocket:
            self.vx += WIND * 0.02

        self.x += self.vx
        self.y += self.vy

        if not self.is_rocket:
            # Air Resistance
            self.vx *= 0.92
            self.vy *= 0.92
            
            # Thermal Cooling (Darken over time)
            self.color[0] = max(0, self.color[0] * 0.99)
            self.color[1] = max(0, self.color[1] * 0.99)
            self.color[2] = max(0, self.color[2] * 0.99)

            self.radius -= self.decay
            
            # Die if too small OR too dark
            if self.radius <= 0 or sum(self.color) < 10:
                self.alive = False

    def draw(self, surface):
        if self.alive and self.radius > 0:
            draw_color = (int(self.color[0]), int(self.color[1]), int(self.color[2]))
            pygame.draw.circle(surface, draw_color, (int(self.x), int(self.y)), int(self.radius))


class Firework:
    def __init__(self, x=None, y=None, is_cluster_child=False):
        self.color = random_color()
        self.particles = []
        self.exploded = False
        self.is_cluster_child = is_cluster_child
        
        if self.is_cluster_child:
            self.fuse = random.randint(20, 50)
            self.is_special = False 
        else:
            self.fuse = random.randint(30, 70)
            self.is_special = (random.randint(1, 5) == 1)

        if x is None:
            # Ground Launch
            start_x = random.randint(100, WIDTH - 100)
            start_y = HEIGHT
            launch_power = -1 * ((HEIGHT / 3) / 45) - random.uniform(3, 6)
            start_vx = random.uniform(-1, 1)
            self.rocket = Particle(start_x, start_y, self.color, is_rocket=True, vx=start_vx, vy=launch_power)
        else:
            # Mid-air Spawn
            angle = random.uniform(math.pi + 0.5, 2 * math.pi - 0.5) 
            speed = random.uniform(6, 14)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self.rocket = Particle(x, y, self.color, is_rocket=True, vx=vx, vy=vy)

        self.age = 0

    def update(self):
        new_borns = []
        if not self.exploded:
            self.rocket.move()
            self.age += 1
            if self.age >= self.fuse or self.rocket.y > HEIGHT:
                new_borns = self.explode()
        else:
            for particle in self.particles:
                particle.move()
            self.particles = [p for p in self.particles if p.alive]
        return new_borns

    def explode(self):
        self.exploded = True
        new_fireworks = []
        
        if self.is_special:
            amount = random.randint(8, 15)
            for _ in range(amount):
                baby = Firework(self.rocket.x, self.rocket.y, is_cluster_child=True)
                new_fireworks.append(baby)
        else:
            amount = random.randint(60, 120)
            for _ in range(amount):
                p = Particle(self.rocket.x, self.rocket.y, self.color, is_rocket=False)
                self.particles.append(p)
        return new_fireworks

    def draw(self, surface):
        if not self.exploded:
            self.rocket.draw(surface)
        else:
            for particle in self.particles:
                particle.draw(surface)

    def is_finished(self):
        return self.exploded and len(self.particles) == 0

# --- Main Loop ---

def main():
    global WIND
    fireworks = []
    
    font = pygame.font.SysFont("Arial", 24)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                # Quit on any key except Arrows/Special Keys
                if event.key in [pygame.K_q, pygame.K_ESCAPE]:
                    running = False
                
                # Interactive features
                if event.key == pygame.K_SPACE:
                    fireworks.append(Firework())
                if event.key == pygame.K_BACKSLASH:
                    for _ in range(10): fireworks.append(Firework())
                if event.key == pygame.K_F12:
                    for _ in range(30): fireworks.append(Firework())
                
                # Wind Controls
                if event.key == pygame.K_RIGHT:
                    WIND += 1
                if event.key == pygame.K_LEFT:
                    WIND -= 1

        if random.randint(1, 15) == 1:
            fireworks.append(Firework())

        # Update
        current_fireworks = fireworks[:] 
        new_additions = []
        for fw in current_fireworks:
            babies = fw.update()
            if babies:
                new_additions.extend(babies)
        fireworks.extend(new_additions)
        fireworks = [fw for fw in fireworks if not fw.is_finished()]

        # Draw
        trail_surface = pygame.Surface((WIDTH, HEIGHT))
        trail_surface.set_alpha(60)
        trail_surface.fill(BLACK)
        screen.blit(trail_surface, (0, 0))

        for fw in fireworks:
            fw.draw(screen)

        # Draw Wind Indicator (ONLY IF WIND IS NOT ZERO)
        if WIND != 0:
            wind_text = f"Wind: {WIND}"
            text_surface = font.render(wind_text, True, (255, 255, 255))
            screen.blit(text_surface, (20, 20))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()