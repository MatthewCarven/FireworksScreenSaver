import pygame
import random
import math
import sys
import ctypes

# --- 1. Windows Screensaver Argument Handling ---
if len(sys.argv) > 1:
    arg = sys.argv[1].lower()
    if "/p" in arg:
        sys.exit()
    if "/c" in arg:
        try:
            MessageBox = ctypes.windll.user32.MessageBoxW
            MessageBox(None, "No configuration options available.", "Fireworks Screensaver", 0)
        except:
            pass
        sys.exit()

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

# --- Constants for Particle Types ---
TYPE_ROCKET = 0
TYPE_SPARK = 1
TYPE_CHASER = 2 
TYPE_CLUSTER = 3
TYPE_TRAIL = 4  # <--- NEW TYPE for heavy falling debris

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
        
        # --- Initialize based on Type ---
        if self.p_type == TYPE_SPARK or self.p_type == TYPE_TRAIL:
            # If no velocity provided, generate random explosion
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
            self.max_speed = random.uniform(6, 9)
            
        else: 
            # TYPE_ROCKET and TYPE_CLUSTER
            self.radius = 4
            self.decay = 0

    def move(self):
        # 1. Gravity (Applies to everyone except the active Chaser engine)
        # if self.p_type != TYPE_CHASER:
        self.vy += GRAVITY
        
        # 2. Type Specific Logic
        if self.p_type == TYPE_SPARK:
            # Sparks have HIGH DRAG (they poof and stop)
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
            # Trails have LOW DRAG (they fall nicely)
            self.vx += WIND * 0.02
            
            # 0.96 drag is much lighter than 0.92, allowing gravity to build up speed
            self.vx *= 0.96 
            self.vy *= 0.96 
            
            # Cooling
            self.color[0] = max(0, self.color[0] * 0.98)
            self.color[1] = max(0, self.color[1] * 0.98)
            self.color[2] = max(0, self.color[2] * 0.98)
            
            self.radius -= self.decay
            if self.radius <= 0 or sum(self.color) < 10:
                self.alive = False

        elif self.p_type == TYPE_CHASER:
            # Homing Logic
            mx, my = pygame.mouse.get_pos()
            dx = mx - self.x
            dy = my - self.y
            angle = math.atan2(dy, dx)
            
            self.vx = math.cos(angle) * self.max_speed
            self.vy = math.sin(angle) * self.max_speed
            
            self.fuel -= 1 
            if self.fuel < 100 and random.randint(0, 10) == 0:
                 self.vx *= 0.5
                 self.vy *= 0.5
        
        # 3. Update Position
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
        
        # --- Logic Branching based on Type ---
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
            self.is_special = False
            
            start_x = random.randint(100, WIDTH - 100)
            start_y = HEIGHT
            self.rocket = Particle(start_x, start_y, self.color, TYPE_CHASER)
            
        else:
            # Standard TYPE_ROCKET
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
                # 1. Drop Heavy Trail
                if self.age % 5 == 0: # More frequent trail
                    # We now use TYPE_TRAIL instead of TYPE_SPARK
                    trail_spark = Particle(self.rocket.x, self.rocket.y, self.color, TYPE_TRAIL)
                    trail_spark.vx = random.uniform(-1, 1)
                    trail_spark.vy = random.uniform(0, 2) # Slight downward push to start
                    self.particles.append(trail_spark)

                # 2. Proximity Detonation
                mx, my = pygame.mouse.get_pos()
                dist_to_mouse = math.hypot(mx - self.rocket.x, my - self.rocket.y)
                
                if self.rocket.fuel <= 0 or dist_to_mouse < 30:
                    new_borns = self.explode()

            else:
                # Normal Fuse Logic
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
        
        if self.is_special and self.p_type == TYPE_ROCKET:
            amount = random.randint(8, 15)
            for _ in range(amount):
                baby = Firework(self.rocket.x, self.rocket.y, p_type=TYPE_CLUSTER)
                new_fireworks.append(baby)
        else:
            # Explosion debris is still TYPE_SPARK (so it explodes outward and stops)
            if self.p_type == TYPE_CHASER:
                amount = 200
            else:
                amount = random.randint(60, 120)
                
            for _ in range(amount):
                p = Particle(self.rocket.x, self.rocket.y, self.color, TYPE_SPARK)
                self.particles.append(p)
        return new_fireworks

    def draw(self, surface):
        if not self.exploded:
            self.rocket.draw(surface)
            for particle in self.particles:
                particle.draw(surface)
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

        if random.randint(1, 30) == 1:
            fireworks.append(Firework(p_type=TYPE_ROCKET))

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

        if WIND != 0:
            wind_text = f"Wind: {WIND}"
            text_surface = font.render(wind_text, True, (255, 255, 255))
            screen.blit(text_surface, (20, 20))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()