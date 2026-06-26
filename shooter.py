import pygame
import warnings
import random
import os 
import csv

pygame.init() 

SCREEN_WIDTH = 800 
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))  # 800 x 640
pygame.display.set_caption('2DS_Game')

#set frame rate: 
clock = pygame.time.Clock()
FPS = 60

#define player-action-variable
GRAVITY = 0.75
SCROLL_THRESH = 200 
ROWS = 16
COLS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS 
TILE_TYPES = 21
screen_scroll = 0
bg_scroll = 0
level = 1
MAX_LEVELS = 3   #total number of levels (level1, level2, level3 csv)
screen_display_menu = False
screen_display_all_btn = False 

#define action variable: 
moving_left = False 
moving_right = False 
shoot = False
grenade = False
grenade_thrown = False

#load images
pine1_img = pygame.image.load('img/background/pine1.png').convert_alpha()
pine2_img = pygame.image.load('img/background/pine2.png').convert_alpha()
mountian_img = pygame.image.load('img/background/mountain.png').convert_alpha()
sky_img = pygame.image.load('img/background/sky_cloud.png').convert_alpha()
#store tiles in a list
img_list = []
for x in range(TILE_TYPES):
    img = pygame.image.load(f'img/Tile/{x}.png')
    img = pygame.transform.scale(img,(TILE_SIZE,TILE_SIZE))
    img_list.append(img)
#bullet
bullet_img = pygame.image.load('img/icons/selected_by_dev.png').convert_alpha()
#grenade
grenade_img = pygame.image.load('img/icons/grenade.png').convert_alpha()
#pick up boxes
health_box_img = pygame.image.load('img/icons/health_box.png').convert_alpha()
ammo_box_img = pygame.image.load('img/icons/ammo_box.png').convert_alpha()
grenade_box_img = pygame.image.load('img/icons/grenade_box.png').convert_alpha()
item_boxes = {
    'Health'    : health_box_img,
    'Ammo'      : ammo_box_img,
    'Grenade'   : grenade_box_img
}

#define colours 
BG = (144,201,120)
RED = (255,0,0)
WHITE = (255,255,255)
GREEN = (0,255,0)
BLACK = (0,0,0)
#define font 
warnings.filterwarnings("ignore", category=UserWarning, module="pygame.sysfont")
font = pygame.font.SysFont('Futura',30)
def draw_text(text,font,text_col,x,y):
    img = font.render(text,True,text_col)
    screen.blit(img,(x,y)) 

# ─────────────────────────────────────────────────────────────
# LOAD SOUNDS
# pygame.mixer.Sound  → short sound effects (wav)
# pygame.mixer.music  → background music (mp3), loops forever
# ─────────────────────────────────────────────────────────────
jump_fx    = pygame.mixer.Sound('audio/jump.wav')
shot_fx    = pygame.mixer.Sound('audio/shot.wav')
grenade_fx = pygame.mixer.Sound('audio/grenade.wav')

pygame.mixer.music.load('audio/music2.mp3')
pygame.mixer.music.set_volume(0.3)   #background music volume (0.0 – 1.0)
pygame.mixer.music.play(-1)          #-1 means loop forever

# ─────────────────────────────────────────────────────────────
# BUTTON IMAGES  (put start_btn.png / restart_btn.png /
#                 exit_btn.png  inside  img/ )
# ─────────────────────────────────────────────────────────────
start_img   = pygame.image.load('img/start_btn.png').convert_alpha()
restart_img = pygame.image.load('img/restart_btn.png').convert_alpha()
exit_img    = pygame.image.load('img/exit_btn.png').convert_alpha()

# ─────────────────────────────────────────────────────────────
# BUTTON CLASS
# __init__  : store the image and create a rect centred at pos
# draw      : blit the image onto the screen
# is_clicked: return True if the mouse pos is inside the rect
# ─────────────────────────────────────────────────────────────
class Button():
    def __init__(self, image, pos):
        self.image = image
        self.rect  = self.image.get_rect(center=pos)

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

# ─────────────────────────────────────────────────────────────
# GAME STATE FLAG
# start_game = False  → show the START screen before playing
# start_game = True   → game is running (or showing game-over)
# ─────────────────────────────────────────────────────────────
start_game = False

def draw_bg(): 
    screen.fill(BG)
    width = sky_img.get_width()
    for x in range(5):
        screen.blit(sky_img,((x*width)-bg_scroll*0.5,0))
        screen.blit(mountian_img,((x*width)-bg_scroll*0.6,SCREEN_HEIGHT-mountian_img.get_height()-300))
        screen.blit(pine1_img,((x*width)-bg_scroll*0.7,SCREEN_HEIGHT-pine1_img.get_height()-150))
        screen.blit(pine2_img,((x*width)-bg_scroll*0.8,SCREEN_HEIGHT-pine2_img.get_height()))
    

class Soldier(pygame.sprite.Sprite):
    def __init__(self,char_type,x,y,scale,speed,ammo,grenades):
        pygame.sprite.Sprite.__init__(self)
        self.alive = True
        self.char_type = char_type
        self.health = 100 
        self.max_health = self.health
        self.speed = speed
        self.ammo = ammo
        self.start_ammo = ammo 
        self.shoot_cooldown = 0 
        self.grenades = grenades
        self.direction = 1
        self.jump = False
        self.in_air = True
        self.vel_y = 0
        self.flip = False
        self.in_water = False          # <── ADDED
        #style of animation list store than used later: 
        self.animation_list = [] 
        #animation per frame: 
        self.frame_index = 0 
        self.action = 0
        self.update_time = pygame.time.get_ticks()
        #create ai spesfic variables
        self.move_counter = 0 
        self.vision = pygame.Rect(0,0,150,20)
        self.idling = False
        self.idling_counter = 0

        #Load all images for the players
        self.animation_types = ['Idle','Run','Jump','Death']
        for animation in self.animation_types:
            #reset temporary list of images
            # trying to load relevant image into my folder depend on the folder name f to go the dir and find 
            temp_list = [] 
                #count number of files in the folder 
            num_of_frames = len(os.listdir(f'img/{self.char_type}/{animation}'))
            for i in range(num_of_frames):
                self.img = pygame.image.load(f'img/{self.char_type}/{animation}/{i}.png').convert_alpha() 
                img = pygame.transform.scale(
                    self.img,
                    (int(self.img.get_width() * scale), int(self.img.get_height() * scale))
                )
                temp_list.append(img)
            self.animation_list.append(temp_list)

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()   
        self.rect.center = (x,y) 
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        

    def shoot(self):
        if self.shoot_cooldown == 0 and self.ammo > 0:   # check the cooldown
            self.shoot_cooldown = 20   # set cooldown in frames
            bullet = Bullet(
                self.rect.centerx + (0.75 * self.rect.size[0] * self.direction),
                self.rect.centery,
                self.direction
            )
            bullet_group.add(bullet)
            self.ammo -= 1
            shot_fx.play()   #play shot sound every time a bullet is fired

    def ai(self):
        if self.alive and player1.alive:
            if self.idling == False and random.randint(1, 200) == 1:
                self.update_action(0)
                self.idling = True
                self.idling_counter = 50
            else:
                if self.vision.colliderect(player1.rect):
                    # stop and shoot
                    self.update_action(0)
                    self.shoot()
                else:
                    if self.idling == False:
                        if self.direction == 1:
                            ai_moving_right = True
                        else:
                            ai_moving_right = False
                        ai_moving_left = not ai_moving_right
                        self.move(ai_moving_left, ai_moving_right)
                        self.update_action(1)
                        self.move_counter += 1
                        self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)
                        #pygame.draw.rect(screen, RED, self.vision)
                        if self.move_counter > TILE_SIZE:
                            self.direction *= -1
                            self.move_counter *= -1
                    else:
                        self.idling_counter -= 1
                        if self.idling_counter <= 0:
                            self.idling = False
        self.rect.x += screen_scroll

    def update_animation(self):
        ANIMATION_COOLDOWN = 100
        #update image depending current frame:
        self.image = self.animation_list[self.action][self.frame_index]
        #check if enough time has passed since the last update:
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        #if the animation has run out of the images then run back to the previous images:
        if self.frame_index >= len(self.animation_list[self.action]):
            if self.action == 3:
                self.frame_index = len(self.animation_list[self.action]) - 1 
            else:
                self.frame_index = 0 
    
    def update_action(self,new_action): 
        #check if the animation is different from the previous one
        if new_action != self.action:
            self.action = new_action
            #update the animation settings 
            self.frame_index = 0 
            self.update_time = pygame.time.get_ticks()

    def check_alive(self):
        if self.health <= 0: 
            self.health = 0 
            self.speed = 0 
            self.alive = False
            self.update_action(3)
        # INSTANT DEATH when player falls off the screen
        if self.char_type == 'player' and self.rect.top > SCREEN_HEIGHT:
            self.health = 0

    # ─── WATER FLOAT (UPDATED with in_water flag) ───
    def check_water(self):
        if pygame.sprite.spritecollide(self, water_group, False):
            self.vel_y = -6          # upward push; gravity will pull back → bob
            self.in_water = True     # <── ADDED
        else:
            self.in_water = False    # <── ADDED

    def draw(self):
        screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)
        #helps to show player position
        # pygame.draw.rect(screen, RED, self.rect,1)

    def update(self):
        self.update_animation()
        self.check_alive()
        if self.shoot_cooldown:
            self.shoot_cooldown -= 1
        # ─── CALL WATER CHECK FOR PLAYER ONLY ───
        if self.char_type == 'player':
            self.check_water()

            
    def move(self,moving_left,moving_right): 
        #reset movement variables 
        screen_scroll = 0
        dx = 0
        dy = 0

        #goal is simple moving the rectangle and the speed!
        if moving_left: 
            dx =- self.speed
            self.flip = True
            self.direction = -1 
        if moving_right:
            dx = self.speed
            self.flip = False
            self.direction = 1 

        #jump ─── MODIFIED to allow jump in water ───
        if self.jump == True and (self.in_air == False or self.in_water):
            self.vel_y = -14
            self.jump = False 
            self.in_air = True
            jump_fx.play()   #play jump sound when player leaves the ground

        #apply gravity
        self.vel_y += GRAVITY
        if self.vel_y > 10: 
            self.vel_y = 10
        dy += self.vel_y

        #check for collision
        for tile in world.obstacle_list:
            # check x collision
            if tile[1].colliderect(pygame.Rect(self.rect.x + dx, self.rect.y, self.width, self.height)):
                dx = 0
                #if ai hit wall turn around
                if self.char_type == 'enemy':
                    self.direction *= -1
                    self.move_counter = 0
            # check y collision
            if tile[1].colliderect(pygame.Rect(self.rect.x, self.rect.y + dy, self.width, self.height)):
                # jumping up into a tile
                if self.vel_y < 0:
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top
                # falling down onto a tile
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    self.in_air = False
                    dy = tile[1].top - self.rect.bottom

        #check if going off the edges of the screen
        if self.char_type == 'player':
            if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
                dx = 0

        #update rec position(note if put self.rect.y += dx it will move verticle)
        self.rect.x += dx
        self.rect.y += dy
        if self.char_type == 'player':
            if (self.rect.right > SCREEN_WIDTH - SCROLL_THRESH and bg_scroll <(world.level_length*TILE_SIZE)-SCREEN_WIDTH) or \
                (self.rect.left < SCROLL_THRESH and bg_scroll > abs(dx)):
                self.rect.x -= dx
                screen_scroll = -dx
        return screen_scroll

class World():
    def __init__(self):
        self.obstacle_list = []

    def process_data(self,data):
        self.level_length = len(data[0])
        #iterate through each value in the level data file
        global player1, health_bar
        for y,row in enumerate(data):
            for x, tile in enumerate(row):
                if tile >= 0: 
                    img = img_list[tile]
                    img_rect = img.get_rect()
                    img_rect.x = x *TILE_SIZE
                    img_rect.y = y *TILE_SIZE
                    tile_data = (img,img_rect)
                    if tile >= 0 and tile <= 8:
                        self.obstacle_list.append(tile_data)
                    elif tile>= 9 and tile <= 10:
                        water = Water(img, x*TILE_SIZE ,y*TILE_SIZE)
                        water_group.add(water)
                    elif (tile >= 11 and tile < 14) or tile == 14:
                        decoration = Decoration(img, x*TILE_SIZE ,y*TILE_SIZE)
                        decoration_group.add(decoration)
                    elif tile == 15:
                        player1 = Soldier('player', x*TILE_SIZE , y*TILE_SIZE, 1.65, 4, 10, 5)
                        health_bar = HealthBar(100, 10, player1.health, player1.max_health)
                    elif tile == 16:
                        enemy = Soldier('enemy', x*TILE_SIZE, y*TILE_SIZE, 1.65, 2, 20, 0)
                        enemy_group.add(enemy)
                    elif tile == 17: #create ammo boxes
                        item_box = ItemBox('Ammo', x*TILE_SIZE ,y*TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 18:
                        item_box = ItemBox('Grenade',  x*TILE_SIZE ,y*TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 19:
                        item_box = ItemBox('Health', x*TILE_SIZE ,y*TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 20:
                        exit = Exit(img, x*TILE_SIZE ,y*TILE_SIZE)
                        exit_group.add(exit)
        return player1,health_bar
    
    def draw(self):
        for tile in self.obstacle_list:
            tile[1][0] += screen_scroll
            screen.blit(tile[0],tile[1])
            


class Decoration(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))
    def update(self):
        self.rect.x += screen_scroll

class Water(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))
    def update(self):
        self.rect.x += screen_scroll

class Exit(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))
    def update(self):
        self.rect.x += screen_scroll

class ItemBox(pygame.sprite.Sprite):
    def __init__(self, item_type, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.item_type = item_type
        self.image = item_boxes[self.item_type]
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))
    def update(self):
        #scroll
        self.rect.x += screen_scroll
        #check player picked boxed 
        #text convert to images second goal 
        if pygame.sprite.collide_rect(self,player1): 
            #check what kind of boxes it was 
            if self.item_type == 'Health': 
                player1.health += 35
                if player1.health > player1.max_health:
                  player1.health = player1.max_health 
            elif self.item_type == 'Ammo': 
                player1.ammo += 15
            elif self.item_type == 'Grenade':
                player1.grenades += 3 
            #delete the item boxes
            self.kill()
    
class HealthBar():
    def __init__(self,x,y,health,max_health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health
    def draw(self,health): 
        #update with new health 
        self.health = health 
        #calculate health ratio
        ratio = self.health/self.max_health
        #Health Bar label 
        draw_text('HP BAR:', font, WHITE, 10, self.y + 1)
        pygame.draw.rect(screen, BLACK, (self.x-2,self.y-2,154,24))
        pygame.draw.rect(screen, RED, (self.x,self.y,150,20))
        pygame.draw.rect(screen,GREEN,(self.x,self.y,150 * ratio ,20 ))
            
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 10
        self.image = bullet_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction

    def update(self):
        # 1. Move the bullet
        self.rect.x += (self.direction * self.speed) + screen_scroll

        # 2. Collision with level tiles – check every frame
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                self.kill()
                return   # stop further checks for this bullet

        # 3. Off‑screen removal (only if still alive)
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()
            return

        # 4. Collision with player
        if pygame.sprite.spritecollide(player1, bullet_group, False):
            if player1.alive:
                player1.health -= 5
                self.kill()
                return

        # 5. Collision with enemies
        for enemy in enemy_group:
            if pygame.sprite.spritecollide(enemy, bullet_group, False):
                if enemy.alive:
                    enemy.health -= 25
                    self.kill()
                    return

class Grenade(pygame.sprite.Sprite):
    def __init__(self, x,y,direction):
        pygame.sprite.Sprite.__init__(self)
        self.timer = 100
        self.vel_y = -11
        self.speed = 7
        self.image = grenade_img
        self.rect = self.image.get_rect()
        self.rect.center = (x,y)
        self.direction = direction
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def update(self):
        self.vel_y += GRAVITY
        dx = self.direction * self.speed
        dy = self.vel_y
        for tile in world.obstacle_list:
            #check collision wall
            if tile[1].colliderect(self.rect.x+dx,self.rect.y,self.width,self.height): 
            #inverse order 
                self.direction *= -1 
                dx = self.direction * self.speed
        #check rectangle position it a wall that you can hit it or walk on it 
        # check y collision
            if tile[1].colliderect(pygame.Rect(self.rect.x, self.rect.y + dy, self.width, self.height)):
                # check thrown up
                self.speed = 0
                if self.vel_y < 0:
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top
                # falling down onto a tile
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    dy = tile[1].top - self.rect.bottom

        #update grenade position
        self.rect.x += dx + screen_scroll
        self.rect.y += dy

        #countdown timer
        self.timer -= 1
        if self.timer <= 0:
            self.kill()
            explosion = Explosion(self.rect.x, self.rect.y, 0.5)
            explosion_group.add(explosion)
            grenade_fx.play()   #play grenade sound when it explodes
            # do damage to anyone that is nearby 
            #scale world map
            if abs(self.rect.centerx - player1.rect.centerx) < TILE_SIZE * 2 and \
            abs(self.rect.centery - player1.rect.centery) < TILE_SIZE * 2:
                player1.health -= 50

            for enemy in enemy_group:
                if abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE * 2 and \
                abs(self.rect.centery - enemy.rect.centery) < TILE_SIZE * 2:
                    enemy.health -= 50
                    

class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, scale):
        pygame.sprite.Sprite.__init__(self)          
        self.images = []                             
        for num in range(1, 6):
            img = pygame.image.load(f'img/explosion/exp{num}.png').convert_alpha()   
            # fixed: scale takes exactly a tuple, no extra arguments
            img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
            self.images.append(img)
        self.frame_index = 0
        self.image = self.images[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)                    
        self.counter = 0
        #ensure explosion won't stuck in place 
    def update(self):
        self.rect.x += screen_scroll
        EXPLOSION_SPEED = 4
        #update explosion animation
        self.counter += 1 

        if self.counter >= EXPLOSION_SPEED:
            self.counter = 0 
            self.frame_index += 1
            #if the animation is complete then delete the explosion
            if self.frame_index >= len(self.images):
                self.kill()
            else:
                self.image = self.images[self.frame_index]


#create sprite groups 
enemy_group = pygame.sprite.Group()   
bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()   
exit_group = pygame.sprite.Group()   
water_group = pygame.sprite.Group()   
decoration_group = pygame.sprite.Group()

# ─────────────────────────────────────────────────────────────
# CREATE BUTTON OBJECTS
# each Button needs: image + centre position (x, y)
# ─────────────────────────────────────────────────────────────
start_btn   = Button(start_img,   (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
restart_btn = Button(restart_img, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
exit_btn    = Button(exit_img,    (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))

#create empty tile list 
world_data = []
for row in range(ROWS):
    r = [-1] * COLS
    world_data.append(r)
#load in level data and create world
with open(f'level{level}_data.csv',newline='')as csvfile:
    reader = csv.reader(csvfile,delimiter=',')
    for x,row in enumerate(reader): 
        for y,tile in enumerate(row):
            world_data[x][y] = int(tile)
world = World()
player1,health_bar =world.process_data(world_data)



run = True
while run:
    clock.tick(FPS)
    #get mouse position every frame (needed for button click checks)
    mouse_pos = pygame.mouse.get_pos()

    # ─────────────────────────────────────────────────────────
    # START SCREEN
    # if start_game is False, show background + START button
    # the game will NOT run until the player clicks START
    # ─────────────────────────────────────────────────────────
    if not start_game:
        draw_bg()
        start_btn.draw(screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_btn.is_clicked(mouse_pos):
                    start_game = True   #← flip flag, enter game loop

        pygame.display.update()
        continue   # skip everything below until START is clicked

    # ─────────────────────────────────────────────────────────
    # MAIN GAME (runs only after START is clicked)
    # ─────────────────────────────────────────────────────────

    #draw background:
    draw_bg()
    #draw world map:
    world.draw()
    #show health bar: 
    health_bar.draw(player1.health)
    #show ammo:
    draw_text('AMMO: ',font,WHITE,10,35) 
    for x in range(player1.ammo):
        screen.blit(bullet_img,(90 + (x * 10),40))
    #show grenade:
    draw_text('GRENADE: ',font,WHITE,10,60)
    for x in range(player1.grenades):
        screen.blit(grenade_img,(135 + (x * 15),60)) 
    #animation running created: 
    player1.update()
    #player class create:
    player1.draw()
    #enemy class create: 
    for enemy in enemy_group:
        enemy.ai()
        enemy.draw() 
        enemy.update()
    #bullet and draw group 
    bullet_group.update()
    bullet_group.draw(screen) 
    #grenade group: 
    grenade_group.update()
    grenade_group.draw(screen)
    #animation explosion groups:
    explosion_group.draw(screen)
    explosion_group.update()
    #item box groups:
    item_box_group.update()
    item_box_group.draw(screen)
    #enivorement groups
    exit_group.update()   
    exit_group.draw(screen)
    water_group.update()
    water_group.draw(screen)
    decoration_group.update()
    decoration_group.draw(screen)

    # ─────────────────────────────────────────────────────────
    # LEVEL TRANSITION
    # if player touches the exit tile → go to next level
    # clear all groups, increment level, reload the new csv
    # ─────────────────────────────────────────────────────────
    if pygame.sprite.spritecollide(player1, exit_group, False):
        if level < MAX_LEVELS:
            level += 1   #increment to next level
            #clear all sprite groups
            enemy_group.empty()
            bullet_group.empty()
            grenade_group.empty()
            explosion_group.empty()
            item_box_group.empty()
            exit_group.empty()
            water_group.empty()
            decoration_group.empty()
            #reload world data from the new level csv
            world_data = []
            for row in range(ROWS):
                r = [-1] * COLS
                world_data.append(r)
            with open(f'level{level}_data.csv', newline='') as csvfile:
                reader = csv.reader(csvfile, delimiter=',')
                for rx, rrow in enumerate(reader):
                    for ry, tile in enumerate(rrow):
                        world_data[rx][ry] = int(tile)
            #re-create world and player at new level
            world.__init__()
            player1, health_bar = world.process_data(world_data)
            #reset scroll
            bg_scroll     = 0
            screen_scroll = 0
        

    #update player action
    if player1.alive:
        #shoot bullet
        if shoot: 
            player1.shoot()
        #throw grenade
        elif grenade and grenade_thrown == False and player1.grenades > 0:
            grenade = Grenade(player1.rect.centerx+ (0.5 * player1.rect.size[0] * player1.direction) ,\
                              player1.rect.top,player1.direction)
            grenade_group.add(grenade)
            #reduce grenades 
            player1.grenades -= 1 
            grenade_thrown = True 
            grenade_fx.play()   #play grenade sound when thrown
            
        if player1.in_air:
            player1.update_action(2) #(jump)
        elif moving_left or moving_right:
            player1.update_action(1) #(run)
        else:
            player1.update_action(0) #(idle)
        screen_scroll=player1.move(moving_left,moving_right) 
        bg_scroll -= screen_scroll
    else:
        # ─────────────────────────────────────────────────────
        # GAME OVER SCREEN
        # player is dead → stop movement, show RESTART + EXIT
        # ─────────────────────────────────────────────────────
        screen_scroll = 0
        restart_btn.draw(screen)
        exit_btn.draw(screen)

    for event in pygame.event.get(): 
        if event.type == pygame.QUIT: 
            run = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            # ─────────────────────────────────────────────────
            # RESTART button: clear all groups, reload level
            # EXIT button: close the game
            # ─────────────────────────────────────────────────
            if not player1.alive:
                if restart_btn.is_clicked(mouse_pos):
                    #clear all sprite groups
                    enemy_group.empty()
                    bullet_group.empty()
                    grenade_group.empty()
                    explosion_group.empty()
                    item_box_group.empty()
                    exit_group.empty()
                    water_group.empty()
                    decoration_group.empty()
                    #rebuild world data from csv
                    world_data = []
                    for row in range(ROWS):
                        r = [-1] * COLS
                        world_data.append(r)
                    with open(f'level{level}_data.csv', newline='') as csvfile:
                        reader = csv.reader(csvfile, delimiter=',')
                        for rx, rrow in enumerate(reader):
                            for ry, tile in enumerate(rrow):
                                world_data[rx][ry] = int(tile)
                    #re-create world and player
                    world.__init__()
                    player1, health_bar = world.process_data(world_data)
                    #reset scroll and action flags
                    bg_scroll      = 0
                    screen_scroll  = 0
                    moving_left    = False
                    moving_right   = False
                    shoot          = False
                    grenade        = False
                    grenade_thrown = False

                elif exit_btn.is_clicked(mouse_pos):
                    run = False

            #key press
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a or event.key == pygame.K_LEFT: 
                moving_left = True
            if event.key == pygame.K_d  or event.key == pygame.K_RIGHT: 
                moving_right = True
            if event.key == pygame.K_SPACE: 
                shoot = True
            if event.key == pygame.K_q: 
                grenade = True
            if (event.key == pygame.K_w and player1.alive)  or (event.key == pygame.K_UP and player1.alive ) :
                player1.jump = True
            if event.key == pygame.K_ESCAPE: 
                run = False

        #Key button released 
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a or event.key == pygame.K_LEFT: 
                moving_left = False
            if event.key == pygame.K_d or event.key == pygame.K_RIGHT: 
                moving_right = False
            if event.key == pygame.K_SPACE: 
                shoot = False
            if event.key == pygame.K_q: 
                grenade = False
                grenade_thrown = False

    pygame.display.update()
pygame.quit()