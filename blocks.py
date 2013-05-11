# Andrew Quintanilla
# Handles blocks
import pygame, random as rnd
from pygame.locals import *

white = (255,255,255)
black = (0,0,0)
grey_lite = (128,128,128)
yellow = (255,255,0)
layouts = dict([(1,(0,0,0,0)), (2,(0,0,0,1)), (3,(0,0,1,1)), (4, (1,0,1,1)),
               (5, (1,1,1,1)), (6, (0,1,0,1))])
tilesize = (45,45)
liningsize = (tilesize[0]-4,tilesize[1]-4)
innersize = (liningsize[0]-4,liningsize[1]-4)
flagliningsize = (tilesize[0]-2,tilesize[1]-2)
flaginnersize = (flagliningsize[0]-2,flagliningsize[1]-2)
griddimensions = (720,450)
gridsize = (16,12)
tiledropwait = 0.05

class BlockManager(pygame.sprite.Group):
    def __init__(self, color1, color2, wiperspeed, waitcount, xoffset=0,
                 yoffset=0):
        pygame.sprite.Group.__init__(self)
        self.color1 = color1
        self.color2 = color2
        self.waitcount = waitcount
        self.fallwait = 0.0
        self.tilewait = 0.0
        self.fallingblock = False
        self.droppingtiles = {}
        # Grid is initialized with the tuple of topleft corner of each cell
        # Points to tiles at locations
        self.grid = {}
        for i in range(16):
            for j in range(12):
                self.grid[(i,j)] = (xoffset+tilesize[0]*i,yoffset+tilesize[1]*(j-2))
        self.xoffset = xoffset
        self.yoffset = yoffset
        self.wiper = Wiper(wiperspeed,self.xoffset,self.yoffset)        
        self.gridlines = Gridlines(self.xoffset,self.yoffset)
        self.tilewiper = pygame.Surface(tilesize)
        self.dmanager = DestructionManager()
        self.layoutqueue = LayoutQueue()

    def KeydownHandler(self, key):
        if key == K_x:
            self.block.RotateClockwise()
        elif key == K_z:
            self.block.RotateCounterclockwise()
        elif key == K_RIGHT:
            self.block.MoveRight()
            if self.CheckBlockCollision():
                self.block.MoveLeft()
        elif key == K_LEFT:
            self.block.MoveLeft()
            if self.CheckBlockCollision():
                self.block.MoveRight()
        elif key == K_DOWN:
            self.oldwaitcount = self.waitcount
            self.waitcount = 0.08

    def KeyupHandler(self, key):
        if key == K_DOWN:
            self.waitcount = self.oldwaitcount

    def CheckBlockCollision(self):
        if pygame.sprite.groupcollide(self.block,self,False,False):
            return True
        elif self.block.x < self.xoffset:
            return True
        elif self.block.x > self.xoffset+griddimensions[0]-2*tilesize[0]:
            return True
        elif self.block.y > self.yoffset+griddimensions[1]-2*tilesize[1]:
            return True
        else:
            return False

    def CheckTileCollision(self,tile):
        if pygame.sprite.spritecollide(tile,self,False):
            return True
        elif tile.rect.bottom > griddimensions[1]+self.yoffset:
            return True
        else:
            return False
        
    # If 2x2 is found, tiles in 2x2 are flagged
    def Check2x2(self,tile):
        loc = tile.grid
        locbelow = (loc[0],loc[1]+1)
        locleft = (loc[0]-1,loc[1])
        locright = (loc[0]+1,loc[1])
        locbelowleft = (loc[0]-1,loc[1]+1)
        locbelowright = (loc[0]+1,loc[1]+1)
        if loc[1] < gridsize[1]-1:
            if not isinstance(self.grid[locbelow],tuple) and \
               self.grid[locbelow].color1 == tile.color1:
                # Check tiles to the left
                if loc[0] > 0 and \
                   not (isinstance(self.grid[locleft],tuple) or \
                        isinstance(self.grid[locbelowleft],tuple)) and \
                        self.grid[locleft].color1 == tile.color1 and \
                        self.grid[locbelowleft].color1 == tile.color1:
                    tile.Flag(1)
                    self.grid[locleft].Flag(0)
                    self.grid[locbelow].Flag(2)
                    self.grid[locbelowleft].Flag(3)
                    templist = [tile, self.grid[locleft], self.grid[locbelow],\
                                self.grid[locbelowleft]]
                    
                    self.dmanager.add(templist)
                # Check tiles to the right
                if loc[0] < gridsize[0]-1 and \
                   not (isinstance(self.grid[locright],tuple) or \
                        isinstance(self.grid[locbelowright],tuple)) and \
                        self.grid[locright].color1 == tile.color1 and \
                        self.grid[locbelowright].color1 == tile.color1:
                    tile.Flag(0)
                    self.grid[locright].Flag(1)
                    self.grid[locbelow].Flag(3)
                    self.grid[locbelowright].Flag(2)
                    templist = [tile,self.grid[locright],self.grid[locbelow],\
                                self.grid[locbelowright]]
                    self.dmanager.add(templist)

    def update(self, time):        
        if self.fallingblock:
            if self.fallwait < self.waitcount:
                self.fallwait += time
            else:
                self.block.MoveDown()
                self.fallwait = 0.0
                # Triggers when a block lands
                if self.CheckBlockCollision():
                    self.block.MoveUp()
                    self.fallingblock = False
                    for sp in self.block.sprites():
                        self.grid[sp.grid] = sp
                        self.add(sp)
                        if not sp.grid[0] in self.droppingtiles:
                            self.droppingtiles[sp.grid[0]] = []
                        self.droppingtiles[sp.grid[0]].append(sp.grid[1])
                    self.block.empty()
        else:
            self.block = Block(self.color1,self.color2, self.layoutqueue.GetNext()\
                               ,griddimensions[0]/2-tilesize[0]+self.xoffset,
                               self.yoffset-tilesize[1]*2, (7,0))
            self.fallingblock = True
                        
        # Animates tiles dropping into gaps
        if self.droppingtiles:
            if self.tilewait < tiledropwait:
                self.tilewait += time
            else:
                droplist = []
                for x in self.droppingtiles:
                    self.droppingtiles[x].sort()
                    self.droppingtiles[x].reverse()
                    for y in self.droppingtiles[x]:
                        loc = gridsize[1]-1
                        temp = self.grid[(x,y)]
                        for j in range(temp.grid[1]+1,gridsize[1]):
                            if not isinstance(self.grid[(temp.grid[0],j)],tuple):
                                loc = j-1
                                break
                        if loc != temp.grid:
                            self.swap((temp.grid[0],loc),temp)
                        droplist.append(temp)
                for sp in droplist:
                    self.Check2x2(sp)
                self.droppingtiles.clear()
                self.tilewait = 0.0           
        
        self.wiper.update(time)
        topdict=self.dmanager.update(self.wiper.sprite, self.grid)
        # For each x, adds tiles above top y to drop list
        for x in topdict:
            for y in range(0,topdict[x]):
                if not isinstance(self.grid[(x,y)],tuple):
                    if not self.grid[(x,y)].grid[0] in self.droppingtiles:
                        self.droppingtiles[self.grid[(x,y)].grid[0]] = []
                    self.droppingtiles[self.grid[(x,y)].grid[0]].append(\
                        self.grid[(x,y)].grid[1])
                
        for sp in pygame.sprite.spritecollide(self.wiper.sprite,self,False):
            if sp.flagged:
                self.tilewiper.fill(sp.color1)
                sp.image.blit(self.tilewiper, \
                    (self.wiper.sprite.rect.left-sp.rect.left-tilesize[0]+3,0))

    def draw(self, Surface):
        self.gridlines.draw(Surface)
        pygame.sprite.Group.draw(self,Surface)
        self.block.draw(Surface)
        self.wiper.draw(Surface)

    # Places tile into grid at gridloc, old location goes back to initial value
    def swap(self, gridloc, tile):
        self.grid[tile.grid] = tile.rect.topleft
        tile.rect.topleft = self.grid[gridloc]
        tile.grid = gridloc
        self.grid[gridloc] = tile

class DestructionManager():
    def __init__(self):
        self.destroyers = []

    def add(self, sprites):
        added = False
        if len(self.destroyers) > 1:
            for dst in self.destroyers:
                for sp in sprites:
                    if sp in dst:
                        dst.addtiles(sprites)
                        return
        self.destroyers.append(TileDestroyer())
        self.destroyers[-1].addtiles(sprites)

    def update(self, wiper, grid):
        lowestYs = {}
        for dst in self.destroyers:
            temp=dst.update(wiper, grid)
            if temp:
                for x in temp:
                    if not x in lowestYs or temp[x] > lowestYs[x]:
                        lowestYs[x] = temp[x]
            if not dst.sprites():
                self.destroyers.remove(dst)
        return lowestYs

    def clear(self):
        self.destroyers[:] = []
                
class TileDestroyer(pygame.sprite.Group):
    def __init__(self):
        pygame.sprite.Group.__init__(self)
        self.maxX = 0
        self.killready = False
        self.kill = False

    def addtiles(self, sprites):
        for sprite in sprites:
            self.add(sprite)
            if sprite.rect.right > self.maxX:
                self.maxX = sprite.rect.right

    # If blocks are killed, returns a dict holding the lowest y for each x
    def update(self, wiper, grid):
        if pygame.sprite.spritecollideany(wiper,self):
            if self.killready:
                self.kill = True
        else:
            if self.kill:
                lowestYs = {}
                for sp in self.sprites():
                    if not sp.grid[0] in lowestYs:
                        lowestYs[sp.grid[0]] = sp.grid[1]
                    elif sp.grid[1] < lowestYs[sp.grid[0]]:
                        lowestYs[sp.grid[0]] = sp.grid[1]
                    grid[(sp.grid)] = sp.rect.topleft
                    sp.kill()
                return lowestYs
            else:
                self.killready = True

# Queue of layouts to use in new blocks
class LayoutQueue():
    def __init__(self):
        self.length = 4
        self.FillQueueTest()

    # Fills Queue
    def FillQueue(self):
        self.blocks = []
        for i in range(self.length):
            self.blocks.append(rnd.randint(1,6))

    # Fills queue with predetermined layouts for testing purposes
    def FillQueueTest(self):
        self.blocks = [1,2,6,1]

    def GetNext(self):
        layout = self.blocks.pop(0)
        self.blocks.append(rnd.randint(1,6))
        return layout

class Tile(pygame.sprite.Sprite):
    def __init__(self, color1, color2):
        pygame.sprite.Sprite.__init__(self)
        self.color1 = color1
        self.color2 = color2
        self.image = pygame.Surface(tilesize)
        self.image.fill(color1)
        lining = pygame.Surface(liningsize)
        lining.fill(color2)
        inner = pygame.Surface(innersize)
        inner.fill(color1)
        self.image.blit(lining,(2,2))
        self.image.blit(inner,(4,4))
        self.rect = self.image.get_rect()
        self.grid = (0,0)
        self.flagged = False

    def MoveLeft(self):
        self.rect.left -= tilesize[0]
        self.grid = (self.grid[0]-1,self.grid[1])

    def MoveRight(self):
        self.rect.left += tilesize[0]
        self.grid = (self.grid[0]+1,self.grid[1])
        
    def MoveDown(self):
        self.rect.top += tilesize[1]
        self.grid = (self.grid[0],self.grid[1]+1)

    def MoveUp(self):
        self.rect.top -= tilesize[1]
        self.grid = (self.grid[0],self.grid[1]-1)

    # Flags tiles according to position in 2x2
    # 0: Top left
    # 1: Top right
    # 2: Bottom right
    # 3: Bottom left
    def Flag(self,pos):
        self.flagged = True
        self.image.fill(self.color1)
        lining = pygame.Surface(flagliningsize)
        inner = pygame.Surface(flaginnersize)
        lining.fill(self.color2)
        inner.fill(self.color1)
        if pos == 0:
            self.image.blit(lining,(2,2))
            self.image.blit(inner,(4,4))
        elif pos == 1:
            self.image.blit(lining,(0,2))
            self.image.blit(inner,(0,4))
        elif pos == 2:
            self.image.blit(lining,(0,0))
            self.image.blit(inner,(0,0))
        else:
            self.image.blit(lining,(2,0))
            self.image.blit(inner,(4,0))            

# Returns a random block, tiles arraged
# 0 1
# 3 2
class Block(pygame.sprite.Group):
    def __init__(self, color1, color2, lay, x=0, y=0, grid=(0,0)):
        pygame.sprite.Group.__init__(self)
        if lay >= 0 and lay <= 6:
            layout = layouts[lay]
        else:
            layout = layouts[rnd.randint(1,6)]        
        # x and y are the coordinates of the top left corner of block
        for i in layout:
            if i == 0:
                self.add(Tile(color1,color2))
            else:
                self.add(Tile(color2,color1))
        self.tiledict = {}        
        for i in range(4):
            if i == 0:
                self.sprites()[i].rect.left = x
                self.sprites()[i].rect.top = y
                self.sprites()[i].grid = grid
            elif i == 1:
                self.sprites()[i].rect.left = x + tilesize[0]
                self.sprites()[i].rect.top = y
                self.sprites()[i].grid = (grid[0]+1,grid[1])
            elif i == 2:
                self.sprites()[i].rect.left = x + tilesize[0]
                self.sprites()[i].rect.top = y + tilesize[1]
                self.sprites()[i].grid = (grid[0]+1,grid[1]+1)
            else:
                self.sprites()[i].rect.left = x
                self.sprites()[i].rect.top = y + tilesize[1]
                self.sprites()[i].grid = (grid[0],grid[1]+1)
            self.tiledict[i]=self.sprites()[i]
        self.x = self.sprites()[0].rect.left
        self.y = self.sprites()[0].rect.top

    def RotateCounterclockwise(self):
        self.tiledict[0].MoveDown()
        self.tiledict[1].MoveLeft()
        self.tiledict[2].MoveUp()
        self.tiledict[3].MoveRight()
        s0 = self.tiledict[0]
        s1 = self.tiledict[1]
        s2 = self.tiledict[2]
        s3 = self.tiledict[3]
        self.tiledict[0] = s1
        self.tiledict[1] = s2
        self.tiledict[2] = s3
        self.tiledict[3] = s0

    def RotateClockwise(self):
        self.tiledict[0].MoveRight()
        self.tiledict[1].MoveDown()
        self.tiledict[2].MoveLeft()
        self.tiledict[3].MoveUp()
        s0 = self.tiledict[0]
        s1 = self.tiledict[1]
        s2 = self.tiledict[2]
        s3 = self.tiledict[3]
        self.tiledict[0] = s3
        self.tiledict[1] = s0
        self.tiledict[2] = s1
        self.tiledict[3] = s2

    def MoveRight(self):
        x_list = []
        for sp in self.sprites():
            sp.MoveRight()
            x_list.append(sp.rect.left)
        if x_list:
            self.x = min(x_list)

    def MoveLeft(self):
        x_list = []
        for sp in self.sprites():
            sp.MoveLeft()
            x_list.append(sp.rect.left)
        if x_list:
            self.x = min(x_list)

    def MoveDown(self):
        y_list = []
        for sp in self.sprites():
            sp.MoveDown()
            y_list.append(sp.rect.top)
        if y_list:
            self.y = min(y_list)

    def MoveUp(self):
        y_list = []
        for sp in self.sprites():
            sp.MoveUp()
            y_list.append(sp.rect.top)
        if y_list:
            self.y = min(y_list)
        

class Line(pygame.sprite.Sprite):
    def __init__(self, size, pos):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface(size)
        self.image.fill(grey_lite)
        self.rect = self.image.get_rect()
        self.rect.topleft = pos
        
# Draws grid of 15 vertical lines x 9 horizontal lines
class Gridlines(pygame.sprite.Group):
    def __init__(self, xoffset=0, yoffset=0):
        pygame.sprite.Group.__init__(self)
        for i in range(0,11):
            self.add(Line((griddimensions[0]+2,2),(xoffset-1,45*i-1+yoffset)))
        for i in range(0,17):
            self.add(Line((2,griddimensions[1]+1),(45*i-1+xoffset,yoffset)))

# The line that wipes out blocks
class Wiper(pygame.sprite.GroupSingle):
    def __init__(self, speed, xoffset=0, yoffset=0):
        pygame.sprite.GroupSingle.__init__(self)
        self.sprite = pygame.sprite.Sprite()
        self.sprite.image = pygame.Surface((2,450))
        self.sprite.image.fill(yellow)
        self.sprite.rect = self.sprite.image.get_rect()
        self.xoffset = xoffset
        self.sprite.rect.topleft = (xoffset,yoffset)
        
        # Velocity is measured in pixels per second
        self.speed = speed
        self.left_float = 0.0+self.sprite.rect.left

    def update(self, time):
        self.left_float = self.left_float + self.speed*time
        if (self.left_float > 719+self.xoffset):
            self.left_float = 0.0+self.xoffset
        self.sprite.rect.left = self.left_float
        
