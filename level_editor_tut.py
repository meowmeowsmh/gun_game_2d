import pygame
import button
import csv
import pickle
import os   # for file existence check

pygame.init()

clock = pygame.time.Clock()
FPS = 60

#game window
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 640
LOWER_MARGIN = 100
SIDE_MARGIN = 300

screen = pygame.display.set_mode((SCREEN_WIDTH + SIDE_MARGIN, SCREEN_HEIGHT + LOWER_MARGIN))
pygame.display.set_caption('Level Editor')


#define game variables
ROWS = 16
MAX_COLS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 21
level = 0
current_tile = 0
scroll_left = False
scroll_right = False
scroll = 0
scroll_speed = 1


#load images
pine1_img = pygame.image.load('img/Background/pine1.png').convert_alpha()
pine2_img = pygame.image.load('img/Background/pine2.png').convert_alpha()
mountain_img = pygame.image.load('img/Background/mountain.png').convert_alpha()
sky_img = pygame.image.load('img/Background/sky_cloud.png').convert_alpha()
#store tiles in a list
img_list = []
for x in range(TILE_TYPES):
    img = pygame.image.load(f'img/tile/{x}.png').convert_alpha()
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    img_list.append(img)

save_img = pygame.image.load('img/save_btn.png').convert_alpha()
load_img = pygame.image.load('img/load_btn.png').convert_alpha()

# --- Create a "Clear" button from a text surface (no extra image needed) ---
clear_font = pygame.font.SysFont(['futura', 'arial', 'helvetica', 'sans-serif'], 24)
clear_text = clear_font.render('Clear', True, (255, 255, 255))
clear_bg = pygame.Surface((clear_text.get_width() + 20, clear_text.get_height() + 10))
clear_bg.fill((200, 50, 50))
clear_bg.blit(clear_text, (10, 5))
clear_img = clear_bg.convert_alpha()

#define colours
GREEN = (144, 201, 120)
WHITE = (255, 255, 255)
RED = (200, 25, 25)
BLACK = (0, 0, 0)

#define font
font = pygame.font.SysFont(['futura', 'arial', 'helvetica', 'sans-serif'], 30)

#create empty tile list
world_data = []
for row in range(ROWS):
    r = [-1] * MAX_COLS
    world_data.append(r)

#create ground
for tile in range(0, MAX_COLS):
    world_data[ROWS - 1][tile] = 0


# --- Status message variables (for feedback) ---
message = ""
message_timer = 0

def set_message(text, duration=120):  # duration in frames (2 sec at 60 FPS)
    global message, message_timer
    message = text
    message_timer = duration

#function for outputting text onto the screen
def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))


#create function for drawing background
def draw_bg():
    screen.fill(GREEN)
    width = sky_img.get_width()
    for x in range(4):
        screen.blit(sky_img, ((x * width) - scroll * 0.5, 0))
        screen.blit(mountain_img, ((x * width) - scroll * 0.6, SCREEN_HEIGHT - mountain_img.get_height() - 300))
        screen.blit(pine1_img, ((x * width) - scroll * 0.7, SCREEN_HEIGHT - pine1_img.get_height() - 150))
        screen.blit(pine2_img, ((x * width) - scroll * 0.8, SCREEN_HEIGHT - pine2_img.get_height()))

#draw grid
def draw_grid():
    #vertical lines
    for c in range(MAX_COLS + 1):
        pygame.draw.line(screen, WHITE, (c * TILE_SIZE - scroll, 0), (c * TILE_SIZE - scroll, SCREEN_HEIGHT))
    #horizontal lines
    for c in range(ROWS + 1):
        pygame.draw.line(screen, WHITE, (0, c * TILE_SIZE), (SCREEN_WIDTH, c * TILE_SIZE))


# --- CULLED world drawing (only visible tiles) ---
def draw_world():
    # Calculate visible column range
    start_col = max(0, scroll // TILE_SIZE)
    end_col = min(MAX_COLS, (scroll + SCREEN_WIDTH) // TILE_SIZE + 1)
    
    for y, row in enumerate(world_data):
        for x in range(start_col, end_col):
            tile = row[x]
            if tile >= 0:
                screen.blit(img_list[tile], (x * TILE_SIZE - scroll, y * TILE_SIZE))


#create buttons
save_button = button.Button(SCREEN_WIDTH // 2, SCREEN_HEIGHT + LOWER_MARGIN - 50, save_img, 1)
load_button = button.Button(SCREEN_WIDTH // 2 + 200, SCREEN_HEIGHT + LOWER_MARGIN - 50, load_img, 1)
clear_button = button.Button(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT + LOWER_MARGIN - 50, clear_img, 1)

#make a button list for tile palette
button_list = []
button_col = 0
button_row = 0
for i in range(len(img_list)):
    tile_button = button.Button(SCREEN_WIDTH + (75 * button_col) + 50, 75 * button_row + 50, img_list[i], 1)
    button_list.append(tile_button)
    button_col += 1
    if button_col == 3:
        button_row += 1
        button_col = 0


run = True
while run:

    clock.tick(FPS)

    draw_bg()
    draw_grid()
    draw_world()

    draw_text(f'Level: {level}', font, WHITE, 10, SCREEN_HEIGHT + LOWER_MARGIN - 90)
    draw_text('Press UP or DOWN to change level', font, WHITE, 10, SCREEN_HEIGHT + LOWER_MARGIN - 60)

    # --- Save and Load with error handling ---
    if save_button.draw(screen):
        #save level data
        with open(f'level{level}_data.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter = ',')
            for row in world_data:
                writer.writerow(row)
        set_message(f'Level {level} saved!')

    if load_button.draw(screen):
        #load in level data
        if os.path.exists(f'level{level}_data.csv'):
            scroll = 0
            with open(f'level{level}_data.csv', newline='') as csvfile:
                reader = csv.reader(csvfile, delimiter = ',')
                for x, row in enumerate(reader):
                    for y, tile in enumerate(row):
                        world_data[x][y] = int(tile)
            set_message(f'Level {level} loaded!')
        else:
            set_message(f'File level{level}_data.csv not found!', duration=90)

    # --- Clear button: resets all tiles to -1 ---
    if clear_button.draw(screen):
        for y in range(ROWS):
            for x in range(MAX_COLS):
                world_data[y][x] = -1
        set_message('Level cleared!')

    #draw tile panel and tiles
    pygame.draw.rect(screen, GREEN, (SCREEN_WIDTH, 0, SIDE_MARGIN, SCREEN_HEIGHT))

    #choose a tile
    button_count = 0
    for button_count, i in enumerate(button_list):
        if i.draw(screen):
            current_tile = button_count

    #highlight the selected tile
    pygame.draw.rect(screen, RED, button_list[current_tile].rect, 3)

    #scroll the map
    if scroll_left == True and scroll > 0:
        scroll -= 5 * scroll_speed
    if scroll_right == True and scroll < (MAX_COLS * TILE_SIZE) - SCREEN_WIDTH:
        scroll += 5 * scroll_speed

    #add new tiles to the screen
    #get mouse position
    pos = pygame.mouse.get_pos()
    x = (pos[0] + scroll) // TILE_SIZE
    y = pos[1] // TILE_SIZE

    #check that the coordinates are within the tile area
    if pos[0] < SCREEN_WIDTH and pos[1] < SCREEN_HEIGHT:
        #update tile value
        if pygame.mouse.get_pressed()[0] == 1:
            if world_data[y][x] != current_tile:
                world_data[y][x] = current_tile
        if pygame.mouse.get_pressed()[2] == 1:
            world_data[y][x] = -1

    # --- Draw status message (if any) ---
    if message_timer > 0:
        # draw a semi-transparent background behind the message
        msg_surf = font.render(message, True, WHITE)
        msg_rect = msg_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT + LOWER_MARGIN - 30))
        # draw a black box behind for readability
        box_rect = msg_rect.inflate(20, 10)
        pygame.draw.rect(screen, BLACK, box_rect)
        pygame.draw.rect(screen, WHITE, box_rect, 2)
        screen.blit(msg_surf, msg_rect)
        message_timer -= 1
    else:
        message = ""   # clear text when timer runs out

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        #keyboard presses
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                level += 1
            if event.key == pygame.K_DOWN and level > 0:
                level -= 1
            if event.key == pygame.K_LEFT:
                scroll_left = True
            if event.key == pygame.K_RIGHT:
                scroll_right = True
            if event.key == pygame.K_RSHIFT:
                scroll_speed = 5
            # --- Hotkey: C = Clear Level ---
            if event.key == pygame.K_c:
                for y in range(ROWS):
                    for x in range(MAX_COLS):
                        world_data[y][x] = -1
                set_message('Level cleared! (C key)')

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                scroll_left = False
            if event.key == pygame.K_RIGHT:
                scroll_right = False
            if event.key == pygame.K_RSHIFT:
                scroll_speed = 1


    pygame.display.update()

pygame.quit()