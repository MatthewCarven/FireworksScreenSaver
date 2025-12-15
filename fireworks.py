import pygame
import random
import math

# --- 1. Initialize Pygame FIRST ---
pygame.init()

# --- 2. Detect Screen Resolution ---
screen_info = pygame.display.Info()
WIDTH = screen_info.current_w
HEIGHT = screen_info.current_h

# Set up the display in Fullscreen mode
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Python Fireworks")
clock = pygame.time.Clock()

# --- Constants ---
FPS = 60            # <--- This was missing!
BLACK = (0, 0, 0)
GRAVITY = 0.05

def random_color():
    return (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))

# --- Classes ---

class Particle:
    def __init__(self, x, y, color, is_rocket=False):
        self.x = x
        self.y = y
        self.color = color
        self.is_rocket = is_rocket
        self.alive = True
        
        if self.is_rocket:
            # Rocket physics
            self.vx = random.uniform(-1, 1)
            # Adjust launch speed slightly based on screen height
            # Taller screens need more power to reach the middle
            launch_power = -1 * ((HEIGHT / 3) / 45) 
            self.vy = random.uniform(launch_power - 2, launch_power)
            
            self.radius = 4
            self.decay = 0
        else:
            # --- EXPLOSION PHYSICS ---
            angle = random.uniform(0, 2 * math.pi)
            
            # Fast start
            speed = random.uniform(8, 16) 
            
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed
            self.radius = random.randint(2, 4)
            self.decay = random.uniform(0.04, 0.08)

    def move(self):
        # Apply Gravity
        self.vy += GRAVITY
        
        # Move particle
        self.x += self.vx
        self.y += self.vy

        if not self.is_rocket:
            # --- "POP" FRICTION ---
            self.vx *= 0.85
            self.vy *= 0.85
            
            # Shrink
            self.radius -= self.decay
            if self.radius <= 0:
                self.alive = False
        else:
            # Rocket logic: explode when it starts falling
            if self.vy >= 0:
                self.alive = False

    def draw(self, surface):
        if self.alive and self.radius > 0:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.radius))


class Firework:
    def __init__(self):
        self.color = random_color()
        self.rocket = Particle(random.randint(50, WIDTH - 50), HEIGHT, self.color, is_rocket=True)
        self.particles = []
        self.exploded = False

    def update(self):
        if not self.exploded:
            self.rocket.move()
            if not self.rocket.alive:
                self.explode()
        else:
            for particle in self.particles:
                particle.move()
            self.particles = [p for p in self.particles if p.alive]

    def explode(self):
        self.exploded = True
        amount = random.randint(50, 100)
        for _ in range(amount):
            p = Particle(self.rocket.x, self.rocket.y, self.color, is_rocket=False)
            self.particles.append(p)

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
    fireworks = []
    
    running = True
    while running:
        # 1. Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                # Quit on Q or ESC (Escape is standard for fullscreen apps)
                if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                    running = False
                
                # Spacebar for manual firework
                if event.key == pygame.K_SPACE:
                    fireworks.append(Firework())

        # 2. Update Logic
        if random.randint(1, 40) == 1:
            fireworks.append(Firework())

        for fw in fireworks:
            fw.update()
        
        fireworks = [fw for fw in fireworks if not fw.is_finished()]

        # 3. Drawing
        trail_surface = pygame.Surface((WIDTH, HEIGHT))
        trail_surface.set_alpha(50) 
        trail_surface.fill(BLACK)
        screen.blit(trail_surface, (0, 0))

        for fw in fireworks:
            fw.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()