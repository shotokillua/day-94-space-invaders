import pygame
import os
import time
import random
pygame.font.init()


WIDTH, HEIGHT = 750, 750
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Space Invader')

# Load images
RED_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_red_small.png"))
GREEN_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_green_small.png"))
BLUE_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_blue_small.png"))
# Player ship
YELLOW_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_yellow.png"))

# Lasers
RED_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_red.png"))
GREEN_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_green.png"))
BLUE_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_blue.png"))
YELLOW_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_yellow.png"))

# Background
BG = pygame.transform.scale(pygame.image.load(os.path.join("assets", "background-black.png")), (WIDTH, HEIGHT)) # scaled the bg image to the width and height of the window

class Laser:
    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))

    def move(self, velocity):
        self.y += velocity

    def off_screen(self, height):
        return not(self.y < height and self.y >= 0) # returns True if self object is within the screen, otherwise False

    def collision(self, obj):
        return collide(self, obj)

class Ship:
    COOLDOWN = 20
    def __init__(self, x, y, health=100):
        self.x = x
        self.y = y
        self.health = health
        self.ship_img = None # variable listed as None in the class for now but when we make an instance of the class, we will define the images so we can use them
        self.laser_img = None
        self.lasers = []
        self.cool_down_counter = 0 # create a countdown so you cant just spam lasers

    def draw(self, window):
        window.blit(self.ship_img, (self.x, self.y))
        for laser in self.lasers:
            laser.draw(window)

    def move_lasers(self, velocity, obj):
        self.cooldown()
        for laser in self.lasers:
            laser.move(velocity)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            elif laser.collision(obj):
                obj.health -= 10
                self.lasers.remove(laser) # remove the laser so the same laser can't proceed to hit object multiple times



    def cooldown(self): # chatGPT this, confusing
        if self.cool_down_counter >= self.COOLDOWN:
            self.cool_down_counter = 0
        elif self.cool_down_counter > 0:
            self.cool_down_counter += 1


    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1

    def get_width(self):
        return self.ship_img.get_width()

    def get_height(self):
        return self.ship_img.get_height()

class Player(Ship):
    def __init__(self, x, y, health=100):
        super().__init__(x, y, health)
        self.ship_img = YELLOW_SPACE_SHIP
        self.laser_img = YELLOW_LASER
        self.mask = pygame.mask.from_surface(self.ship_img) # mask allows for pixel perfect collisions so a collision w/blank pixels don't count (has to make contact)
        self.max_health = health

    def move_lasers(self, velocity, objs):
        self.cooldown()
        for laser in self.lasers:
            laser.move(velocity)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            else:
                for obj in objs:
                    if laser.collision(obj):
                        objs.remove(obj)
                        if laser in self.lasers:
                            self.lasers.remove(laser) # remove the laser so the same laser can't proceed to hit object multiple times
    def draw(self, window):
        super().draw(window) # inherit draw method from parent class Ship
        self.healthbar(window)

    def healthbar(self, window):
        pygame.draw.rect(window, (255, 0, 0), (self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width(), 10))
        pygame.draw.rect(window, (0, 255, 0), (self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width() * (self.health/self.max_health), 10))

class Enemy(Ship):
    COLOR_MAP = {
        "red": (RED_SPACE_SHIP, RED_LASER),
        "blue": (BLUE_SPACE_SHIP, BLUE_LASER),
        "green": (GREEN_SPACE_SHIP, GREEN_LASER)
    }

    def __init__(self, x, y, color, health=100):
        super().__init__(x, y, health)
        self.ship_img, self.laser_img = self.COLOR_MAP[color] # genius, passes color argument to COLOR_MAP dictionary to define the ship_img and laser_img
        self.mask = pygame.mask.from_surface(self.ship_img)

    def move(self, velocity):
        self.y += velocity

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x-20, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1

def collide(obj1, obj2):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) != None # return if the mask of obj1 is overlapping the mask of obj2 within the offset /intersection area (True/False)

def main():
    run = True
    FPS = 60
    level = 0
    lives = 5
    main_font = pygame.font.SysFont("comicsans", 50) # must initialize font and create a font object before you render text on the screen
    lost_font = pygame.font.SysFont("comicsans", 60)

    player_velocity = 5
    laser_velocity = 5
    player = Player(300, 630)

    clock = pygame.time.Clock()

    enemies = []
    wave_length = 5
    enemy_velocity = 1

    lost = False
    lost_count = 0

    def redraw_window():
        WINDOW.blit(BG, (0, 0)) # WINDOW is a surface, blit takes a pygame image and draws it to the surface at the specified coordinate system (0, 0) is top left hand corner
        # draw text
        lives_label = main_font.render(f"Lives: {lives}", 1, (255, 255, 255)) # create label with text, antialias (always 1) and color in RGB code, THEN BLIT to the label
        level_label = main_font.render(f"Level: {level}", 1, (255, 255, 255))

        WINDOW.blit(lives_label, (10, 10))
        WINDOW.blit(level_label, (WIDTH - level_label.get_width() - 10, 10)) # do math to get the label to sit on the upper right hand corner, spaced from the edge

        for enemy in enemies:
            enemy.draw(WINDOW)

        player.draw(WINDOW)

        if lost:
            lost_label = lost_font.render("You Lost!!", 1, (255, 255, 255))
            WINDOW.blit(lost_label, (WIDTH/2 - lost_label.get_width()/2, 350))

        pygame.display.update() # in this case blit is drawing the BG onto the surface at (0, 0)


    while run:
        clock.tick(FPS) # speed of game is consistent on any device, 60 FPS
        redraw_window()

        if lives <= 0 or player.health <= 0:
            lost = True
            lost_count += 1

        if lost:
            if lost_count > FPS * 3: # if the lost_label has been showing for more than 3 seconds...
                run = False          # then quit the game
            else:
                continue             # otherwise, "continue" which means go back to the top of the while loop and keep running


        if len(enemies) == 0:
            level += 1
            wave_length += 5
            for i in range(wave_length):
                enemy = Enemy(random.randrange(50, WIDTH - 100), random.randrange(-1500, -100), random.choice(["red", "blue", "green"])) # x position, y position, color
                enemies.append(enemy)


        for event in pygame.event.get(): # check for events
            if event.type == pygame.QUIT: # if user has quit the game....
                quit()              # stop running

        keys = pygame.key.get_pressed()
        if (keys[pygame.K_a] or keys[pygame.K_LEFT]) and player.x - player_velocity > 0: # move left
            player.x -= player_velocity
        if (keys[pygame.K_d] or keys[pygame.K_RIGHT]) and player.x + player_velocity + player.get_width() < WIDTH: # move right
            player.x += player_velocity
        if (keys[pygame.K_s] or keys[pygame.K_DOWN]) and player.y - player_velocity + player.get_height() < HEIGHT: # move down
            player.y += player_velocity
        if (keys[pygame.K_w] or keys[pygame.K_UP]) and player.y + player_velocity > 0: # move up
            player.y -= player_velocity
        if keys[pygame.K_SPACE]:
            player.shoot()

        for enemy in enemies[:]:
            enemy.move(enemy_velocity)
            enemy.move_lasers(laser_velocity, player)

            if random.randrange(0, 2*60) == 1:
                enemy.shoot()

            if collide(enemy, player):
                player.health -= 10
                enemies.remove(enemy)

            elif enemy.y + enemy.get_height() > HEIGHT:
                lives -= 1
                enemies.remove(enemy)

        player.move_lasers(-laser_velocity, enemies)

def main_menu():
    title_font = pygame.font.SysFont("comicsans", 50)

    run = True
    while run:
        WINDOW.blit(BG, (0, 0))
        title_label = title_font.render("Press the mouse to begin....", 1, (255, 255, 255))
        WINDOW.blit(title_label, (WIDTH / 2 - title_label.get_width() / 2, 350))

        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                main()

    pygame.quit()
main_menu()