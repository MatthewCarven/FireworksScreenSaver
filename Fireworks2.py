import pygame
import random
import math

# --- 1. Init & Config ---
pygame.init()
screen_info = pygame.display.Info()
WIDTH = screen_info.current_w
HEIGHT = screen_info.current_h

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Cluster Fireworks")
clock = pygame.time.Clock()

FPS = 60
BLACK = (0, 0, 0)
GRAVITY = 0.05

def random_color():
    return (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))

# --- Classes ---

class Particle:
    """A single point in space (Rocket or Spark)."""
    def __init__(self, x, y, color, is_rocket=False, vx=0, vy=0):
        self.x = x
        self.y = y
        self.color = color
        self.is_rocket = is_rocket
        self.alive = True
        
        # If velocity is passed in, use it. Otherwise, randomize.
        self.vx = vx
        self.vy = vy
        
        if not is_rocket:
            # Explosion spark defaults
            if self.vx == 0 and self.vy == 0:
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(2, 10)
                self.vx = math.cos(angle) * speed
                self.vy = math.sin(angle) * speed
            
            self.radius = random.randint(2, 4)
            self.decay = random.uniform(0.05, 0.15)
        else:
            # Rocket defaults
            self.radius = 4
            self.decay = 0

    def move(self):
        self.vy += GRAVITY
        self.x += self.vx
        self.y += self.vy

        if not self.is_rocket:
            # Drag/Friction for sparks
            self.vx *= 0.9
            self.vy *= 0.9
            self.radius -= self.decay
            if self.radius <= 0:
                self.alive = False

    def draw(self, surface):
        if self.alive and self.radius > 0:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.radius))


class Firework:
    def __init__(self, x=None, y=None, is_cluster_child=False):
        """
        x, y: Optional starting coordinates (for cluster children)
        is_cluster_child: If True, this is a baby firework spawned from a parent
        """
        self.color = random_color()
        self.particles = []
        self.exploded = False
        self.is_cluster_child = is_cluster_child
        
        # --- 1. RANDOM FUSE (1 to 3 seconds) ---
        # 60 FPS * 1s = 60 frames. 
        if self.is_cluster_child:
            # Baby fireworks explode faster (0.5 to 1.0 second)
            self.fuse = random.randint(30, 60)
            self.is_special = False # Babies are never special (prevents infinite loop)
        else:
            # Main fireworks
            self.fuse = random.randint(30, 60) # 1s to 3s
            # 20% chance to be a "Special" Cluster Firework
            self.is_special = (random.randint(1, 4) == 1)

        # --- Launch Logic ---
        if x is None:
            # Ground Launch
            start_x = random.randint(50, WIDTH - 50)
            start_y = HEIGHT
            # High vertical velocity to last 3 seconds
            launch_power = -1 * ((HEIGHT / 3) / 45) - random.uniform(2, 5)
            # Slight random spread
            start_vx = random.uniform(-1, 1)
            
            self.rocket = Particle(start_x, start_y, self.color, is_rocket=True, vx=start_vx, vy=launch_power)
        else:
            # Mid-air Spawn (Cluster Child)
            # Spread out in a semi-circle upwards
            angle = random.uniform(math.pi + 0.5, 2 * math.pi - 0.5) # Upwards arc
            speed = random.uniform(5, 12)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            self.rocket = Particle(x, y, self.color, is_rocket=True, vx=vx, vy=vy)

        self.age = 0

    def update(self):
        new_borns = [] # List to return new fireworks if we are special

        if not self.exploded:
            self.rocket.move()
            self.age += 1
            
            # --- FUSE CHECK ---
            # Explode if time is up OR if it hits the ground
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
        
        # --- 2. SPECIAL CLUSTER LOGIC ---
        if self.is_special:
            # Instead of sparks, spawn 5-10 NEW Fireworks
            amount = random.randint(10, 25)
            for _ in range(amount):
                # Create baby firework at current position
                # Note: We don't add it to self.particles, we return it to main loop
                baby = Firework(self.rocket.x, self.rocket.y, is_cluster_child=True)
                new_fireworks.append(baby)
        else:
            # Normal Explosion
            amount = random.randint(25, 50)
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
    fireworks = []
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_SPACE:
                    fireworks.append(Firework())
                if event.key == pygame.K_BACKSLASH:
                    for each in range(1,10,1):
                        fireworks.append(Firework())
                if event.key == pygame.K_F12:
                    for each in range(1,100,1):
                        fireworks.append(Firework())


        # Auto-launch
        if random.randint(1, 10) == 1:
            fireworks.append(Firework())

        # Update and handle Cluster Spawns
        # We need to use a temporary list because we can't modify 'fireworks' while iterating
        current_fireworks = fireworks[:] 
        new_additions = []
        
        for fw in current_fireworks:
            # fw.update() now returns a list of babies (if any)
            babies = fw.update()
            if babies:
                new_additions.extend(babies)
        
        # Add the babies to the main list
        fireworks.extend(new_additions)
        
        # Clean up dead fireworks
        fireworks = [fw for fw in fireworks if not fw.is_finished()]

        # Draw
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