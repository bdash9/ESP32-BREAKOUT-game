import board
import displayio
from adafruit_display_shapes.rect import Rect
from adafruit_display_text.label import Label
from adafruit_bitmap_font import bitmap_font
import time, random, gc
from digitalio import DigitalInOut, Pull

# Constants
SCL_PIN = board.SCL
SDA_PIN = board.SDA
BUTTON_LEFT_PIN = DigitalInOut(board.A1)  # Left button
BUTTON_RIGHT_PIN = DigitalInOut(board.A2)  # Right button
BUTTON_START_PIN = DigitalInOut(board.A5)  # Start button
BUTTON_LEFT_PIN.switch_to_input(pull=Pull.UP)  # Configure as pull-up input
BUTTON_RIGHT_PIN.switch_to_input(pull=Pull.UP)  # Configure as pull-up input
BUTTON_START_PIN.switch_to_input(pull=Pull.UP)  # Configure as pull-up input

SCREEN_W = 240
SCREEN_H = 135
DELAY = 0.01

BRICK_W = 16
BRICK_H = 8
BRICK_ROW = 4
BRICK_COLOR = 0xFFFFFF

PADDLE_W = 16
PADDLE_H = 4
PADDLE_SPEED = 6
PADDLE_COLOR = 0xFF00FF

BALL_W = 4
BALL_H = 4
BALL_MIN_SPEED = 1
BALL_COLOR = 0xFFFF00

# Initialize display
display = displayio.Group()
board.DISPLAY.show(display)

# Initialize the random seed
seed = 0
for _ in range(1000):
    seed += random.randint(0, 1023)
seed *= 10
random.seed(seed * 10)

gc.enable()

class Brick(Rect):
    def __init__(self, x, y):
        super().__init__(x=x, y=y, width=BRICK_W, height=BRICK_H, fill=BRICK_COLOR)
        if y == BRICK_H * BRICK_ROW + 8:
            self.fill = 0x0000FF  # Medium Blue
        elif y == BRICK_H * (BRICK_ROW - 1) + 8:
            self.fill = 0x00FF00  # Green
        elif y == BRICK_H * (BRICK_ROW - 2) + 8:
            self.fill = 0xFFA500  # Orange
        elif y == BRICK_H * (BRICK_ROW - 3) + 8:
            self.fill = 0xFF0000  # Red


class Paddle(Rect):
    def __init__(self, x, y):
        super().__init__(x=x, y=y, width=PADDLE_W, height=PADDLE_H, fill=PADDLE_COLOR)
        self.speed_x = 0

    def move(self, left_button, right_button):
        if left_button:
            self.speed_x = -PADDLE_SPEED
        elif right_button:
            self.speed_x = PADDLE_SPEED
        else:
            self.speed_x = 0

        new_x = self.x + self.speed_x
        if new_x < 0:
            new_x = 0
        if new_x + self.width >= SCREEN_W:
            new_x = SCREEN_W - self.width - 1

        self.x = new_x

class Ball(Rect):
    def __init__(self, x, y):
        super().__init__(x=x, y=y, width=BALL_W, height=BALL_H, fill=BALL_COLOR)
        self.speed_x = BALL_MIN_SPEED
        self.speed_y = -BALL_MIN_SPEED

    def move(self, paddle):
        self.x += self.speed_x
        self.y += self.speed_y
        if self.x < 0 or self.x + self.width > SCREEN_W:
            self.speed_x = -self.speed_x
        if self.y < 0:
            self.speed_y = -self.speed_y

        if self.isCollidedWith(paddle):
            self.bounceOffPaddle(paddle)

    def bounceOffPaddle(self, paddle):
        if self.speed_y > 0 and self.y + self.height >= paddle.y and paddle.x <= self.x <= paddle.x + paddle.width:
            self.speed_y = -self.speed_y
            self.y = paddle.y - self.height

    def isCollidedWith(self, other):
        return (self.x < other.x + other.width and
                self.x + self.width > other.x and
                self.y < other.y + other.height and
                self.y + self.height > other.y)

    def isFailedToBeCatchedBy(self, paddle):
        return (self.speed_y > 0 and  # Ball is moving downwards
                self.y + self.height > paddle.y and
                (paddle.x <= self.x <= paddle.x + paddle.width or
                 paddle.x <= self.x + self.width <= paddle.x + paddle.width))

    def bounceOffPaddle(self, paddle):
        if self.isFailedToBeCatchedBy(paddle):
            # Reverse the vertical direction of the ball
            self.speed_y = -self.speed_y
            # Center the ball on the paddle
            self.y = paddle.y - self.height


class Score(Label):
    def __init__(self):
        super().__init__(
            font=bitmap_font.load_font("/fonts/Arial-12.bdf"),
            color=0xFFFFFF
        )
        self.x = 0
        self.y = 5

class Game:
    def __init__(self):
        self.bricks = []
        self.paddle = None
        self.ball = None
        self.score = 0
        self.score_show = False
        self.score_label = Score()
        display.append(self.score_label)

    def displayBreakout(self):
        self.displayClear()
        colors = [0xFF0000, 0xFFA500, 0xFFFF00, 0x00FF00, 0x0000FF, 0xFF00FF]
        x = (SCREEN_W - 6 * 12) // 2 - 40
        y = (SCREEN_H - 12) // 2
        for i, letter in enumerate("BREAKOUT"):
            label = Label(
                font=bitmap_font.load_font("/fonts/Arial-Bold-36.bdf"),
                text=letter,
                color=colors[i % len(colors)]
            )
            label.x = x + i * 18  # Adjusted spacing between letters
            label.y = y
            display.append(label)

        # Add the DASH9COMPUTING text at the bottom
        dash_label = Label(
            font=bitmap_font.load_font("/fonts/Arial-12.bdf"),
            text="DASH9COMPUTING",
            color=0xFFFFFF
        )
        dash_label.x = (SCREEN_W - dash_label.width) // 2
        dash_label.y = SCREEN_H - dash_label.height - 5
        display.append(dash_label)

        time.sleep(2)
        self.displayClear()

    def refreshScreen(self):
        # No need to clear the display, as we are directly manipulating the Group
        if self.score_show:
            if self.score_label not in display:
                display.append(self.score_label)

    def displayClear(self):
        # Remove objects from the display Group
        for item in display:
            display.remove(item)

    def displayCenterText(self, text):
        self.displayClear()
        label = Label(font=bitmap_font.load_font("/fonts/Arial-12.bdf"), text=text, color=0xFFFFFF)
        label.x = (SCREEN_W - label.width) // 2
        label.y = SCREEN_H // 2
        display.append(label)

    def resetArcade(self):
        for brick in self.bricks:
            display.remove(brick)
        self.bricks.clear()
        for x in range(0, SCREEN_W, BRICK_W):
            for y in range(BRICK_H * BRICK_ROW + 8, 8, -BRICK_H):  # Modified line
                brick = Brick(x, y)
                display.append(brick)
                self.bricks.append(brick)

        self.paddle = Paddle((SCREEN_W - PADDLE_W) // 3,
                             SCREEN_H - PADDLE_H - 1)
        display.append(self.paddle)
        self.paddle.speed_x = 0

        self.ball = Ball((SCREEN_W - BALL_W) // 2,
                         SCREEN_H - PADDLE_H - BALL_H - 1)
        display.append(self.ball)
        self.ball.speed_x = BALL_MIN_SPEED
        self.ball.speed_y = -BALL_MIN_SPEED
        self.score = 0
        self.score_show = True

game = Game()

while True:
    game.displayBreakout()

    while True:
        if game.score_show:
            game.displayCenterText('PRESS TO START')
        else:
            game.displayClear()
        game.score_show = not game.score_show
        for _ in range(10):
            if not BUTTON_START_PIN.value:
                break
            time.sleep(0.05)
        else:
            continue
        break

    game.displayClear()
    game.resetArcade()

    while True:
        left_button = not BUTTON_LEFT_PIN.value
        right_button = not BUTTON_RIGHT_PIN.value
        game.paddle.move(left_button, right_button)

        for brick in game.bricks:
            if game.ball.isCollidedWith(brick):
                display.remove(brick)
                game.bricks.remove(brick)
                game.score += 1
                game.score_label.text = f'Score: {game.score}'
                break

        game.ball.move(game.paddle)  # Pass the paddle object as an argument
        game.ball.bounceOffPaddle(game.paddle)  # Pass the paddle object as an argument
        game.refreshScreen()

        if game.score == BRICK_ROW * (SCREEN_W // BRICK_W):
            cleared = True
            break

        if game.ball.isFailedToBeCatchedBy(game.paddle):
            cleared = False
            break

        gc.collect()
        time.sleep(DELAY)

    game.displayClear()
    game.refreshScreen()
    time.sleep(0.1)
    game.score_show = True
    game.refreshScreen()

    if cleared:
        time.sleep(1)
        game.displayCenterText('GAME CLEARED')
    else:
        time.sleep(1)
        game.displayCenterText('GAME OVER')

    time.sleep(2)
    game.displayClear()
    time.sleep(3)
    game.score_show = False

