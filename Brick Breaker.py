
import pygame
import sys
import random
from pygame.locals import *

# Initialize pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 15
BALL_RADIUS = 8
BRICK_WIDTH = 75
BRICK_HEIGHT = 20
POWERUP_SIZE = 20
POWERUP_SPEED = 3

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)
GRAY = (128, 128, 128)

# Power-up types
POWERUP_EXTEND = "extend_paddle"
POWERUP_SHRINK = "shrink_paddle"
POWERUP_MULTIBALL = "multiball"
POWERUP_FAST = "fast_ball"
POWERUP_SLOW = "slow_ball"
POWERUP_STICKY = "sticky_paddle"

class Paddle:
    def __init__(self):
        self.width = PADDLE_WIDTH
        self.height = PADDLE_HEIGHT
        self.x = (SCREEN_WIDTH - self.width) // 2
        self.y = SCREEN_HEIGHT - self.height - 10
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.speed = 8
        self.sticky = False
        self.sticky_timer = 0
    
    def update(self):
        keys = pygame.key.get_pressed()
        if keys[K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[K_RIGHT] and self.rect.right < SCREEN_WIDTH:
            self.rect.x += self.speed
        
        # Update sticky timer
        if self.sticky and pygame.time.get_ticks() > self.sticky_timer:
            self.sticky = False
    
    def draw(self, surface):
        pygame.draw.rect(surface, WHITE, self.rect)
        if self.sticky:
            # Draw a visual indicator for sticky paddle
            pygame.draw.rect(surface, GREEN, (self.rect.x, self.rect.y - 5, self.width, 3))

class Ball:
    def __init__(self, x=None, y=None):
        self.radius = BALL_RADIUS
        if x is None and y is None:
            self.x = SCREEN_WIDTH // 2
            self.y = SCREEN_HEIGHT // 2
        else:
            self.x = x
            self.y = y
        self.dx = 4 * random.choice([-1, 1])
        self.dy = -4
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius, 
                               self.radius * 2, self.radius * 2)
        self.active = True
    
    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.rect.x = self.x - self.radius
        self.rect.y = self.y - self.radius
        
        # Wall collision
        if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
            self.dx *= -1
        if self.rect.top <= 0:
            self.dy *= -1
        
        # Bottom screen check
        if self.rect.top > SCREEN_HEIGHT:
            self.active = False
    
    def draw(self, surface):
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.radius)
    
    def reset(self, paddle):
        self.x = paddle.rect.centerx
        self.y = paddle.rect.top - self.radius
        self.dx = 4 * random.choice([-1, 1])
        self.dy = -4
        self.active = True

class Brick:
    def __init__(self, x, y, color, hits=1):
        self.rect = pygame.Rect(x, y, BRICK_WIDTH, BRICK_HEIGHT)
        self.color = color
        self.hits = hits
        self.original_hits = hits
        self.active = True
    
    def draw(self, surface):
        if not self.active:
            return
        
        pygame.draw.rect(surface, self.color, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)
        
        # Show hit count if more than 1
        if self.hits > 1:
            font = pygame.font.SysFont(None, 20)
            text = font.render(str(self.hits), True, WHITE)
            text_rect = text.get_rect(center=self.rect.center)
            surface.blit(text, text_rect)
    
    def hit(self):
        self.hits -= 1
        if self.hits <= 0:
            self.active = False
            return True  # Brick destroyed
        return False  # Brick still alive

class PowerUp:
    def __init__(self, x, y, type):
        self.rect = pygame.Rect(x, y, POWERUP_SIZE, POWERUP_SIZE)
        self.type = type
        self.speed = POWERUP_SPEED
        self.active = True
        
        # Set color based on type
        if type == POWERUP_EXTEND:
            self.color = GREEN
        elif type == POWERUP_SHRINK:
            self.color = RED
        elif type == POWERUP_MULTIBALL:
            self.color = CYAN
        elif type == POWERUP_FAST:
            self.color = YELLOW
        elif type == POWERUP_SLOW:
            self.color = BLUE
        elif type == POWERUP_STICKY:
            self.color = PURPLE
    
    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.active = False
    
    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)
        pygame.draw.rect(surface, WHITE, self.rect, 2)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Brick Breaker")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)
        self.small_font = pygame.font.SysFont(None, 24)
        
        self.paddle = Paddle()
        self.balls = [Ball()]
        self.bricks = []
        self.powerups = []
        self.level = 1
        self.lives = 3
        self.score = 0
        self.game_over = False
        self.paused = False
        self.level_complete = False
        
        self.create_level(self.level)
    
    def create_level(self, level):
        self.bricks = []
        colors = [RED, GREEN, BLUE, YELLOW, PURPLE, CYAN, ORANGE]
        
        # Adjust brick layout based on level
        rows = min(3 + level, 8)  # Max 8 rows
        cols = SCREEN_WIDTH // (BRICK_WIDTH + 5)  # Calculate columns based on screen width
        
        for row in range(rows):
            for col in range(cols):
                # Skip some bricks randomly to make patterns
                if random.random() > 0.2:  # 80% chance to place a brick
                    x = 5 + col * (BRICK_WIDTH + 5)
                    y = 50 + row * (BRICK_HEIGHT + 5)
                    
                    # Higher levels have more durable bricks
                    hits = 1
                    if level >= 3 and random.random() < 0.3:  # 30% chance for 2-hit bricks
                        hits = 2
                    if level >= 5 and random.random() < 0.1:  # 10% chance for 3-hit bricks
                        hits = 3
                    
                    color = colors[(row + level) % len(colors)]  # Cycle through colors
                    self.bricks.append(Brick(x, y, color, hits))
    
    def handle_collisions(self):
        for ball in self.balls[:]:
            if not ball.active:
                continue
            
            # Ball-paddle collision
            if ball.rect.colliderect(self.paddle.rect) and ball.dy > 0:
                ball.dy *= -1
                
                # Adjust ball direction based on where it hits the paddle
                offset = (ball.rect.centerx - self.paddle.rect.centerx) / (self.paddle.width / 2)
                ball.dx = offset * 5  # Max 5 pixels/frame
                
                # If paddle is sticky, stick the ball to it
                if self.paddle.sticky:
                    ball.reset(self.paddle)
                    ball.dx = 0  # Stop horizontal movement until launched
                    self.paddle.sticky = False  # One-time use
            
            # Ball-brick collisions
            for brick in self.bricks[:]:
                if brick.active and ball.rect.colliderect(brick.rect):
                    # Determine collision side
                    if ball.rect.centerx < brick.rect.left or ball.rect.centerx > brick.rect.right:
                        ball.dx *= -1
                    else:
                        ball.dy *= -1
                    
                    # Hit the brick
                    destroyed = brick.hit()
                    if destroyed:
                        self.score += 10 * brick.original_hits
                        
                        # Random chance to drop power-up (20%)
                        if random.random() < 0.2:
                            self.powerups.append(PowerUp(
                                brick.rect.centerx - POWERUP_SIZE // 2,
                                brick.rect.centery - POWERUP_SIZE // 2,
                                random.choice([
                                    POWERUP_EXTEND,
                                    POWERUP_SHRINK,
                                    POWERUP_MULTIBALL,
                                    POWERUP_FAST,
                                    POWERUP_SLOW,
                                    POWERUP_STICKY
                                ])
                            ))
                    
                    break  # Only one brick collision per frame
        
        # Paddle-powerup collisions
        for powerup in self.powerups[:]:
            if powerup.rect.colliderect(self.paddle.rect):
                self.apply_powerup(powerup.type)
                powerup.active = False
        
        # Remove inactive powerups
        self.powerups = [p for p in self.powerups if p.active]
        
        # Remove inactive balls
        self.balls = [b for b in self.balls if b.active]
        
        # Check for level complete
        if all(not brick.active for brick in self.bricks):
            self.level_complete = True
    
    def apply_powerup(self, type):
        if type == POWERUP_EXTEND:
            self.paddle.width = min(self.paddle.width + 20, 150)
            self.paddle.rect.width = self.paddle.width
        elif type == POWERUP_SHRINK:
            self.paddle.width = max(self.paddle.width - 20, 50)
            self.paddle.rect.width = self.paddle.width
        elif type == POWERUP_MULTIBALL:
            # Create 2 new balls
            for _ in range(2):
                new_ball = Ball(self.paddle.rect.centerx, self.paddle.rect.top - BALL_RADIUS)
                new_ball.dx = random.uniform(-5, 5)
                new_ball.dy = -4
                self.balls.append(new_ball)
        elif type == POWERUP_FAST:
            for ball in self.balls:
                ball.dx *= 1.5
                ball.dy *= 1.5
        elif type == POWERUP_SLOW:
            for ball in self.balls:
                ball.dx *= 0.75
                ball.dy *= 0.75
        elif type == POWERUP_STICKY:
            self.paddle.sticky = True
            self.paddle.sticky_timer = pygame.time.get_ticks() + 5000  # 5 seconds
    
    def reset_after_ball_loss(self):
        self.lives -= 1
        if self.lives <= 0:
            self.game_over = True
        else:
            # Reset paddle and create a new ball
            self.paddle = Paddle()
            self.balls = [Ball()]
            self.balls[0].reset(self.paddle)
    
    def next_level(self):
        self.level += 1
        self.paddle = Paddle()
        self.balls = [Ball()]
        self.balls[0].reset(self.paddle)
        self.powerups = []
        self.create_level(self.level)
        self.level_complete = False
    
    def draw(self):
        self.screen.fill(BLACK)
        
        # Draw bricks
        for brick in self.bricks:
            brick.draw(self.screen)
        
        # Draw paddle
        self.paddle.draw(self.screen)
        
        # Draw balls
        for ball in self.balls:
            ball.draw(self.screen)
        
        # Draw powerups
        for powerup in self.powerups:
            powerup.draw(self.screen)
        
        # Draw UI
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        lives_text = self.font.render(f"Lives: {self.lives}", True, WHITE)
        level_text = self.font.render(f"Level: {self.level}", True, WHITE)
        
        self.screen.blit(score_text, (10, 10))
        self.screen.blit(lives_text, (SCREEN_WIDTH - 120, 10))
        self.screen.blit(level_text, (SCREEN_WIDTH // 2 - 50, 10))
        
        # Game over or level complete messages
        if self.game_over:
            game_over_text = self.font.render("GAME OVER", True, RED)
            restart_text = self.small_font.render("Press R to Restart", True, WHITE)
            self.screen.blit(game_over_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50))
            self.screen.blit(restart_text, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 + 10))
        
        if self.level_complete and not self.game_over:
            level_complete_text = self.font.render(f"LEVEL {self.level} COMPLETE!", True, GREEN)
            next_level_text = self.small_font.render("Press N for Next Level", True, WHITE)
            self.screen.blit(level_complete_text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 50))
            self.screen.blit(next_level_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 10))
        
        if self.paused:
            pause_text = self.font.render("PAUSED", True, WHITE)
            self.screen.blit(pause_text, (SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT // 2 - 50))
        
        pygame.display.flip()
    
    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == KEYDOWN:
                    if event.key == K_p:
                        self.paused = not self.paused
                    if event.key == K_r and self.game_over:
                        self.__init__()  # Restart game
                    if event.key == K_n and self.level_complete:
                        self.next_level()
                    if event.key == K_SPACE and any(ball.dx == 0 for ball in self.balls):
                        # Launch any stuck balls
                        for ball in self.balls:
                            if ball.dx == 0:
                                ball.dx = random.choice([-4, 4])
            
            if not self.paused and not self.game_over and not self.level_complete:
                # Update game objects
                self.paddle.update()
                
                for ball in self.balls:
                    ball.update()
                
                for powerup in self.powerups:
                    powerup.update()
                
                # Handle collisions
                self.handle_collisions()
                
                # Check for ball loss
                if not any(ball.active for ball in self.balls):
                    self.reset_after_ball_loss()
            
            self.draw()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()