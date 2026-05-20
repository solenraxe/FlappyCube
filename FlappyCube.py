import pygame
from random import randint
import math
import json
import sys, os

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def get_save_path():
    appdata = os.getenv("APPDATA")
    save_dir = os.path.join(appdata, "FlappyCube")
    os.makedirs(save_dir, exist_ok=True)
    return os.path.join(save_dir, "save_data.json")

save_path = get_save_path()
if not os.path.exists(save_path):
    with open(save_path, 'w') as f:
        with open(resource_path('data/data.json'), 'r') as default_f:
            f.write(default_f.read())

pygame.init()
pygame.font.init()
pygame.joystick.init()

#init
joysticks = []
joysticks_nb = pygame.joystick.get_count()

comicSans = pygame.font.SysFont('Comic Sans MS', 30)

WIDTH, HEIGHT = 800, 600

screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

pygame.display.set_caption("Flappy Cube")
pygame.display.set_icon(pygame.image.load(resource_path('assets/Dino/DinoWhite.png')).convert_alpha())

data = {}
with open(save_path, 'r') as f:
    data = json.load(f)

bad_words = []
with open(resource_path("data/bad_words.json"), "r") as f:
    bad_words = json.load(f)

best_scores = []
for i in range(1, len(data) + 1):
    best_scores.append(data[str(i)]["score"])
best_score = best_scores[-1] if best_scores != [] else 0

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
skinList = ["Dino", "Cube", "Pig", "Duck", "Bear", "Cat", "Particle"]
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
joyCooldowns = {}

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
        self.alive = True
        self.unspentPoints = 6
        self.skin = 0
        self.ability = 0
        self.coolDown = 0
        self.effects = []

    def physics_update(self, deltat):
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
        self.bottom = pygame.Rect(WIDTH, randomNum + 200 * gameVariables["gapSize"], 65, 600)
        self.gavePoint = gavePoint

        self.top_surf = assets["Pipe180"]
        self.bottom_surf = assets["Pipe"]

        self.top_cap = assets["PipeTop180"]
        self.bottom_cap = assets["PipeTop"]

    def move(self, dx):
        self.top.x += dx
        self.bottom.x += dx

class Laser:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 50, 20)
        self.lifetime = 60
        self.speed = 20

    def update(self, deltat):
        self.rect.x += self.speed * deltat * 60
        self.lifetime -= 1

#menus variables
menuList = ["Play", "Skins", "Colors", "Stats", "Abilities", "Leaderboard", "Settings"]
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
        2 : comicSans.render(f"Unspent Points : {6}", False, colors["White"])
    },
    "AbilitiesTexts" : {
        1 : comicSans.render(f"Current ability : Shrink", False, colors["White"])
    },
    "LeaderboardTexts" : {
        # to be filled dynamically
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
    "Leaderboard": -20,
    "Settings": 0
}

letterList = [chr(i) for i in range(97, 123)] + [str(i) for i in range(0, 10)] + ["_"]
nameChoice = {
    "choosingName" : False,
    "currentLetter" : 0,
    "currentLetterIndex" : -1,
    "chosenLetters" : ["_", "_", "_"]
}

currentSelection = 0

settingsList = ["Player Count", "Difficulty", "Clouds Number", "Background"]
difficultyList = ["Easy", "Normal", "Hard"]
settingsMenu = {
    "currentSetting" : 0,
    "cloudsNumber" : 5,
    "clouds" : True,
    "settings" : {
        "Player Count": [comicSans.render(f"Player Count : {1}", False, colors["Red"]), "Red", 1],
        "Difficulty": [comicSans.render(f"Difficulty : {difficultyList[1]}", False, colors["White"]), "White", "Normal", 1],
        "Clouds Number": [comicSans.render(f"Clouds Number : 5", False, colors["White"]), "White", 5],
        "Background": [comicSans.render(f"Background : On", False, colors["White"]), "White", "On"]
    }
}
max_players = 2

statsList = ["Jump Power", "Inertia", "Gravity"]
statsVars = {
    "currentStat" : 0,
    "stats" : {
        "Jump Power": [18, "Red", "jumpPower"],
        "Inertia": [0.5, "White", "inertia"],
        "Gravity": [0.5, "White", "gravity"]
    }
}

abilitiesList = ["Shrink", "Laser", "Revive"]
abilitiesCoolDown = [400, 800, 2000]
for ability in abilitiesList:
    assets[f"{ability}Icon"] = pygame.image.load(resource_path(f'assets/Icons/{ability}.png')).convert_alpha()

#game variables
gameVariables = {
    "gameSpeedMax": 1,
    "adjustment": 1,
    "spacing": 1,
    "gapSize": 1
}

obstacleList = []
playerList = [Player(1)]
cloudList = []
laserList = []
background_x = 0

playersAlive = 1
gameSpeed = 5

score = 0
scoreText = comicSans.render(f"Score : {0}", False, (255, 255, 255))

gameStates = {
    "gameStarted" : False,
    "gameInit" : False
}

pauseText = comicSans.render("Game Paused! Press ESC to resume.", False, colors["White"])
pSelectText = comicSans.render(f"Current player selection : P{1}", False, colors["White"])

dt = 0.1 
currentSpacing = 90

#functions
def save_data():
    try:
        with open(save_path, 'w') as f:
            json.dump(data, f)
        print("Saved to:", save_path)
    except Exception as e:
        print("SAVE FAILED:", e)

def updateLeaderboard():
    for i, v in enumerate(data.values()):
        menusTexts["LeaderboardTexts"][i + 1] = comicSans.render(f"{i + 1}. {v['playerName']} : {v['score']}", False, colors["White"])
updateLeaderboard()

def render_score(s):
    return comicSans.render(f"Score : {s}", False, (255, 255, 255))

def create_obstacle():
    previousObstacle = obstacleList[-1] if len(obstacleList) > 0 else None
    minY, maxY = 50, 350
    if previousObstacle:
        lastY = previousObstacle.top.height
        minY = max(50, lastY - math.floor((currentSpacing - gameSpeed*4 * gameVariables["adjustment"]) * 2 * gameVariables["adjustment"]))
        maxY = min(HEIGHT - 250, lastY + math.floor((currentSpacing - gameSpeed*4 * gameVariables["adjustment"]) * 2 * gameVariables["adjustment"]))
    randomNum = randint(minY, maxY)
    obstacleList.append(ObstacleTuple(randomNum))

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
            laserList.append(Laser(player.rect.x + player.rect.width, player.rect.y + player.rect.height//2 - 5))
        elif abilityNum == 2:  # Revive
            for player in playerList:
                player.alive = True
        
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
        if changedSetting == "Difficulty":
            settingsMenu["settings"]["Difficulty"][3] = (settingsMenu["settings"]["Difficulty"][3] + direction) % len(difficultyList)
            settingsMenu["settings"]["Difficulty"][2] = difficultyList[settingsMenu["settings"]["Difficulty"][3]]
            for i, _ in gameVariables.items():
                gameVariables[i] = 1 - (settingsMenu["settings"]["Difficulty"][3] - 1) * 0.2
                           
        elif changedSetting == "Player Count":
            settingsMenu["settings"]["Player Count"][2] = (settingsMenu["settings"]["Player Count"][2] + direction - 1) % (max_players) + 1
            playerStats = []
            for i in range(max_players):
                if len(playerList) > i:
                    playerStats.append((playerList[i].jumpPower, playerList[i].inertia, playerList[i].gravity, playerList[i].unspentPoints, playerList[i].color, playerList[i].sprite, playerList[i].skin))
                else:
                    playerStats.append((18, 0.5, 0.5, 2, 0, assets["DinoWhite"], 0))
            playerList = []
            for i in range(settingsMenu["settings"]["Player Count"][2]):
                playerList.append(Player(i + 1))
                playerList[i].jumpPower, playerList[i].inertia, playerList[i].gravity, playerList[i].unspentPoints, playerList[i].color, playerList[i].sprite, playerList[i].skin = playerStats[i]
            currentSelection = 0
                                
        elif changedSetting == "Clouds Number":
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
        currentSelection = (currentSelection + 1) % settingsMenu["settings"]["Player Count"][2]
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

def keyEnterName():
    global nameChoice, best_scores, best_score, data, score
    badwordfound = False
    for word in bad_words:
        if "".join(nameChoice["chosenLetters"]).lower() == word:
            nameChoice["chosenLetters"] = ["_", "_", "_"]
            nameChoice["currentLetterIndex"] = 0
            nameChoice["currentLetter"] = 0
            badwordfound = True
            break
    if not badwordfound:
        found = False
        previous_data = data.copy()
        for i in range(0, 10):
            if score > best_scores[i] and not found:
                best_scores.insert(i, score)
                best_scores.pop()
                data[str(i + 1)] = {"playerName": "".join(nameChoice["chosenLetters"]), "score": score}
                best_score = best_scores[-1]
                found = True
            elif found and i < 10:
                data[str(i + 1)] = previous_data[str(i)]
        updateLeaderboard()
        nameChoice["choosingName"] = False

def keyTabName(direction=1):
    global nameChoice
    nameChoice["currentLetter"] = (nameChoice["currentLetter"] + direction) % 3
    nameChoice["currentLetterIndex"] = letterList.index(nameChoice["chosenLetters"][nameChoice["currentLetter"]])

def keyChangeLetter(direction):
    global nameChoice
    nameChoice["currentLetterIndex"] = (nameChoice["currentLetterIndex"] + direction) % len(letterList)
    nameChoice["chosenLetters"][nameChoice["currentLetter"]] = letterList[nameChoice["currentLetterIndex"]]

#main loop
running = True
while running:
    for key in joyCooldowns:
        joyCooldowns[key] -= 1
        if joyCooldowns[key] <= 0:
            del joyCooldowns[key]
            break
    if gameStates["gameStarted"]:
        if not gameStates["gameInit"]:
            screen.fill(colors["Black"])
            obstacleList = []
            laserList = []
            for player in playerList:
                player.reset()
            if len(playerList) < settingsMenu["settings"]["Player Count"][2]:
                for i in range(settingsMenu["settings"]["Player Count"][2] - len(playerList)):
                    playerList.append(Player(len(playerList) + 1))
            else:
                playerList = playerList[:settingsMenu["settings"]["Player Count"][2]]
            playersAlive = settingsMenu["settings"]["Player Count"][2]
            score = 0
            scoreText = render_score(score)
            gameSpeed = 5
            currentSpacing = 90
            gameStates["gameInit"] = True
            cloudList = [pygame.Rect(WIDTH + randint(0, WIDTH * 2), i * int(600/settingsMenu["cloudsNumber"]) + 20, 200, 200) for i in range(settingsMenu["cloudsNumber"])] if settingsMenu["clouds"] else []

            if joysticks_nb > 0:
                max_players = min(joysticks_nb, 4)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                    save_data()
                    running = False

            elif event.type == pygame.KEYDOWN:

                playerKeys = {pygame.K_UP: 0, pygame.K_DOWN: 1, pygame.K_RIGHT: 2, pygame.K_LEFT: 3}
                if event.key == pygame.K_RIGHT or event.key == pygame.K_LEFT or event.key == pygame.K_DOWN or event.key == pygame.K_UP:
                    if len(playerList) > 0 and playerKeys[event.key] < len(playerList):
                        playerList[playerKeys[event.key]].vy -= playerList[playerKeys[event.key]].jumpPower
                elif event.key == pygame.K_z:
                    use_ability(playerList[0], playerList[0].ability)
                elif event.key == pygame.K_s and len(playerList) > 1:
                    use_ability(playerList[1], playerList[1].ability)
                elif event.key == pygame.K_ESCAPE:
                    gameStates["gameStarted"] = not gameStates["gameStarted"]
                elif event.key == pygame.K_SPACE:
                    playerList[0].vy -= playerList[0].jumpPower

                elif event.key == pygame.K_q:
                    running = False
            elif event.type == pygame.JOYDEVICEADDED:
                joystick = pygame.joystick.Joystick(event.device_index)
                print(joystick.get_name())
                joysticks.append(joystick)
                joysticks_nb = pygame.joystick.get_count()

        for i in range(len(playerList)):
            if not len(joysticks) > i:
                continue
            horiz_move_0 = joysticks[i].get_axis(0)
            vert_move_0 = joysticks[i].get_axis(1)
            if ((vert_move_0)**2)**0.5 > 0.2 or ((horiz_move_0)**2)**0.5 > 0.2:
                if joyCooldowns["VertUp"] <= 0:
                    joyCooldowns["VertUp"] = 30
                    use_ability(playerList[i], playerList[i].ability)
            for j in range(6):
                if joysticks[i].get_button(j) and (i, j) not in joyCooldowns:
                    joyCooldowns[(i, j)] = 30
                    if j < 4:
                        playerList[i].vy -= playerList[i].jumpPower
                    elif j < 5:
                        use_ability(playerList[i], playerList[i].ability)
                    else:
                        gameStates["gameStarted"] = not gameStates["gameStarted"]
            if joysticks[i].get_hat(0)[1] == 1 or joysticks[i].get_hat(0)[0] == 1 or joysticks[i].get_hat(0)[0] == -1 or joysticks[i].get_hat(0)[1] == -1:
                if joyCooldowns["VertUp"] <= 0:
                    joyCooldowns["VertUp"] = 30
                    use_ability(playerList[i], playerList[i].ability)       

        for player in playerList:
            player.physics_update(dt)

        newObstacleList = []
        for obstacle in obstacleList:
            dx = -int(gameSpeed * dt * 60)
            obstacle.move(dx)

            availablePoints = playersAlive * (settingsMenu["settings"]["Difficulty"][3] + 1)
            top, bottom = obstacle.top, obstacle.bottom

            for player in playerList:
                if player.alive:
                    if not obstacle.gavePoint and top.x <= player.rect.x:
                        obstacle.gavePoint = True
                        score += availablePoints
                        scoreText = render_score(score)
                    if top.colliderect(player.rect) or bottom.colliderect(player.rect):
                        player.alive = False
                        playersAlive = 0
                        for player in playerList:
                            if player.alive == True:
                                playersAlive += 1
                        if playersAlive == 0:
                            gameStates["gameStarted"] = False
                            gameStates["gameInit"] = False
                            if score > best_score:
                                nameChoice["choosingName"] = True

            if top.x + top.width > 0:
                newObstacleList.append(obstacle)

        for laser in laserList:
            laser.update(dt)
            for obstacle in obstacleList:
                if laser.rect.colliderect(obstacle.top) or laser.rect.colliderect(obstacle.bottom):
                    newObstacleList.remove(obstacle)
            if laser.lifetime <= 0:
                laserList.remove(laser)
        
        if settingsMenu["clouds"]:
            for cloud in cloudList:
                cloud.x -= int(gameSpeed * dt * 60)
                if cloud.x + cloud.width < 0:
                    cloud.x = WIDTH + randint(0, 800)

        obstacleList = newObstacleList

        if gameSpeed < 10 * (2 - gameVariables["gameSpeedMax"]):
            gameSpeed = score // 8 + 5

        if obstacleList == [] or obstacleList[-1].top.x < WIDTH - currentSpacing:
            create_obstacle()
            currentSpacing = randint(max(int(250 * gameVariables["spacing"]), int((300 - score//2) * gameVariables["spacing"])), max(int(400 * gameVariables["spacing"]), int((600 - score) * gameVariables["spacing"]))) + 65

        screen.fill(colors["CoolerBlue"])
        if settingsMenu["settings"]["Background"][2] == "On":
            background_x += int(gameSpeed * dt * 60) * 0.8
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

        for player in playerList:
            if player.alive:
                screen.blit(player.sprite, player.rect)
                pygame.draw.rect(screen, colors["White"], (WIDTH - 75 * player.number - 3, HEIGHT - 103, 56, 56))
                screen.blit(assets[f"{abilitiesList[player.ability]}Icon"], (WIDTH - 75 * player.number, HEIGHT - 100))
                pygame.draw.rect(screen, colors["Gray"], (WIDTH - 75 * player.number, HEIGHT - 100, 50, 50 * (player.coolDown / abilitiesCoolDown[player.ability])))
                if settingsMenu["settings"]["Player Count"][2] > 1:
                    ptext = comicSans.render(f"P{player.number}", False, colors[colorList[player.color]])
                    screen.blit(ptext, (player.rect.x + player.rect.width//4, player.rect.y - comicSans.get_height()))

        for laser in laserList:
            screen.blit(assets["Laser"], laser.rect)

        screen.blit(scoreText, (25, 25))

    else:
        screen.fill(colors["Black"])
        if not gameStates["gameInit"] and not nameChoice["choosingName"]:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    save_data()
                    running = False
                elif event.type == pygame.KEYDOWN:
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
                    elif event.key == pygame.K_q:
                        running = False
                elif event.type == pygame.JOYDEVICEADDED:
                    joystick = pygame.joystick.Joystick(event.device_index)
                    joysticks.append(joystick)
                    joysticks_nb = pygame.joystick.get_count()
            
            for i in range(len(playerList)):
                if not len(joysticks) > i:
                    continue
                horiz_move_0 = joysticks[i].get_axis(0)
                vert_move_0 = joysticks[i].get_axis(1)
                if vert_move_0 > 0.2:
                    if joyCooldowns["VertUp"] <= 0:
                        joyCooldowns["VertUp"] = 30
                        keyVertMenu(1)
                elif vert_move_0 < -0.2:
                    if joyCooldowns["VertDown"] <= 0:
                        joyCooldowns["VertDown"] = 30
                        keyVertMenu(-1)
                if horiz_move_0 > 0.2:
                    if joyCooldowns["HorRight"] <= 0:
                        joyCooldowns["HorRight"] = 30
                        keyHorMenu(1)
                elif horiz_move_0 < -0.2:
                    if joyCooldowns["HorLeft"] <= 0:
                        joyCooldowns["HorLeft"] = 30
                        keyHorMenu(-1)

                for j in range(6):
                    if joysticks[i].get_button(j) and (i, j) not in joyCooldowns:
                        joyCooldowns[(i, j)] = 30
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
                                currentSelection = (currentSelection + 1) % settingsMenu["settings"]["Player Count"][2]
                                pSelectText = comicSans.render(f"Current player selection : P{currentSelection + 1}", False, colors["White"])
                                menusTexts["ColorsTexts"][2] = comicSans.render(f"Current color : {colorList[playerList[currentSelection].color]}", False, colors["White"])
                                menusTexts["SkinsTexts"][2] = comicSans.render(f"Current skin : {skinList[playerList[currentSelection].skin]}", False, colors["White"])
                
                if joysticks[i].get_hat(0)[1] == 1:
                    if joyCooldowns["VertUp"] <= 0:
                        joyCooldowns["VertUp"] = 30
                        keyVertMenu(1)
                if joysticks[i].get_hat(0)[1] == -1:
                    if joyCooldowns["VertDown"] <= 0:
                        joyCooldowns["VertDown"] = 30
                        keyVertMenu(-1)
                if joysticks[i].get_hat(0)[0] == 1:
                    if joyCooldowns["HorRight"] <= 0:
                        joyCooldowns["HorRight"] = 30
                        keyHorMenu(1)
                if joysticks[i].get_hat(0)[0] == -1:
                    if joyCooldowns["HorLeft"] <= 0:
                        joyCooldowns["HorLeft"] = 30
                        keyHorMenu(-1)

            screen.blit(menuSwitch["menuText"], (WIDTH//2 - menuSwitch["menuText"].get_width()//2, HEIGHT//2 - menuSwitch["menuText"].get_height()//2 - 200))

            pygame.draw.polygon(screen, colors["White"], [[WIDTH//2 - menuSwitch["menuText"].get_width()//2 - 50, HEIGHT//2 - 200], [WIDTH//2 - menuSwitch["menuText"].get_width()//2 - 25, HEIGHT//2 - 175], [WIDTH//2 - menuSwitch["menuText"].get_width()//2 - 25, HEIGHT//2 - 225]], 0)
            pygame.draw.polygon(screen, colors["White"], [[WIDTH//2 + menuSwitch["menuText"].get_width()//2 + 50, HEIGHT//2 - 200], [WIDTH//2 + menuSwitch["menuText"].get_width()//2 + 25, HEIGHT//2 - 175], [WIDTH//2 + menuSwitch["menuText"].get_width()//2 + 25, HEIGHT//2 - 225]], 0)

            for i, v in enumerate(menusTexts[f"{menuList[menuSwitch["currentMenu"]]}Texts"].values()):
                screen.blit(v, (WIDTH//2 - v.get_width()//2, HEIGHT//2 - v.get_height()//2 - 100 + menusOffset[menuList[menuSwitch["currentMenu"]]] + i * 40))
           
            if menuList[menuSwitch["currentMenu"]] == "Colors" or menuList[menuSwitch["currentMenu"]] == "Skins" or menuList[menuSwitch["currentMenu"]] == "Abilities" or menuList[menuSwitch["currentMenu"]] == "Stats":
                if settingsMenu["settings"]["Player Count"][2] > 1:
                    screen.blit(pSelectText, (WIDTH//2 - pSelectText.get_width()//2, HEIGHT//2 - pSelectText.get_height()//2 - 20))

            if menuList[menuSwitch["currentMenu"]] == "Colors" or menuList[menuSwitch["currentMenu"]] == "Skins":
                screen.blit(assets[f"{skinList[playerList[currentSelection].skin]}{colorList[playerList[currentSelection].color]}"], (WIDTH//2 - 25, HEIGHT//2 + 100))
            
            elif menuList[menuSwitch["currentMenu"]] == "Stats":
                for i, stat in enumerate(statsList):
                    statText = comicSans.render(f"{stat} : {getattr(playerList[currentSelection], statsVars["stats"][stat][2])}", False, colors[statsVars["stats"][stat][1]])
                    screen.blit(statText, (WIDTH//2 - statText.get_width()//2, HEIGHT//2 - statText.get_height()//2 + i * 50 + 75))
            
            elif menuList[menuSwitch["currentMenu"]] == "Settings":
                for i, setting in enumerate(settingsList):
                    screen.blit(settingsMenu["settings"][setting][0], (WIDTH//2 - settingsMenu["settings"][setting][0].get_width()//2, HEIGHT//2 - settingsMenu["settings"][setting][0].get_height()//2 + i * 50))

            elif menuList[menuSwitch["currentMenu"]] == "Abilities":
                screen.blit(assets[f"{abilitiesList[playerList[currentSelection].ability]}Icon"], (WIDTH//2 - assets[f"{abilitiesList[playerList[currentSelection].ability]}Icon"].get_width()//2, HEIGHT//2 + 100))
        
        elif not nameChoice["choosingName"]:
            for event in pygame.event.get():   
                if event.type == pygame.QUIT:
                    save_data()
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        gameStates["gameStarted"] = not gameStates["gameStarted"]
                    if event.key == pygame.K_q:
                        running = False
                elif event.type == pygame.JOYDEVICEADDED:
                    joystick = pygame.joystick.Joystick(event.device_index)
                    joysticks.append(joystick)
                    joysticks_nb = pygame.joystick.get_count()
            
            for i in range(len(playerList)):
                if not len(joysticks) > i:
                    continue
                for j in range(8):
                    if joysticks[i].get_button(j) and (i, j) not in joyCooldowns:
                        joyCooldowns[(i, j)] = 30
                        gameStates["gameStarted"] = not gameStates["gameStarted"]   
                if joysticks[i].get_hat(0)[1] == 1:
                    if joyCooldowns["VertUp"] <= 0:
                        joyCooldowns["VertUp"] = 30
                        gameStates["gameStarted"] = not gameStates["gameStarted"]
                if joysticks[i].get_hat(0)[1] == -1:
                    if joyCooldowns["VertDown"] <= 0:
                        joyCooldowns["VertDown"] = 30
                        gameStates["gameStarted"] = not gameStates["gameStarted"]
                if joysticks[i].get_hat(0)[0] == 1:
                    if joyCooldowns["HorRight"] <= 0:
                        joyCooldowns["HorRight"] = 30
                        gameStates["gameStarted"] = not gameStates["gameStarted"]
                if joysticks[i].get_hat(0)[0] == -1:
                    if joyCooldowns["HorLeft"] <= 0:
                        joyCooldowns["HorLeft"] = 30
                        gameStates["gameStarted"] = not gameStates["gameStarted"]

            screen.blit(pauseText, (WIDTH//2 - pauseText.get_width()//2, HEIGHT//2 - pauseText.get_height()//2))

        else:
            for event in pygame.event.get():   
                if event.type == pygame.QUIT:
                    save_data()
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a:
                        keyEnterName()
                    elif event.key == pygame.K_TAB:
                        keyTabName()
                    elif event.key == pygame.K_UP:
                        keyChangeLetter(1)
                    elif event.key == pygame.K_DOWN:
                        keyChangeLetter(-1)
                    elif event.key == pygame.K_q:
                        running = False
                elif event.type == pygame.JOYDEVICEADDED:
                    joystick = pygame.joystick.Joystick(event.device_index)
                    joysticks.append(joystick)
                    joysticks_nb = pygame.joystick.get_count()

            for i in range(len(playerList)):
                if not len(joysticks) > i:
                    continue
                horiz_move_0 = joysticks[i].get_axis(0)
                vert_move_0 = joysticks[i].get_axis(1)
                if vert_move_0 > 0.2:
                    if joyCooldowns["VertUp"] <= 0:
                        joyCooldowns["VertUp"] = 30
                        keyChangeLetter(1)
                elif vert_move_0 < -0.2:
                    if joyCooldowns["VertDown"] <= 0:
                        joyCooldowns["VertDown"] = 30
                        keyChangeLetter(-1)
                if horiz_move_0 > 0.2:
                    if joyCooldowns["VertUp"] <= 0:
                        joyCooldowns["VertUp"] = 30
                    keyTabName(1)
                elif horiz_move_0 < -0.2:
                    if joyCooldowns["VertDown"] <= 0:
                        joyCooldowns["VertDown"] = 30
                        keyTabName(-1)

                for j in range(5):
                    if joysticks[i].get_button(j) and (i, j) not in joyCooldowns:
                        joyCooldowns[(i, j)] = 30
                        if j == 0:
                            keyChangeLetter(1)
                        elif j == 1:
                            keyChangeLetter(-1)
                        elif j == 2:
                            keyTabName(1)
                        elif j == 3:
                            keyTabName(-1)
                        elif j == 4:
                            keyEnterName()
                
                if joysticks[i].get_hat(0)[1] == 1:
                    if joyCooldowns["VertUp"] <= 0:
                        joyCooldowns["VertUp"] = 30
                        keyChangeLetter(1)
                if joysticks[i].get_hat(0)[1] == -1:
                    if joyCooldowns["VertDown"] <= 0:
                        joyCooldowns["VertDown"] = 30
                        keyChangeLetter(-1)
                if joysticks[i].get_hat(0)[0] == 1:
                    if joyCooldowns["HorRight"] <= 0:
                        joyCooldowns["HorRight"] = 30
                        keyTabName(1)
                if joysticks[i].get_hat(0)[0] == -1:
                    if joyCooldowns["HorLeft"] <= 0:
                        joyCooldowns["HorLeft"] = 30
                        keyTabName(-1)

            underscoreText = comicSans.render("_", False, colors["White"])

            screen.blit(comicSans.render("New High Score!", False, colors["White"]), (WIDTH//2 - comicSans.render("New High Score!", False, colors["White"]).get_width()//2, HEIGHT//2 - 100))
            screen.blit(comicSans.render(f"Your Score: {score}", False, colors["White"]), (WIDTH//2 - comicSans.render(f"Your Score: {score}", False, colors["White"]).get_width()//2, HEIGHT//2 - 50))
            screen.blit(comicSans.render("Enter your name and press a:", False, colors["White"]), (WIDTH//2 - comicSans.render("Enter your name and press a:", False, colors["White"]).get_width()//2, HEIGHT//2))
            for i in range(3):
                if nameChoice["currentLetter"] == i:
                    screen.blit(comicSans.render(nameChoice["chosenLetters"][i], False, colors["Red"]), (WIDTH//2 - underscoreText.get_width()//2 - 25 + i * 25, HEIGHT//2 + 50))
                else:
                    screen.blit(comicSans.render(nameChoice["chosenLetters"][i], False, colors["White"]), (WIDTH//2 - underscoreText.get_width()//2 - 25 + i * 25, HEIGHT//2 + 50))
    
    pygame.display.flip()
    dt = max(0.001, min(0.1, clock.tick(60)/1000))

pygame.quit()

save_data()