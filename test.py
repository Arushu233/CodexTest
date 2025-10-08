import math
import random
import sys
from dataclasses import dataclass
from typing import List, Tuple

import pygame

# Constants for the game configuration
WINDOW_WIDTH = 720
WINDOW_HEIGHT = 540
GRID_SIZE = 24
GRID_WIDTH = WINDOW_WIDTH // GRID_SIZE
GRID_HEIGHT = WINDOW_HEIGHT // GRID_SIZE
FPS = 12

# Colors
BG_TOP = (30, 30, 40)
BG_BOTTOM = (15, 15, 25)
GRID_COLOR = (45, 45, 60)
SNAKE_HEAD_COLOR = (102, 252, 241)
SNAKE_BODY_COLOR = (56, 176, 222)
FOOD_COLOR = (255, 99, 132)
TEXT_COLOR = (236, 240, 241)
SHADOW_COLOR = (0, 0, 0)
BUTTON_BG = (64, 74, 92)
BUTTON_HOVER = (102, 252, 241)
OVERLAY_COLOR = (10, 10, 10, 160)

# Directions represented as vectors
DIRECTIONS = {
    pygame.K_UP: (0, -1),
    pygame.K_DOWN: (0, 1),
    pygame.K_LEFT: (-1, 0),
    pygame.K_RIGHT: (1, 0),
}


@dataclass
class SnakeSegment:
    x: int
    y: int

    @property
    def position(self) -> Tuple[int, int]:
        return self.x, self.y


class Button:
    """Simple button with hover feedback for better UX."""

    def __init__(self, text: str, font: pygame.font.Font, center: Tuple[int, int]):
        self.text = text
        self.font = font
        self.center = center
        self.padding = pygame.Vector2(28, 12)
        self.rect = pygame.Rect(0, 0, 0, 0)

    def draw(self, surface: pygame.Surface, hovered: bool) -> None:
        label = self.font.render(self.text, True, TEXT_COLOR)
        self.rect = label.get_rect()
        self.rect.inflate_ip(self.padding.x, self.padding.y)
        self.rect.center = self.center

        bg_color = BUTTON_HOVER if hovered else BUTTON_BG
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=16)
        surface.blit(label, label.get_rect(center=self.center))

    def is_hovered(self, mouse_pos: Tuple[int, int]) -> bool:
        return self.rect.collidepoint(mouse_pos)


class SnakeGame:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Serpent Sprint")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self.title_font = pygame.font.SysFont("Poppins", 64, bold=True)
        self.large_font = pygame.font.SysFont("Poppins", 36)
        self.medium_font = pygame.font.SysFont("Poppins", 28)
        self.small_font = pygame.font.SysFont("Poppins", 20)

        self.state = "menu"
        self.direction = pygame.Vector2(1, 0)
        self.pending_direction = self.direction
        self.snake: List[SnakeSegment] = []
        self.food = SnakeSegment(0, 0)
        self.score = 0
        self.best_score = 0

        self.start_button = Button("Tap Space to Start", self.medium_font, (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 120))
        self.reset()

    # ------------------------------------------------------------------
    # Game setup helpers
    # ------------------------------------------------------------------
    def reset(self) -> None:
        center_x = GRID_WIDTH // 2
        center_y = GRID_HEIGHT // 2
        self.snake = [
            SnakeSegment(center_x, center_y),
            SnakeSegment(center_x - 1, center_y),
            SnakeSegment(center_x - 2, center_y),
        ]
        self.direction = pygame.Vector2(1, 0)
        self.pending_direction = self.direction
        self.score = 0
        self.spawn_food()

    def spawn_food(self) -> None:
        positions = {segment.position for segment in self.snake}
        while True:
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)
            if (x, y) not in positions:
                self.food = SnakeSegment(x, y)
                break

    # ------------------------------------------------------------------
    # Drawing routines
    # ------------------------------------------------------------------
    def draw_gradient_background(self) -> None:
        for y in range(WINDOW_HEIGHT):
            ratio = y / WINDOW_HEIGHT
            r = BG_TOP[0] * (1 - ratio) + BG_BOTTOM[0] * ratio
            g = BG_TOP[1] * (1 - ratio) + BG_BOTTOM[1] * ratio
            b = BG_TOP[2] * (1 - ratio) + BG_BOTTOM[2] * ratio
            pygame.draw.line(self.screen, (int(r), int(g), int(b)), (0, y), (WINDOW_WIDTH, y))

    def draw_grid(self) -> None:
        for x in range(0, WINDOW_WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR, (x, 0), (x, WINDOW_HEIGHT))
        for y in range(0, WINDOW_HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y), (WINDOW_WIDTH, y))

    def draw_snake(self) -> None:
        for index, segment in enumerate(self.snake):
            rect = pygame.Rect(segment.x * GRID_SIZE, segment.y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            color = SNAKE_HEAD_COLOR if index == 0 else SNAKE_BODY_COLOR
            radius = GRID_SIZE // 3 if index == 0 else GRID_SIZE // 5
            pygame.draw.rect(self.screen, color, rect.inflate(-4, -4), border_radius=radius)

    def draw_food(self) -> None:
        rect = pygame.Rect(self.food.x * GRID_SIZE, self.food.y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
        pygame.draw.rect(self.screen, FOOD_COLOR, rect.inflate(-6, -6), border_radius=GRID_SIZE // 3)

    def draw_scoreboard(self) -> None:
        score_text = f"Score: {self.score}"
        best_text = f"Best: {self.best_score}"
        self.draw_shadow_text(score_text, self.medium_font, (20, 16))
        self.draw_shadow_text(best_text, self.medium_font, (WINDOW_WIDTH - 20, 16), align_right=True)

    def draw_shadow_text(
        self,
        text: str,
        font: pygame.font.Font,
        position: Tuple[int, int],
        align_right: bool = False,
        center: bool = False,
    ) -> None:
        label = font.render(text, True, TEXT_COLOR)
        shadow = font.render(text, True, SHADOW_COLOR)

        label_rect = label.get_rect()
        if center:
            label_rect.center = position
        elif align_right:
            label_rect.topright = position
        else:
            label_rect.topleft = position

        shadow_rect = label_rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 2
        self.screen.blit(shadow, shadow_rect)
        self.screen.blit(label, label_rect)

    def draw_overlay(self, text: str, subtitle: str) -> None:
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill(OVERLAY_COLOR)
        self.screen.blit(overlay, (0, 0))

        self.draw_shadow_text(text, self.title_font, (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 60), center=True)
        self.draw_shadow_text(subtitle, self.medium_font, (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 10), center=True)
        self.draw_shadow_text("Press Enter to restart", self.small_font, (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 70), center=True)

    # ------------------------------------------------------------------
    # Event handling and game logic
    # ------------------------------------------------------------------
    def handle_direction_change(self, key: int) -> None:
        if key not in DIRECTIONS:
            return
        new_direction = pygame.Vector2(DIRECTIONS[key])
        if new_direction + self.direction == pygame.Vector2():
            return
        self.pending_direction = new_direction

    def update_snake(self) -> None:
        self.direction = self.pending_direction
        new_head = SnakeSegment(
            self.snake[0].x + int(self.direction.x),
            self.snake[0].y + int(self.direction.y),
        )

        # Collision with boundaries
        if not (0 <= new_head.x < GRID_WIDTH) or not (0 <= new_head.y < GRID_HEIGHT):
            self.trigger_game_over()
            return

        # Collision with itself
        if any(segment.position == new_head.position for segment in self.snake):
            self.trigger_game_over()
            return

        self.snake.insert(0, new_head)

        if new_head.position == self.food.position:
            self.score += 10
            self.spawn_food()
            self.best_score = max(self.best_score, self.score)
        else:
            self.snake.pop()

    def trigger_game_over(self) -> None:
        self.state = "game_over"
        self.best_score = max(self.best_score, self.score)

    # ------------------------------------------------------------------
    # Screens
    # ------------------------------------------------------------------
    def draw_menu(self) -> None:
        self.draw_gradient_background()
        self.draw_grid()
        self.draw_shadow_text("Serpent Sprint", self.title_font, (WINDOW_WIDTH // 2, 120), center=True)
        instructions = [
            "Use arrow keys or WASD to glide.",
            "Collect neon bites to grow.",
            "Press Space to pause mid-run.",
        ]
        for index, line in enumerate(instructions):
            self.draw_shadow_text(line, self.medium_font, (WINDOW_WIDTH // 2, 220 + index * 40), center=True)

        mouse_pos = pygame.mouse.get_pos()
        hovered = self.start_button.is_hovered(mouse_pos)
        self.start_button.draw(self.screen, hovered)

    def draw_gameplay(self) -> None:
        self.draw_gradient_background()
        self.draw_grid()
        self.draw_snake()
        self.draw_food()
        self.draw_scoreboard()

    def draw_pause(self) -> None:
        self.draw_gameplay()
        self.draw_overlay("Paused", "Take a breath, racer!")

    def draw_game_over(self) -> None:
        self.draw_gameplay()
        subtitle = f"Final score: {self.score}"
        self.draw_overlay("Game Over", subtitle)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self) -> None:
        while self.running:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_keydown(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN and self.state == "menu":
                    if self.start_button.is_hovered(event.pos):
                        self.state = "playing"

            if self.state == "playing":
                self.update_snake()

            if self.state == "menu":
                self.draw_menu()
            elif self.state == "playing":
                self.draw_gameplay()
            elif self.state == "paused":
                self.draw_pause()
            elif self.state == "game_over":
                self.draw_game_over()

            pygame.display.flip()

        pygame.quit()
        sys.exit()

    def handle_keydown(self, key: int) -> None:
        if key in (pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d):
            key_mapping = {
                pygame.K_w: pygame.K_UP,
                pygame.K_s: pygame.K_DOWN,
                pygame.K_a: pygame.K_LEFT,
                pygame.K_d: pygame.K_RIGHT,
            }
            key = key_mapping[key]

        if self.state == "menu":
            if key in (pygame.K_SPACE, pygame.K_RETURN):
                self.state = "playing"
        elif self.state == "playing":
            if key == pygame.K_SPACE:
                self.state = "paused"
            else:
                self.handle_direction_change(key)
        elif self.state == "paused":
            if key == pygame.K_SPACE:
                self.state = "playing"
            elif key == pygame.K_ESCAPE:
                self.state = "menu"
                self.reset()
        elif self.state == "game_over":
            if key == pygame.K_RETURN:
                self.reset()
                self.state = "playing"
            elif key == pygame.K_ESCAPE:
                self.state = "menu"
                self.reset()


if __name__ == "__main__":
    SnakeGame().run()
