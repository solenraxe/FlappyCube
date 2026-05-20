import pygame
from random import randint
import sys, os

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

pygame.init()
pygame.font.init()
pygame.joystick.init()

#init
joysticks = []
joysticks_nb = pygame.joystick.get_count()

comicSans = pygame.font.SysFont('Comic Sans MS', 30)

WIDTH, HEIGHT = 800, 600
framecount = 0

screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

pygame.display.set_caption("Flappy Cube")
pygame.display.set_icon(pygame.image.load(resource_path('assets/Dino/DinoWhite.png')).convert_alpha())

assets = {
    "Pipe": pygame.image.load(resource_path('assets/pipe.png')).convert_alpha(),
    "PipeTop": pygame.image.load(resource_path('assets/pipeTop.png')).convert_alpha(),
    "Background": pygame.image.load(resource_path('assets/background.png')).convert(),
    "Cloud": pygame.image.load(resource_path('assets/cloud.png')).convert_alpha(),
    "Laser": pygame.image.load(resource_path('assets/laser.png')).convert_alpha()
}
assets["Cloud"].set_alpha(200)
assets["PipeTop180"] = pygame.transform.rotate(assets["PipeTop"], 180)
assets["Pipe"] = pygame.transform.scale(assets["Pipe"], (65, 600))
assets["Pipe180"] = pygame.transform.rotate(assets["Pipe"], 180)

colorList = ["White", "Green", "Blue", "Red", "Yellow", "Cyan", "Magenta"]
skinList = ["Dino", "Cube", "Pig", "Duck", "Bear", "Cat"]
colors = {
    "White": (255, 255, 255),
    "Red": (255, 0, 0),
    "Green": (0, 255, 0),
    "Blue": (0, 0, 255),
    "Yellow": (255, 255, 0),
    "Cyan": (0, 255, 255),
    "Magenta": (255, 0, 255),
    "Black": (0, 0, 0),
    "CoolerBlue": (0, 183, 239),
    "Gray": (64, 64, 64)
}

for skin in skinList:
    for color in colorList:
        assets[f"{skin}{color}"] = pygame.image.load(resource_path(f'assets/{skin}/{skin}{color}.png')).convert_alpha()

running = False

#classes
class Player:
    def __init__(self, num):
        self.rect = pygame.Rect(100 - num * 10 + 20, HEIGHT//2, 50, 50)
        self.sprite = assets["DinoWhite"]
        self.color = 0
        self.vy = 0
        self.jumpPower = 18
        self.gravity = 0.5
        self.inertia = 0.5
        self.number = num
        self.unspentPoints = 2
        self.skin = 0
        self.ability = 0
        self.coolDown = 0
        self.effects = []

        self.keysPressed = []
        self.pipeCooldown = 0
        self.laserCooldown = 0
        self.yAttack = 300

    def ig_update(self, deltat):
        if self.vy < 20 and self.vy >= -10:
            if self.vy >= 0:
                self.vy += self.gravity * 2 * self.inertia
            else:
                self.vy = (self.vy * 1.950 * self.inertia + self.gravity * 2 * self.inertia) if self.inertia * 1.95 < 1 else (self.vy * 0.999 + self.gravity * 2 * self.inertia)
        elif self.vy < -10:
            self.vy *= 1.6 * self.inertia if self.inertia * 1.6 < 0.95 else 0.95
        if self.rect.y + self.vy < HEIGHT - self.rect.height and self.rect.y + self.vy > 0:
            self.rect.y += self.vy * deltat * 60
        else:
            if self.rect.y + self.vy >= HEIGHT - self.rect.height:
                self.rect.y = HEIGHT - self.rect.height
            else:
                self.rect.y = 0
            self.vy = 0
        
        self.coolDown -= 1 if self.coolDown >= 1 else 0
        for effect in self.effects:
            effect["Duration"] -= 1
            if effect["Duration"] <= 0:
                player_effect(self, effect["Name"], on=False)

    def og_update(self):
        for key in self.keysPressed:
            if key == pygame.K_LEFT or key == pygame.K_q:
                self.yAttack += gameSpeed * 0.75
            elif key == pygame.K_RIGHT or key == pygame.K_d:
                self.yAttack -= gameSpeed * 0.75
        self.pipeCooldown -= 1 if self.pipeCooldown >= 1 else 0
        self.laserCooldown -= 1 if self.laserCooldown >= 1 else 0

    def reset(self):
        self.rect.y = HEIGHT//2
        self.vy = 0
        self.alive = True
        for effect in self.effects:
            effect["Duration"] = 0
            player_effect(self, effect["Name"], on=False)
        self.coolDown = 0
        self.rect = pygame.Rect(100 - self.number * 10 + 20, HEIGHT//2, 50, 50)

class ObstacleTuple:
    def __init__(self, randomNum, gavePoint=False):
        self.top = pygame.Rect(WIDTH, randomNum - HEIGHT, 65, 600)
        self.bottom = pygame.Rect(WIDTH, randomNum + 200, 65, 600)
        self.gavePoint = gavePoint

        self.top_surf = assets["Pipe180"]
        self.bottom_surf = assets["Pipe"]

        self.top_cap = assets["PipeTop180"]
        self.bottom_cap = assets["PipeTop"]

    def move(self, dx):
        self.top.x += dx
        self.bottom.x += dx

class Laser:
    def __init__(self, x, y, usedBy, d=1):
        self.rect = pygame.Rect(x, y, 50, 20)
        self.lifetime = 60
        self.speed = 20
        self.d = d
        self.usedBy = usedBy

    def update(self, deltat):
        self.rect.x += self.speed * deltat * 60 * self.d
        self.lifetime -= 1

#menus variables
menuList = ["Play", "Skins", "Colors", "Stats", "Abilities", "Settings"]
menuSwitch = {
    "currentMenu" : 0,
    "menuText" : comicSans.render("Play", False, colors["White"])
}

menusTexts = {
    "PlayTexts" : {
        1 : comicSans.render("Press DOWN to play!", False, colors["White"])
    },
    "SkinsTexts" : {
        1 : comicSans.render("Press DOWN or UP to change skin!", False, colors["White"]),
        2 : comicSans.render(f"Current skin : Dino", False, colors["White"])
    },
    "ColorsTexts" : {
        1 : comicSans.render("Press DOWN or UP to change color!", False, colors["White"]),
        2 : comicSans.render(f"Current color : White", False, colors["White"])
    },
    "StatsTexts" : {
        1 : comicSans.render("Press UP to increase, DOWN to decrease.", False, colors["White"]),
        2 : comicSans.render(f"Unspent Points : {2}", False, colors["White"])
    },
    "AbilitiesTexts" : {
        1 : comicSans.render(f"Current ability : Shrink", False, colors["White"])
    },
    "SettingsTexts" : {
        1 : comicSans.render("Press TAB to change setting.", False, colors["White"]),
        2 : comicSans.render("Press UP or DOWN to change setting value.", False, colors["White"])
    }
}

menusOffset = {
    "Play": 125,
    "Skins": 0,
    "Colors": 0,
    "Stats": 0,
    "Abilities": 125,
    "Settings": 0
}

currentSelection = 0

settingsList = ["Clouds Number", "Background"]
settingsMenu = {
    "currentSetting" : 0,
    "cloudsNumber" : 5,
    "clouds" : True,
    "settings" : {
        "Clouds Number": [comicSans.render(f"Clouds Number : 5", False, colors["Red"]), "Red", 5],
        "Background": [comicSans.render(f"Background : On", False, colors["White"]), "White", "On"]
    }
}

statsList = ["Jump Power", "Inertia", "Gravity"]
statsVars = {
    "currentStat" : 0,
    "stats" : {
        "Jump Power": [18, "Red", "jumpPower"],
        "Inertia": [0.5, "White", "inertia"],
        "Gravity": [0.5, "White", "gravity"]
    }
}

abilitiesList = ["Shrink", "Laser"]
abilitiesCoolDown = [400, 800]
for ability in abilitiesList:
    assets[f"{ability}Icon"] = pygame.image.load(resource_path(f'assets/Icons/{ability}.png')).convert_alpha()

#game variables
obstacleList = []
playerList = [Player(1), Player(2)]
cloudList = []
laserList = []
background_x = 0

playersAlive = 2
gameSpeed = 5

currentPlaying = 0

score1 = 0
score2 = 0
scoreText1 = comicSans.render(f"Score : {0}", False, (255, 255, 255))
scoreText2 = comicSans.render(f"Score : {0}", False, (255, 255, 255))

gameStates = {
    "gameStarted" : False,
    "gameInit" : False
}

pauseText = comicSans.render("Game Paused! Press ESC to resume.", False, colors["White"])
pSelectText = comicSans.render(f"Current player selection : P{1}", False, colors["White"])

dt = 0.1

#functions

def render_score(s):
    return comicSans.render(f"Score : {s}", False, (255, 255, 255))

def player_effect(player, effect, on=True, duration=180):
    if effect == "Shrinked":
        if on:
            player.effects.append({"Name": "Shrinked", "Duration": duration})
            player.rect.height, player.rect.width = 25, 25
            player.sprite = pygame.transform.scale(player.sprite, (25, 25))
            player.rect.y += 12
            player.rect.x += 12
        else:
            player.effects.remove({"Name": "Shrinked", "Duration": 0})
            player.rect.height, player.rect.width = 50, 50
            player.sprite = pygame.transform.scale(player.sprite, (50, 50))
            player.rect.y -= 12
            player.rect.x -= 12

def use_ability(player, abilityNum):
    if player.coolDown == 0:
        if abilityNum == 0:  # Shrink
            player_effect(player, "Shrinked", on=True, duration=180)
        elif abilityNum == 1:  # Laser
            laserList.append(Laser(player.rect.x + player.rect.width, player.rect.y + player.rect.height//2 - 5, player.number))
        
        player.coolDown = abilitiesCoolDown[abilityNum]

#keys functions
def keyHorMenu(direction):
    global menuSwitch
    menuSwitch["currentMenu"] = (menuSwitch["currentMenu"] +direction) % len(menuList)
    menuSwitch["menuText"] = comicSans.render(menuList[menuSwitch["currentMenu"]], False, colors["White"])

def keyVertMenu(direction):
    global gameStates, currentSelection, playerList, menusTexts, settingsMenu, gameVariables, statsVars
    if menuList[menuSwitch["currentMenu"]] == "Play":
        gameStates["gameStarted"] = True

    elif menuList[menuSwitch["currentMenu"]] == "Skins":
        playerList[currentSelection].skin = (playerList[currentSelection].skin + direction) % len(skinList)
        menusTexts["SkinsTexts"][2] = comicSans.render(f"Current skin : {skinList[playerList[currentSelection].skin]}", False, colors["White"])
        playerList[currentSelection].sprite = assets[f"{skinList[playerList[currentSelection].skin]}{colorList[playerList[currentSelection].color]}"]
                        
    elif menuList[menuSwitch["currentMenu"]] == "Colors":
        playerList[currentSelection].color = (playerList[currentSelection].color + direction) % len(colorList)
        menusTexts["ColorsTexts"][2] = comicSans.render(f"Current color : {colorList[playerList[currentSelection].color]}", False, colors["White"])
        playerList[currentSelection].sprite = assets[f"{skinList[playerList[currentSelection].skin]}{colorList[playerList[currentSelection].color]}"]

    elif menuList[menuSwitch["currentMenu"]] == "Settings":
        changedSetting = settingsList[settingsMenu["currentSetting"]]
                                
        if changedSetting == "Clouds Number":
            settingsMenu["settings"]["Clouds Number"][2] = (settingsMenu["settings"]["Clouds Number"][2] + direction) % 16
            settingsMenu["cloudsNumber"] = settingsMenu["settings"]["Clouds Number"][2]
            settingsMenu["clouds"] = settingsMenu["cloudsNumber"] > 0
                                
        elif changedSetting == "Background":
            if settingsMenu["settings"]["Background"][2] == "On":
                settingsMenu["settings"]["Background"][2] = "Off"
            else:
                settingsMenu["settings"]["Background"][2] = "On"
        settingsMenu["settings"][changedSetting][0] = comicSans.render(f"{changedSetting} : {settingsMenu['settings'][changedSetting][2]}", False, colors[settingsMenu["settings"][changedSetting][1]])
                        
    elif menuList[menuSwitch["currentMenu"]] == "Stats":
        statName = statsList[statsVars["currentStat"]]
        if direction == -1:
            decrease = 1
            newValue = getattr(playerList[currentSelection], statsVars["stats"][statName][2])
            if newValue > 0.1 * decrease:
                newValue = ((newValue * 10 - decrease)/10) if statName != "Jump Power" else newValue - decrease
                playerList[currentSelection].unspentPoints += 1
                setattr(playerList[currentSelection], statsVars["stats"][statName][2], newValue)
        elif direction == 1 and playerList[currentSelection].unspentPoints > 0:
            increase = 1
            newValue = getattr(playerList[currentSelection], statsVars["stats"][statName][2])
            newValue = ((newValue * 10 + increase)/10) if statName != "Jump Power" else newValue + increase
            playerList[currentSelection].unspentPoints -= 1
            setattr(playerList[currentSelection], statsVars["stats"][statName][2], newValue)
        menusTexts["StatsTexts"][2] = comicSans.render(f"Unspent Points : {playerList[currentSelection].unspentPoints}", False, colors["White"])
                    
    elif menuList[menuSwitch["currentMenu"]] == "Abilities":
        playerList[currentSelection].ability = (playerList[currentSelection].ability + direction) % len(abilitiesList)
        menusTexts["AbilitiesTexts"][1] = comicSans.render(f"Current ability : {abilitiesList[playerList[currentSelection].ability]}", False, colors["White"])

def keyTabMenu():
    global menuSwitch, currentSelection, settingsMenu, pSelectText, menusTexts, statsVars
    if menuList[menuSwitch["currentMenu"]] == "Colors" or menuList[menuSwitch["currentMenu"]] == "Skins" or menuList[menuSwitch["currentMenu"]] == "Abilities":
        currentSelection = (currentSelection + 1) % 2
        pSelectText = comicSans.render(f"Current player selection : P{currentSelection + 1}", False, colors["White"])
        menusTexts["ColorsTexts"][2] = comicSans.render(f"Current color : {colorList[playerList[currentSelection].color]}", False, colors["White"])
        menusTexts["SkinsTexts"][2] = comicSans.render(f"Current skin : {skinList[playerList[currentSelection].skin]}", False, colors["White"])
        menusTexts["AbilitiesTexts"][1] = comicSans.render(f"Current ability : {abilitiesList[playerList[currentSelection].ability]}", False, colors["White"])
                        
    elif menuList[menuSwitch["currentMenu"]] == "Settings":
        changedSetting = settingsList[settingsMenu["currentSetting"]]
        settingsMenu["settings"][changedSetting][1] = "White"
        settingsMenu["settings"][changedSetting][0] = comicSans.render(f"{changedSetting} : {settingsMenu['settings'][changedSetting][2]}", False, colors[settingsMenu["settings"][changedSetting][1]])
        settingsMenu["currentSetting"] = (settingsMenu["currentSetting"] + 1) % len(settingsList)
        changedSetting = settingsList[settingsMenu["currentSetting"]]
        settingsMenu["settings"][changedSetting][1] = "Red"
        settingsMenu["settings"][changedSetting][0] = comicSans.render(f"{changedSetting} : {settingsMenu['settings'][changedSetting][2]}", False, colors[settingsMenu["settings"][changedSetting][1]])
                        
    elif menuList[menuSwitch["currentMenu"]] == "Stats":
        statsVars["stats"][statsList[statsVars["currentStat"]]][1] = "White"
        statsVars["currentStat"] = (statsVars["currentStat"] + 1) % len(statsList)
        statsVars["stats"][statsList[statsVars["currentStat"]]][1] = "Red"

#main loop
running = True
while running:
    if gameStates["gameStarted"]:
        framecount += 1
        if not gameStates["gameInit"]:
            screen.fill(colors["Black"])
            obstacleList = []
            laserList = []
            framecount = 1
            for player in playerList:
                player.reset()
            playersAlive = 2
            currentPlaying = 0
            score1, score2 = 0, 0
            scoreText1 = render_score(score1)
            scoreText2 = render_score(score2)
            gameSpeed = 5
            gameStates["gameInit"] = True
            cloudList = [pygame.Rect(WIDTH + randint(0, WIDTH * 2), i * int(600/settingsMenu["cloudsNumber"]) + 20, 200, 200) for i in range(settingsMenu["cloudsNumber"])] if settingsMenu["clouds"] else []

            joysticks = []
            for event in pygame.event.get():
                if event.type == pygame.JOYDEVICEADDED:
                    joystick = pygame.joystick.Joystick(event.device_index)
                    joysticks.append(joystick)
            joysticks_nb = pygame.joystick.get_count()

        player = playerList[currentPlaying]
        attacker = playerList[1 - currentPlaying]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                    running = False
            if event.type == pygame.KEYDOWN:
                playerKeys = {pygame.K_SPACE: 0, pygame.K_UP: 1, pygame.K_z: 0, pygame.K_DOWN: 1}
                if event.key == pygame.K_UP or event.key == pygame.K_SPACE:
                    user = playerList[playerKeys[event.key]]
                    if user == attacker and not user.pipeCooldown > 0:
                        obstacleList.append(ObstacleTuple(user.yAttack - 100))
                        user.pipeCooldown = 120 - gameSpeed * 8
                    elif user == player:
                        user.vy -= user.jumpPower
                elif event.key == pygame.K_z or event.key == pygame.K_DOWN:
                    user = playerList[playerKeys[event.key]]
                    if user == attacker and not user.laserCooldown > 0:
                        laserList.append(Laser(WIDTH, user.yAttack, user.number, -1))
                        user.laserCooldown = 180 - gameSpeed * 12
                    else:
                        use_ability(user, user.ability)
                elif event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    playerList[1].keysPressed.append(event.key)
                elif event.key == pygame.K_q or event.key == pygame.K_d:
                    playerList[0].keysPressed.append(event.key)
                elif event.key == pygame.K_ESCAPE:
                    gameStates["gameStarted"] = not gameStates["gameStarted"]
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    playerList[1].keysPressed.remove(event.key)
                elif event.key == pygame.K_q or event.key == pygame.K_d:
                    playerList[0].keysPressed.remove(event.key)

        if joysticks_nb > 1:
            horiz_move_0 = joysticks[currentPlaying].get_axis(0)
            vert_move_0 = joysticks[currentPlaying].get_axis(1)
            if ((vert_move_0)**2)**0.5 > 0.2 or ((horiz_move_0)**2)**0.5 > 0.2:
                use_ability(player, player.ability)
            for j in range(4):
                if joysticks[currentPlaying].get_buttons(j):
                    player.vy -= player.jumpPower
            if joysticks[currentPlaying].get_buttons(4):
                use_ability(player, player.ability)
            if joysticks[currentPlaying].get_buttons(5):
                gameStates["gameStarted"] = not gameStates["gameStarted"]
            if joysticks[currentPlaying].get_hat(0)[1] == 1 or joysticks[currentPlaying].get_hat(0)[0] == 1 or joysticks[currentPlaying].get_hat(0)[0] == -1 or joysticks[currentPlaying].get_hat(0)[1] == -1:
                use_ability(player, player.ability)

        player.ig_update(dt)
        attacker.og_update()

        if framecount % (300 + gameSpeed * 60) == 0:
            currentPlaying = 1 if currentPlaying == 0 else 0
            framecount = 0
            newPlayer = playerList[currentPlaying]
            newPlayer.rect, newPlayer.vy, newPlayer.effects = player.rect, player.vy, player.effects
            player = newPlayer
            obstacleList, laserList = [], []

        newObstacleList = []
        for obstacle in obstacleList:
            dx = -int(gameSpeed * dt * 60)
            obstacle.move(dx)

            availablePoints = gameSpeed - 4
            top, bottom = obstacle.top, obstacle.bottom

            if not obstacle.gavePoint and top.x <= player.rect.x:
                obstacle.gavePoint = True
                if currentPlaying == 0:
                    score1 += 1
                    scoreText1 = render_score(score1)
                else:
                    score2 += 1
                    scoreText2 = render_score(score2)
            if top.colliderect(player.rect) or bottom.colliderect(player.rect):
                player.alive = False
                gameStates["gameStarted"] = False
                gameStates["gameInit"] = False
                                
            if top.x + top.width > 0:
                newObstacleList.append(obstacle)

        for laser in laserList:
            laser.update(dt)
            if laser.usedBy - 1 == currentPlaying:
                for obstacle in obstacleList:
                    if laser.rect.colliderect(obstacle.top) or laser.rect.colliderect(obstacle.bottom):
                        newObstacleList.remove(obstacle)
            else:
                if laser.rect.colliderect(player.rect):
                    if player.number != laser.usedBy:
                        player.alive = False
                        gameStates["gameStarted"] = False
                        gameStates["gameInit"] = False
            if laser.lifetime <= 0:
                laserList.remove(laser)
        
        if settingsMenu["clouds"]:
            for cloud in cloudList:
                cloud.x -= int(gameSpeed * dt * 60)
                if cloud.x + cloud.width < 0:
                    cloud.x = WIDTH + randint(0, 800)

        obstacleList = newObstacleList

        if gameSpeed < 12:
            gameSpeed = (score1 + score2) // 8 + 5

        screen.fill(colors["CoolerBlue"])
        if settingsMenu["settings"]["Background"][2] == "On":
            background_x += int(gameSpeed * dt * 60)
            background_x = background_x % WIDTH
            screen.blit(assets["Background"], (-background_x, 0))
            screen.blit(assets["Background"], (WIDTH - background_x, 0))

        for obstacle in obstacleList:
            top, bottom = obstacle.top, obstacle.bottom
            screen.blit(obstacle.top_surf, top)
            screen.blit(obstacle.bottom_surf, bottom)
            screen.blit(obstacle.top_cap, (top.x + 2, top.y + HEIGHT - 25))
            screen.blit(obstacle.bottom_cap, (bottom.x + 2, bottom.y))

        if settingsMenu["clouds"]:
            for cloud in cloudList:
                screen.blit(assets["Cloud"], cloud)

        screen.blit(player.sprite, player.rect)
        pygame.draw.rect(screen, colors["White"], (WIDTH - 75 - 3, HEIGHT - 103, 56, 56))
        screen.blit(assets[f"{abilitiesList[player.ability]}Icon"], (WIDTH - 75, HEIGHT - 100))
        pygame.draw.rect(screen, colors["Gray"], (WIDTH - 75, HEIGHT - 100, 50, 50 * (player.coolDown / abilitiesCoolDown[player.ability])))
        ptext = comicSans.render(f"P{player.number}", False, colors[colorList[player.color]])
        screen.blit(ptext, (player.rect.x + player.rect.width//4, player.rect.y - comicSans.get_height()))

        for laser in laserList:
            screen.blit(assets["Laser"], laser.rect)

        pygame.draw.rect(screen, colorList[attacker.color], (WIDTH - 75, attacker.yAttack, 16, 16))

        screen.blit(scoreText1, (25, 25))
        screen.blit(scoreText2, (WIDTH - 25 - scoreText2.get_width(), 25))

    else:
        screen.fill(colors["Black"])
        if not gameStates["gameInit"]:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RIGHT:
                        keyHorMenu(1)
                    elif event.key == pygame.K_LEFT:
                        keyHorMenu(-1)
                    elif event.key == pygame.K_DOWN:
                        keyVertMenu(-1)
                    elif event.key == pygame.K_UP:
                        keyVertMenu(1)
                    elif event.key == pygame.K_TAB:
                        keyTabMenu()

            for i in range(joysticks_nb):
                horiz_move_0 = joysticks[i].get_axis(0)
                vert_move_0 = joysticks[i].get_axis(1)
                if vert_move_0 > 0.2:
                    keyVertMenu(1)
                elif vert_move_0 < -0.2:
                    keyVertMenu(-1)
                if horiz_move_0 > 0.2:
                    keyHorMenu(1)
                elif horiz_move_0 < -0.2:
                    keyHorMenu(-1)

                for j in range(6):
                    if joysticks[i].get_buttons(j):
                        if j == 0:
                            keyVertMenu(1)
                        elif j == 1:
                            keyVertMenu(-1)
                        elif j == 2:
                            keyHorMenu(1)
                        elif j == 3:
                            keyHorMenu(-1)
                        elif j == 4:
                            keyTabMenu()
                        elif j == 5:
                            if menuList[menuSwitch["currentMenu"]] == "Colors" or menuList[menuSwitch["currentMenu"]] == "Skins" or menuList[menuSwitch["currentMenu"]] == "Abilities" or menuList[menuSwitch["currentMenu"]] == "Stats":
                                currentSelection = (currentSelection + 1) % 2
                                pSelectText = comicSans.render(f"Current player selection : P{currentSelection + 1}", False, colors["White"])
                                menusTexts["ColorsTexts"][2] = comicSans.render(f"Current color : {colorList[playerList[currentSelection].color]}", False, colors["White"])
                                menusTexts["SkinsTexts"][2] = comicSans.render(f"Current skin : {skinList[playerList[currentSelection].skin]}", False, colors["White"])
                
                if joysticks[i].get_hat(0)[1] == 1:
                    keyVertMenu(1)
                if joysticks[i].get_hat(0)[1] == -1:
                    keyVertMenu(-1)
                if joysticks[i].get_hat(0)[0] == 1:
                    keyHorMenu(1)
                if joysticks[i].get_hat(0)[0] == -1:
                    keyHorMenu(-1)

            screen.blit(menuSwitch["menuText"], (WIDTH//2 - menuSwitch["menuText"].get_width()//2, HEIGHT//2 - menuSwitch["menuText"].get_height()//2 - 200))

            pygame.draw.polygon(screen, colors["White"], [[WIDTH//2 - menuSwitch["menuText"].get_width()//2 - 50, HEIGHT//2 - 200], [WIDTH//2 - menuSwitch["menuText"].get_width()//2 - 25, HEIGHT//2 - 175], [WIDTH//2 - menuSwitch["menuText"].get_width()//2 - 25, HEIGHT//2 - 225]], 0)
            pygame.draw.polygon(screen, colors["White"], [[WIDTH//2 + menuSwitch["menuText"].get_width()//2 + 50, HEIGHT//2 - 200], [WIDTH//2 + menuSwitch["menuText"].get_width()//2 + 25, HEIGHT//2 - 175], [WIDTH//2 + menuSwitch["menuText"].get_width()//2 + 25, HEIGHT//2 - 225]], 0)

            for i, v in enumerate(menusTexts[f"{menuList[menuSwitch["currentMenu"]]}Texts"].values()):
                screen.blit(v, (WIDTH//2 - v.get_width()//2, HEIGHT//2 - v.get_height()//2 - 100 + menusOffset[menuList[menuSwitch["currentMenu"]]] + i * 40))
           
            if menuList[menuSwitch["currentMenu"]] == "Colors" or menuList[menuSwitch["currentMenu"]] == "Skins" or menuList[menuSwitch["currentMenu"]] == "Abilities" or menuList[menuSwitch["currentMenu"]] == "Stats":
                screen.blit(pSelectText, (WIDTH//2 - pSelectText.get_width()//2, HEIGHT//2 - pSelectText.get_height()//2 - 20))

            if menuList[menuSwitch["currentMenu"]] == "Colors" or menuList[menuSwitch["currentMenu"]] == "Skins":
                screen.blit(assets[f"{skinList[playerList[currentSelection].skin]}{colorList[playerList[currentSelection].color]}"], (WIDTH//2 - 25, HEIGHT//2 + 100))
            
            elif menuList[menuSwitch["currentMenu"]] == "Stats":
                for i, stat in enumerate(statsList):
                    statText = comicSans.render(f"{stat} : {getattr(playerList[currentSelection], statsVars["stats"][stat][2])}", False, colors[statsVars["stats"][stat][1]])
                    screen.blit(statText, (WIDTH//2 - statText.get_width()//2, HEIGHT//2 - statText.get_height()//2 + i * 50 + 75))
            
            elif menuList[menuSwitch["currentMenu"]] == "Settings":
                for i, setting in enumerate(settingsList):
                    screen.blit(settingsMenu["settings"][setting][0], (WIDTH//2 - settingsMenu["settings"][setting][0].get_width()//2, HEIGHT//2 - settingsMenu["settings"][setting][0].get_height()//2 + i * 50 + 75))

            elif menuList[menuSwitch["currentMenu"]] == "Abilities":
                screen.blit(assets[f"{abilitiesList[playerList[currentSelection].ability]}Icon"], (WIDTH//2 - assets[f"{abilitiesList[playerList[currentSelection].ability]}Icon"].get_width()//2, HEIGHT//2 + 100))
        
        else:
            for event in pygame.event.get():   
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        gameStates["gameStarted"] = not gameStates["gameStarted"]
            
            for i in range(joysticks_nb):
                for j in range(8):
                    if joysticks[i].get_buttons(j):
                        gameStates["gameStarted"] = not gameStates["gameStarted"]   
                if joysticks[i].get_hat(0)[1] == 1:
                    gameStates["gameStarted"] = not gameStates["gameStarted"]
                if joysticks[i].get_hat(0)[1] == -1:
                    gameStates["gameStarted"] = not gameStates["gameStarted"]
                if joysticks[i].get_hat(0)[0] == 1:
                    gameStates["gameStarted"] = not gameStates["gameStarted"]
                if joysticks[i].get_hat(0)[0] == -1:
                    gameStates["gameStarted"] = not gameStates["gameStarted"]

            screen.blit(pauseText, (WIDTH//2 - pauseText.get_width()//2, HEIGHT//2 - pauseText.get_height()//2))
    
    pygame.display.flip()
    dt = clock.tick(60)/1000
    dt = max(0.001, min(0.1, dt))

pygame.quit()