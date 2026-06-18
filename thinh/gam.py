import pygame
import sys
import random

# ====================== GAME SETUP ======================
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gravity Reborn Runner - Dragon Edition")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 24)
big_font = pygame.font.SysFont("Arial", 48)

# Colors (novel vibe)
BLACK = (10, 10, 20)
VIOLET = (138, 43, 226)
GOLD = (255, 215, 0)
CRIMSON = (220, 20, 60)
WHITE = (255, 255, 255)

# Player class
class Player:
    def __init__(self, char="Minato"):
        self.char = char
        self.x = 100
        self.y = 400
        self.vel_y = 0
        self.on_ground = True
        self.dragon_mode = False
        self.score = 0
        self.distance = 0
        self.attack_cooldown = 0
        self.monsters_defeated = 0

    def update(self):
        self.distance += 3  # auto-run speed
        self.score = int(self.distance // 10)

        if self.dragon_mode:
            self.vel_y = 0  # floating
        else:
            self.vel_y += 0.8  # gravity
            self.y += self.vel_y

        if self.y >= 400:
            self.y = 400
            self.vel_y = 0
            self.on_ground = True

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

    def jump(self):
        if self.on_ground and not self.dragon_mode:
            self.vel_y = -18
            self.on_ground = False
        elif not self.dragon_mode:
            self.dragon_mode = True  # mount dragon!
            self.vel_y = -5

    def slam(self):
        if self.on_ground:
            self.vel_y = 25  # gravity slam

    def attack(self):
        if self.attack_cooldown == 0:
            self.attack_cooldown = 30
            self.monsters_defeated += 1
            return True
        return False

    def draw(self, surf):
        # Body
        color = VIOLET if self.char == "Minato" else GOLD
        pygame.draw.rect(surf, color, (self.x, self.y, 50, 60))  # body
        pygame.draw.circle(surf, WHITE, (self.x + 35, self.y + 15), 12)  # head

        if self.dragon_mode:
            # Dragon wings
            pygame.draw.polygon(surf, CRIMSON, [(self.x + 50, self.y + 30),
                                                (self.x + 90, self.y + 10),
                                                (self.x + 50, self.y + 50)])
            text = font.render("🐉", True, CRIMSON)
            surf.blit(text, (self.x + 70, self.y - 10))

# Monster class
class Monster:
    def __init__(self, distance):
        self.x = WIDTH + random.randint(50, 300)
        self.y = 380
        self.speed = 6
        # Stronger monsters appear later
        if distance > 2000:
            self.type = "Titan"
            self.color = (100, 100, 100)
            self.size = 70
        elif distance > 1000:
            self.type = "Cerberai"
            self.color = CRIMSON
            self.size = 45
        else:
            self.type = "Bloodwolf"
            self.color = (139, 69, 19)
            self.size = 35

    def update(self):
        self.x -= self.speed

    def draw(self, surf):
        pygame.draw.rect(surf, self.color, (self.x, self.y, self.size, self.size))
        label = font.render(self.type[0], True, WHITE)
        surf.blit(label, (self.x + 10, self.y + 5))

# ====================== MAIN GAME ======================
def main():
    player = Player("Minato")  # change to "Aria" after unlock
    monsters = []
    codex_fragments = 0
    spawn_timer = 0
    game_over = False
    unlocked_aria = False  # change to True after 50 fragments in full game

    running = True
    while running:
        dt = clock.tick(60)
        screen.fill(BLACK)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN and not game_over:
                if event.key == pygame.K_SPACE:
                    player.jump()
                if event.key == pygame.K_DOWN:
                    player.slam()
                if event.key == pygame.K_a:  # Attack key
                    if player.attack():
                        # Attack effect
                        pass

        if not game_over:
            player.update()

            # Monster spawning - gets harder the farther you run
            spawn_timer += 1
            spawn_rate = max(25, 80 - (player.distance // 300))  # more monsters later
            if spawn_timer >= spawn_rate:
                monsters.append(Monster(player.distance))
                spawn_timer = 0

            # Update monsters
            for m in monsters[:]:
                m.update()
                if m.x < -50:
                    monsters.remove(m)
                # Collision
                if abs(m.x - player.x) < 50 and abs(m.y - player.y) < 50:
                    if player.dragon_mode and player.attack_cooldown > 0:
                        monsters.remove(m)  # dragon attack kills
                    else:
                        game_over = True

            # Codex fragment chance (increases with distance)
            if random.random() < 0.008 + (player.distance / 100000):
                codex_fragments += 1
                if codex_fragments >= 50 and not unlocked_aria:
                    unlocked_aria = True
                    # In full game this would unlock Aria

            # Draw everything
            player.draw(screen)
            for m in monsters:
                m.draw(screen)

            # HUD
            score_text = font.render(f"Distance: {int(player.distance)}m", True, WHITE)
            screen.blit(score_text, (20, 20))
            frag_text = font.render(f"Codex: {codex_fragments}", True, VIOLET)
            screen.blit(frag_text, (20, 50))
            char_text = font.render(f"Character: {player.char}", True, GOLD)
            screen.blit(char_text, (20, 80))

            # Attack cooldown bar
            if player.attack_cooldown > 0:
                bar = 100 * (player.attack_cooldown / 30)
                pygame.draw.rect(screen, CRIMSON, (player.x, player.y - 20, bar, 8))

            # Dragon mode indicator
            if player.dragon_mode:
                dragon_text = big_font.render("🐉 DRAGON SOAR 🐉", True, CRIMSON)
                screen.blit(dragon_text, (WIDTH//2 - dragon_text.get_width()//2, 20))

            # Simple story pop-up every 800m
            if int(player.distance) % 800 < 10 and player.distance > 100:
                popup = font.render("Yui's fire is getting closer...", True, CRIMSON)
                screen.blit(popup, (WIDTH//2 - popup.get_width()//2, HEIGHT - 50))

        else:
            # Game Over screen
            go_text = big_font.render("CRUSHED BY GRAVITY", True, CRIMSON)
            screen.blit(go_text, (WIDTH//2 - go_text.get_width()//2, 200))
            final = font.render(f"Final Distance: {int(player.distance)}m", True, WHITE)
            screen.blit(final, (WIDTH//2 - final.get_width()//2, 280))
            restart = font.render("Press R to Restart", True, WHITE)
            screen.blit(restart, (WIDTH//2 - restart.get_width()//2, 340))

            if pygame.key.get_pressed()[pygame.K_r]:
                main()  # restart

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()