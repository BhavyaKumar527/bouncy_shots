import pygame, sys, random, time, os, math
import data.engine as e
from data.clip import clip
mainClock = pygame.time.Clock()
from pygame.locals import *
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.display.set_caption('Bouncy Shots')
WINDOWWIDTH = 500
WINDOWHEIGHT = 700
screen = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT),0,32)
display = pygame.Surface((250,350))

# Things 
ball_hit_s = pygame.mixer.Sound('data/sfx/ball_hit.wav')
ball_hit_s.set_volume(0.5)
loss_s = pygame.mixer.Sound('data/sfx/loss.wav')
new_ball_s = pygame.mixer.Sound('data/sfx/new_ball.wav')
player_score_s = pygame.mixer.Sound('data/sfx/player_score.wav')
player_score_2_s = pygame.mixer.Sound('data/sfx/player_score_2.wav')
shoot_s = pygame.mixer.Sound('data/sfx/shoot.wav')
shoot_s.set_volume(0.2)
score_tick_s = pygame.mixer.Sound('data/sfx/score_tick.wav')
score_tick_s.set_volume(0.4)
score_final_s = pygame.mixer.Sound('data/sfx/score_final.wav')

global numbers
numbers = {}
for num in range(10):
    img = pygame.image.load('data/numbers/' + str(num) + '.png').convert()
    numbers[str(num)] = img.copy()

def draw_number(number,x,y,surface):
    global numbers
    x_offset = 0
    for char in number:
        surface.blit(numbers[char],(x+x_offset,y))
        x_offset += 23

e.load_particle_images('data/particles')

bg_img = pygame.image.load('data/bg.png').convert()
bg_img.set_colorkey((0,0,0))

instructions_img = pygame.image.load('data/instructions.png').convert()
instructions_img.set_colorkey((0,0,0))

def advance(pos,rot,amt):
    x = pos[0] + math.cos(math.radians(rot)) * amt
    y = pos[1] + math.sin(math.radians(rot)) * amt
    return [x,y]

def normalize(num,amt):
    if num < -amt:
        num += amt
    elif num > amt:
        num -= amt
    else:
        num = 0
    return num

def mirror_angle(original,base):
    dif = 180-base
    base = 180
    new = original+dif
    new = new % 360
    dif = base-new
    return original + dif * 2

def rotate_towards(target,original,rate):
    dif = 180-target
    target = 180
    new = original+dif
    new = new % 360
    dif = target-new
    if abs(dif) < rate:
        return dif
    else:
        return dif/abs(dif) * rate

right = False
left = False

player_rotation = 76
player_polygon_rot = 0
player_polygon_spin = 0
player_cooldown = 0
player_max_cooldown = 20

opponent_rotation = 256
opponent_polygon_rot = 0
opponent_polygon_spin = 0
opponent_cooldown = 0
opponent_true_cooldown = 0
opponent_max_cooldown = 20
opponent_accuracy = 50
opponent_speed = 70
opponent_target_offset = random.randint(0,int(opponent_accuracy))-int(opponent_accuracy/2)

points_in_polygons = 12
polygon_radius = 200

blue = (0,171,214)
red = (242,83,109)
gray = (230,230,230)

colors = {'player':blue,'opponent':red}

projectile_data = {'player':[8,20,1.3],'opponent':[8,20,1.3]}

projectile_accuracy = 4
ball_radius = 10

projectiles = []
slash_particles = []
particles = []
circle_effects = []

balls = [[125,175,0,0]]
for i in range(20):
    particles.append(e.particle(balls[-1][0]+random.randint(0,ball_radius*2)-ball_radius,balls[-1][1]+random.randint(0,ball_radius*2)-ball_radius,'p',[random.randint(0,60)/10-3,random.randint(0,60)/10-3],0.2,random.randint(0,20)/10,gray))
circle_effects.append([[125,175],10,20])

opponent_center = [display.get_width()/2,30-polygon_radius]

time_since_last_score = 1
score = 0
warping = -1
scored = False
instructions = 1
failure = -1
while True:
    # BG 
    screen.fill((93,105,110))
    display.fill((0,0,0))
    # Timer 
    if instructions == 0:
        time_since_last_score += 1
    if time_since_last_score % (60 * 7) == 0:
        balls.append([125,175,0,0])
        new_ball_s.play()
        for i in range(20):
            particles.append(e.particle(balls[-1][0]+random.randint(0,ball_radius*2)-ball_radius,balls[-1][1]+random.randint(0,ball_radius*2)-ball_radius,'p',[random.randint(0,60)/10-3,random.randint(0,60)/10-3],0.2,random.randint(0,20)/10,gray))
        circle_effects.append([[125,175],10,20])
    # Rotation
    if right == True:
        if player_rotation > 50:
            player_rotation -= 1.5
            player_polygon_spin -= 0.5
    if left == True:
        if player_rotation < 100:
            player_rotation += 1.5
            player_polygon_spin += 0.5
    player_polygon_spin = normalize(player_polygon_spin,0.2)
    player_polygon_rot += player_polygon_spin
    # Opponent AI 
    if instructions == 0:
        nearest_ball = [None,99999]
        for ball in balls:
            if ball[1] < nearest_ball[1]:
                nearest_ball = [ball.copy(),ball[1]]
        if nearest_ball[0] != None:
            dis_x = nearest_ball[0][0]-opponent_center[0]
            dis_y = nearest_ball[0][1]-opponent_center[1]
            angle_to_ball = -math.degrees(math.atan2(dis_y,dis_x))
            angle_to_ball += opponent_target_offset
            rot = rotate_towards(angle_to_ball-13.5,opponent_rotation,1.5)
            opponent_rotation += rot
            opponent_polygon_spin += rot/3
            if opponent_rotation > 280:
                opponent_rotation = 280
            if opponent_rotation < 230:
                opponent_rotation = 230
            if opponent_true_cooldown <= 0:
                opponent_cooldown = opponent_max_cooldown
                opponent_true_cooldown = opponent_max_cooldown * random.randint(10,int(opponent_speed))/10
                projectiles.append(['opponent',opponent_center.copy(),-(opponent_rotation+13.5),projectile_data['opponent'][1]])
                opponent_target_offset = random.randint(0,int(opponent_accuracy))-int(opponent_accuracy/2)
                shoot_s.play()
        opponent_polygon_spin = normalize(opponent_polygon_spin,0.2)
        opponent_polygon_rot += opponent_polygon_spin
    # Particles 
    remove_list = []
    n = 0
    for particle in particles:
        alive = particle.update()
        if alive:
            particle.draw(display,[0,0])
        else:
            remove_list.append(n)
        n += 1
    remove_list.sort(reverse=True)
    for particle in remove_list:
        particles.pop(particle)
    # Slash Particles 
    remove_list = []
    n = 0
    for particle in slash_particles: # center, rot, time_left
        points = []
        points.append(advance(particle[0],particle[1]+90,1))
        points.append(advance(particle[0],particle[1]+180,5))
        points.append(advance(particle[0],particle[1]+270,1))
        points.append(advance(particle[0],particle[1],particle[2]))
        pygame.draw.polygon(display,gray,points)
        particle[0] = advance(particle[0],particle[1],8)
        particle[2] -= 4
        if particle[2] < 0:
            remove_list.append(n)
        n += 1
    remove_list.sort(reverse=True)
    for particle in remove_list:
        slash_particles.pop(particle)
    # Balls 
    for ball in balls:
        mult = 1
        if (ball[0] < ball_radius) or (ball[0] > display.get_width()-ball_radius):
            ball[2] = -ball[2]
            mult = 2
        ball[0] += ball[2] * mult
        ball[1] += ball[3] * mult
        ball[2] = normalize(ball[2],0.001)
        ball[3] = normalize(ball[3],0.001)
        pygame.draw.circle(display,gray,[int(ball[0]),int(ball[1])],ball_radius)
        if ball[1] < -ball_radius:
            player_score_s.play()
            player_score_2_s.play()
            w = int(len(str(score))*23/2)
            circle_effects.append([[3+w,18],2,120])
            for ball in balls:
                for i in range(20):
                    particles.append(e.particle(ball[0]+random.randint(0,ball_radius*2)-ball_radius,ball[1]+random.randint(0,ball_radius*2)-ball_radius,'p',[random.randint(0,60)/10-3,random.randint(0,60)/10-3],0.2,random.randint(0,20)/10,gray))
                circle_effects.append([[ball[0],ball[1]],10,20])
            balls = []
            time_since_last_score = 1
            score += 1
            opponent_accuracy += (10-opponent_accuracy)/8
            opponent_speed += (10-opponent_speed)/20
            opponent_max_cooldown += (5-opponent_max_cooldown)/10
            player_max_cooldown += (5-player_max_cooldown)/10
            for entity in projectile_data:
                projectile_data[entity][0] += 0.3
                projectile_data[entity][2] += 0.1
            warping = 0
            scored = True
        if ball[1] > display.get_height()+ball_radius:
            loss_s.play()
            balls = []
            time_since_last_score = 1
            warping = 0
            scored = True
            failure = 0
    
    # Draw Player and Opponent 
    # player
    player_cooldown -= 1
    player_points = []
    center = [display.get_width()/2,display.get_height()-30+polygon_radius]
    mult = 1.05
    mult *= min(1,1-(player_cooldown/player_max_cooldown)*0.03)
    player_r = pygame.Rect(center[0]-polygon_radius*mult,center[1]-polygon_radius*mult,polygon_radius * mult * 2, polygon_radius * mult * 2)
    
    for i in range(points_in_polygons):
        rot = player_polygon_rot + (i * (360 / points_in_polygons))
        player_points.append([center[0] + math.cos(math.radians(rot)) * polygon_radius, center[1] + math.sin(math.radians(rot)) * polygon_radius])
    pygame.draw.polygon(display,blue,player_points)

    pygame.draw.arc(display,blue,player_r,math.radians(player_rotation + 5),math.radians(player_rotation + 25),max(1,int((player_cooldown/player_max_cooldown)*5)))
    
    # opponent
    opponent_cooldown -= 1
    opponent_true_cooldown -= 1
    opponent_points = []
    opponent_center = [display.get_width()/2,30-polygon_radius]
    mult = 1.05
    mult *= min(1,1-(opponent_cooldown/opponent_max_cooldown)*0.03)
    opponent_r = pygame.Rect(opponent_center[0]-polygon_radius*mult,opponent_center[1]-polygon_radius*mult,polygon_radius * mult * 2, polygon_radius * mult * 2)
    
    for i in range(points_in_polygons):
        rot = opponent_polygon_rot + (i * (360 / points_in_polygons))
        opponent_points.append([opponent_center[0] + math.cos(math.radians(rot)) * polygon_radius, opponent_center[1] + math.sin(math.radians(rot)) * polygon_radius])
    pygame.draw.polygon(display,red,opponent_points)

    pygame.draw.arc(display,red,opponent_r,math.radians(opponent_rotation + 5),math.radians(opponent_rotation + 25),max(1,int((opponent_cooldown/opponent_max_cooldown)*5)))
    
    # Projectiles 
    remove_list = []
    n = 0
    for projectile in projectiles:
        remove = False
        mult = projectile_data[projectile[0]][0]
        if projectile[3] == projectile_data[projectile[0]][1]:
            mult = polygon_radius-projectile_data[projectile[0]][1]
        if projectile[1][0] < projectile[3]:
            projectile[2] = mirror_angle(projectile[2]-180,0)
            mult *= 2
        if projectile[1][0] > display.get_width()-projectile[3]:
            projectile[2] = mirror_angle(projectile[2]-180,180)
            mult *= 2
        core_motion_x = math.cos(math.radians(projectile[2]))
        core_motion_y = math.sin(math.radians(projectile[2]))
        for i in range(projectile_accuracy):
            projectile[1][0] += core_motion_x * (projectile[3] / projectile_data[projectile[0]][1]) * mult / projectile_accuracy
            projectile[1][1] += core_motion_y * (projectile[3] / projectile_data[projectile[0]][1]) * mult / projectile_accuracy
            for ball in balls:
                dis_x = ball[0] - projectile[1][0]
                dis_y = ball[1] - projectile[1][1]
                dis = math.sqrt((dis_x**2) + (dis_y**2))
                if dis < ball_radius+projectile[3]:
                    ball_hit_s.play()
                    warping = 6
                    collision_angle = math.atan2(dis_y,dis_x)
                    for i in range(random.randint(2,4)):
                        slash_particles.append([advance(projectile[1],math.degrees(collision_angle),projectile[3]),math.degrees(collision_angle)+random.randint(0,120)-60,random.randint(32,72)])
                    for i in range(random.randint(1,2)):
                        slash_particles.append([advance(projectile[1],math.degrees(collision_angle),projectile[3]),math.degrees(-collision_angle)+random.randint(0,120)-60,random.randint(24,48)])
                    ball[2] = ball[2]/3
                    ball[3] = ball[3]/3
                    ball[2] += math.cos(collision_angle) * projectile_data[projectile[0]][2] * (projectile[3] / projectile_data[projectile[0]][1])
                    ball[3] += math.sin(collision_angle) * projectile_data[projectile[0]][2] * (projectile[3] / projectile_data[projectile[0]][1])
                    remove = True
                    for i in range(int(projectile[3]/2)):
                        particles.append(e.particle(projectile[1][0]+random.randint(0,int(projectile[3]))-projectile[3]/2,projectile[1][1]+random.randint(0,int(projectile[3]))-projectile[3]/2,'p',[core_motion_x*3+random.randint(0,40)/10-2,core_motion_y*3+random.randint(0,40)/10-2],0.1,random.randint(0,30)/10,colors[projectile[0]]))
        pygame.draw.circle(display,colors[projectile[0]],[int(projectile[1][0]),int(projectile[1][1])],int(projectile[3]+1))
        projectile[3] -= 0.3*projectile_data['player'][0]/10
        particles.append(e.particle(projectile[1][0]+random.randint(0,int(projectile[3]))-projectile[3]/2,projectile[1][1]+random.randint(0,int(projectile[3]))-projectile[3]/2,'p',[0,0],0.2,0,gray))
        if projectile[3] <= 0:
            remove = True
        if remove:
            remove_list.append(n)
        n += 1
    remove_list.sort(reverse=True)
    for proj in remove_list:
        projectiles.pop(proj)
    
    # Circle Effects 
    remove_list = []
    n = 0
    for circle in circle_effects: # center, radius, time_left
        pygame.draw.circle(display,gray,[int(circle[0][0]),int(circle[0][1])],int(circle[1]),min(int(circle[2]/3)+1,int(circle[1])))
        circle[2] += (-0.7-circle[2])/8
        circle[1] += circle[2]**0.7+0.5
        if circle[2] <= 0:
            remove_list.append(n)
        n += 1
    remove_list.sort(reverse=True)
    for circle in remove_list:
        circle_effects.pop(circle)
    
    # GUI 
    gui_surf = display.copy()
    gui_surf.fill((0,0,0))
    gui_surf.set_colorkey((0,0,0))
    if failure == -1:
        draw_number(str(score),3,3,gui_surf)
    if instructions != 0:
        if instructions < 40:
            gui_surf.blit(instructions_img,(72,83))
        else:
            gui_surf.blit(instructions_img,(72,80))
        if instructions > 55:
            instructions = 1
        instructions += 1
    
    # Buttons 
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()
            if event.key == K_RIGHT:
                right = True
                instructions = 0
            if event.key == K_LEFT:
                left = True
                instructions = 0
            if event.key == K_UP:
                if player_cooldown <= 0:
                    player_cooldown = player_max_cooldown
                    projectiles.append(['player',center,-(player_rotation+13.5),projectile_data['player'][1]]) # color, position, rotation, size
                    shoot_s.play()
                instructions = 0
        if event.type == KEYUP:
            if event.key == K_RIGHT:
                right = False
            if event.key == K_LEFT:
                left = False
    
    # Update
    display_2 = display.copy()
    display_2.fill((31,48,56))
    display_2.blit(display,(0,0))
    surf = display_2.copy()
    surf.fill((100,100,100))
    display_2.blit(surf,(0,0),special_flags=BLEND_MULT)
    screen.blit(pygame.transform.scale(display_2,(WINDOWWIDTH-50,WINDOWHEIGHT-50)),(24,24))
    screen.blit(pygame.transform.scale(bg_img,(WINDOWWIDTH,WINDOWHEIGHT)),(0,0))
    display.set_colorkey((0,0,0))
    screen.blit(pygame.transform.scale(display,(WINDOWWIDTH,WINDOWHEIGHT)),(0,0))
    screen.blit(pygame.transform.scale(gui_surf,(WINDOWWIDTH,WINDOWHEIGHT)),(0,0))
    if (warping != -1) and (failure == -1):
        if warping > 20:
            warping = -2
            if scored:
                scored = False
                particles = []
                projectiles = []
                balls = [[125,175,0,0]]
                time_since_last_score = 1
                for i in range(20):
                    particles.append(e.particle(balls[-1][0]+random.randint(0,ball_radius*2)-ball_radius,balls[-1][1]+random.randint(0,ball_radius*2)-ball_radius,'p',[random.randint(0,60)/10-3,random.randint(0,60)/10-3],0.2,random.randint(0,20)/10,gray))
                circle_effects.append([[125,175],10,20])
        if scored == False:
            if warping > 10:
                warping = -2
        screen.blit(pygame.transform.scale(screen,(WINDOWWIDTH+warping*2,int(WINDOWHEIGHT+warping*2*(7/5)))),(-warping+random.randint(0,12)-6,-warping*(7/5)))
        for i in range(random.randint(6,24)):
            size_x = random.randint(30,200)
            size_y = random.randint(4,24)
            pos_x = random.randint(0,WINDOWWIDTH)
            pos_y = random.randint(0,WINDOWHEIGHT)
            img = clip(screen.copy(),pos_x-int(size_x/2),pos_y-int(size_y/2),size_x,size_y)
            screen.blit(img,(pos_x+random.randint(0,80)-40+int(size_x/2),pos_y+int(size_y/2)))
        warping += 1
    pygame.display.update()
    mainClock.tick(60)
    if failure != -1:
        screen_copy = screen.copy()
        while failure != -1:
            failure += 1
            temp_surf = gui_surf.copy()
            temp_surf.fill((31,48,56))
            temp_surf.set_alpha(min(failure*10,100))
            screen.blit(screen_copy,(0,0))
            screen.blit(pygame.transform.scale(temp_surf,(WINDOWWIDTH,WINDOWHEIGHT)),(0,0))
            end_surf = gui_surf.copy()
            end_surf.fill((0,0,0))
            end_surf.set_colorkey((0,0,0))
            if failure > 10:
                if failure-11 < score:
                    score_tick_s.play()
                if failure-11 == score:
                    score_final_s.play()
                num = min(failure-11,score)
                draw_number(str(num),125-(len(str(num))*23/2),160,end_surf)
            if failure-30 > score:
                if failure % 55 < 40:
                    end_surf.blit(instructions_img,(72,223))
                else:
                    end_surf.blit(instructions_img,(72,220))
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if event.key in [K_RIGHT,K_LEFT,K_UP]:
                        if failure-30 > score:
                            right = False
                            left = False
                            player_rotation = 76
                            player_polygon_rot = 0
                            player_polygon_spin = 0
                            player_cooldown = 0
                            player_max_cooldown = 20
                            opponent_rotation = 256
                            opponent_polygon_rot = 0
                            opponent_polygon_spin = 0
                            opponent_cooldown = 0
                            opponent_true_cooldown = 0
                            opponent_max_cooldown = 20
                            opponent_accuracy = 50
                            opponent_speed = 70
                            opponent_target_offset = random.randint(0,int(opponent_accuracy))-int(opponent_accuracy/2)
                            projectile_data = {'player':[8,20,1.3],'opponent':[8,20,1.3]}
                            projectiles = []
                            slash_particles = []
                            particles = []
                            circle_effects = []
                            balls = [[125,175,0,0]]
                            for i in range(20):
                                particles.append(e.particle(balls[-1][0]+random.randint(0,ball_radius*2)-ball_radius,balls[-1][1]+random.randint(0,ball_radius*2)-ball_radius,'p',[random.randint(0,60)/10-3,random.randint(0,60)/10-3],0.2,random.randint(0,20)/10,gray))
                            circle_effects.append([[125,175],10,20])
                            opponent_center = [display.get_width()/2,30-polygon_radius]
                            time_since_last_score = 1
                            score = 0
                            warping = -1
                            scored = False
                            failure = -1
            screen.blit(pygame.transform.scale(end_surf,(WINDOWWIDTH,WINDOWHEIGHT)),(0,0))
            pygame.display.update()
            mainClock.tick(60)