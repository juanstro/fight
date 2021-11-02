import pygame
import os
'''
Juan Castro

FIX: User can click faster than the animation of attacking
- Should implement a click-delay or wait time, to simulate a cooldown.
'''
class Game:
    def __init__(self, run=True, w=550, h=280, fps=60):
        pygame.init()
        self.run = run
        self.width = w
        self.height = h
        # Create global variable screen; other classes must be able to access the screen
        global green, red
        # RGB Colors
        green, red = (0,255,0),(255,0,0)
        # Create the screen
        global screen
        screen = pygame.display.set_mode((w,h))

        self.clock = pygame.time.Clock()
        self.fps = fps
        self.background = pygame.image.load("pic/bg/bg.png").convert()

        # Create enemy attack event
        global enemyAttackEvent
        # 3 sec delay between attacks
        enemy_delay = 3000 # 3000 ms = 3 sec
        enemyAttackEvent = pygame.USEREVENT
        pygame.time.set_timer(enemyAttackEvent, enemy_delay)
        self.victoryBanner = pygame.image.load("pic/banners/victory.png").convert_alpha()
        self.defeatBanner = pygame.image.load("pic/banners/defeat.png").convert_alpha()

    def setCaption(self):
        pygame.display.set_caption("Fight!")

    def drawBackg(self):
        screen.blit(self.background, (0,0))
    
    def drawBanner(self, win):
        if win == True:
            # x = 90, y = 10; had to readjust until perfect location
            screen.blit(self.victoryBanner, (90,10))
        elif win == False:
            # x = 120, y = 10
            screen.blit(self.defeatBanner, (120,10))

    def setSounds(self):
        # Set-up the music
        pygame.mixer.music.load("sounds/background.wav")
        # Passing -1 as an argument ensures the music will indefinitely play
        pygame.mixer.music.play(-1)
        # Set volume to 0.25
        pygame.mixer.music.set_volume(0.15)

        # Sounds may need to be used in gameLoop (game class), Entity (enemy/hero) classes, 
        global sounds
        sounds = []
        i = 0
        for sound in ["heroAttack", "heroAttackGrunt", "heroDeath","enemyAttack","enemyDeath","victory","defeat"]:
            sounds.append(pygame.mixer.Sound(f"sounds/{sound}.wav"))
            # Set the volume for each sound (value between 0.0 - 1.0)
            sounds[i].set_volume(0.2)
            ++i

    def gameLoop(self):
        end = False
        self.setSounds()
        # Set the caption
        self.setCaption()
        # Create hero and enemy objects
        hero = Hero()
        enemy = Enemy()

        # While self.run == True, continue to run until run == False
        while self.run:
            # Set frames per sec.
            self.clock.tick(self.fps)
            # Draw background
            
            self.drawBackg()
            if end == True:
                self.drawBanner(hero.alive)

            hero.control(enemy, end)
            enemy.update(end)
            
            
            # Quit game
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run = False
                # User / Enemy can ONLY attack if both are alive (if and only if both conditions are true)
                if enemy.alive == True and hero.alive == True:
                    if event.type == enemyAttackEvent:
                        enemy.attack(hero)
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        hero.attack(enemy)
                if not hero.alive or not enemy.alive:
                    end = True

            # Update display
            pygame.display.update()
        pygame.quit()

class Entity:
    def __init__(self, name, maxHp, x, y):
        self.name = name
        self.hp = maxHp
        self.maxHp = maxHp
        self.x = x
        self.y = y
        # An array to collect all of the animation frames/imgs
        self.animationStates = []

        self.alive = True


        self.updateTime = pygame.time.get_ticks()

        # Initalize state/idx to 0
        self.state = 0  # 0 idle, 1 atk, 2 hurt, 3 die, 4/5 walk/flip
        self.imgIdx = 0

        self.loadFrames() 

    def loadFrames(self):
        states = ["idle","attack","hurt","die","walk"]

        # Load in all the images(frames) for states : idle, attack, hurt, die, and walk
        for state in states:
            curr, currF = [], []
            for i in range(len(os.listdir(f"pic/{self.name}/{state}"))):
                image = pygame.image.load(f"pic/{self.name}/{state}/{i}.png")
                image = pygame.transform.scale(image, (image.get_width()*2, image.get_height()*2))
                flip = pygame.transform.flip(image, True, False)
                # Append the scaled image to the curr (temporary) list
                curr.append(image)
                currF.append(flip)
            # Append the curr list to animationStates (will become a multi-dimensional array)
            self.animationStates.append(curr)
            # Only accepting the flipped-walk animations; Will include more flipped-animations in the future:
            if state in ['walk']:
                self.animationStates.append(currF)

        
        self.image = self.animationStates[0][0] 
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)
        
    def update(self, end):
        if end == False:
            self.drawHealth()
        # Sets animation cooldown; 70 is some arbitrary value
        cooldown = 70

        # Set the image to the current state/frame we are on
        self.image = self.animationStates[self.state][self.imgIdx]

        # Must ensure that the time since the last update is > cooldown time -> for animation cooldown
        if pygame.time.get_ticks() - self.updateTime > cooldown:
            self.updateTime = pygame.time.get_ticks()
            # If we have not reached the last frame of the animation state, then ++ to the imgIdx
            if self.imgIdx < len(self.animationStates[self.state]):
                self.imgIdx += 1
    
            
        # If we reached the last frame of the animated state:
        if self.imgIdx >= len(self.animationStates[self.state]):
            # If dead, then set imgIdx to last frame of animation state.
            if self.state == 3:
                self.imgIdx = len(self.animationStates[self.state]) - 1
                pass
            # Reset back to start of animation
            else:
                self.state = 0
                self.imgIdx = 0
        screen.blit(self.image, self.rect)
    
    def die(self):
        pygame.mixer.music.fadeout(0)
        self.alive = False
        # Sets to death state
        self.state = 3
        self.imgIdx = 0
        self.updateTime = pygame.time.get_ticks()
        end = True
        if self.name == "hero":
            # Hero death sound
            sounds[2].play()
            # Defeat sound
            sounds[6].play()
        else:
            # Enemy death sound
            sounds[4].play()
            # Victory sound
            sounds[5].play()


class Hero(Entity):
    def __init__(self, name="hero", maxHp=30, x=125, y=115):
        super().__init__(name, maxHp, x, y)
    
    def control(self, enemy, end):
        dx = dy = 0
        # Get user- keypresses
        key = pygame.key.get_pressed()
        if enemy.alive == True and self.alive == True:
            # A moves hero to the left
            if key[pygame.K_a] and self.x > 60:
                dx -= 3
                self.state = 5
            # D key moves hero right
            if key[pygame.K_d] and self.x < 380:
                dx += 3
                self.state = 4
            self.x += dx
            self.y += dy

        self.rect.center = (self.x, self.y)
        super().update(end)

    def attack(self, enemy):
        # The user's attacks can only damage the enemy if they are within 30 units
        if enemy.x - self.x <= 30:
            enemy.hp -= 2 # Could change this value to a initalized value (self.damage)
            if enemy.hp <= 0:
                enemy.die()
        self.state = 1
        sounds[1].play()
        sounds[0].play()

    def drawHealth(self):
        per = self.hp/self.maxHp
        pygame.draw.rect(screen, red, (self.x - 50, self.y - 50, 100, 10))
        pygame.draw.rect(screen, green, (self.x - 50, self.y - 50, 100 * per, 10))

class Enemy(Entity):
    def __init__(self, name="enemy", maxHp=50, x=375, y=60):
        super().__init__(name, maxHp, x, y)
    
    def drawHealth(self):
        per = self.hp/self.maxHp
        pygame.draw.rect(screen, red, (self.x - 25, self.y - 50, 175, 15))
        pygame.draw.rect(screen, green, (self.x - 25, self.y - 50, 175 * per, 15))
    
    def attack(self, hero):
        # If user is within 95 units (pixels?), enemy is triggered to attack hero
        if self.x - hero.x <= 95:
            # Sets to attack state
            self.state = 1 

            # Change this to an initalized value (self.damage); could progressively increase by levels?
            hero.hp -= 10
            sounds[3].play()
            if hero.hp <= 0:
                hero.die()
    

def main():
    game = Game()
    # Game loop should create the entities
    game.gameLoop()

if __name__ == "__main__":
    main()
