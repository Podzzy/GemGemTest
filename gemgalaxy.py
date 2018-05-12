import random, time, pygame, sys, copy
from pygame.locals import *

FPS = 30
WINDOWWIDTH = 600
WINDOWHEIGHT = 600

BOARDWIDTH = 8
BOARDHEIGHT = 8
GEMSIZE = 64

GEMNUM = 7
assert GEMNUM >= 5 #game needs at least 5 gems to work

SOUNDNUM = 6

MOVERATE = 25 #1 to 100. Higher means faster animation
DEDUCTSPEED = 0.8 #Reduce score by 1 every DEDUCTSPEED seconds

#COLOR       R   G   B
PURPLE    =(255,  0,255)
LIGHTBLUE =(170,190,255)
BLUE      =(  0,  0,255)
BLACK     =(  0,  0,  0)
RED       =(255,  0,  0)
BROWN     =( 85, 65,  0)

HIGHLIGHTCOLOR = PURPLE #Color of selected gem's border
BGCOLOR = LIGHTBLUE
GRIDCOLOR = BLUE
GAMEOVERTEXTCOLOR = RED
GAMEOVERBGCOLOR = BLACK
SCORECOLOR = BROWN

XMARGIN = int((WINDOWWIDTH - GEMSIZE * BOARDWIDTH) / 2)
YMARGIN = int((WINDOWHEIGHT - GEMSIZE * BOARDHEIGHT) / 2)

UP = 'up'
DOWN = 'down'
LEFT = 'left'
RIGHT = 'right'

EMPTY_SPACE = -1
ROWABOVEBOARD = 'row above board'

def main():
    global FPSCLOCK, DISPLAYSURF, GEMIMAGES, GAMESOUNDS, BASICFONT, BOARDRECTS

    #Initial setup
    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
    pygame.display.set_caption("Gem Galaxy")
    BASICFONT = pygame.font.Font('freesansbold.ttf',36)

    #Load images
    GEMIMAGES = []
    for i in range(1, GEMNUM + 1):
        gemImage = pygame.image.load('gem%s.png' % i)
        if gemImage.get_size() != (GEMSIZE, GEMSIZE):
            gemImage = pygame.tramsform.smoothscale(gemImage, (GEMSIZE, GEMSIZE))
        GEMIMAGES.append(gemImage)

    #Load the sounds
    GAMESOUNDS = {}
    GAMESOUNDS['bad swap'] = pygame.mixer.Sound('badswap.wav')
    GAMESOUNDS['match'] = []
    for i in range(SOUNDNUM):
        GAMESOUNDS['match'].append(pygame.mixer.Sound('match%s.wav' % i))


    #Make pygame.Rect object for each space on the board
    #Coordinate calculations for pixel to board               
    BOARDRECTS = []
    for x in range(BOARDWIDTH):
        BOARDRECTS.append([])
        for y in range(BOARDHEIGHT):
            r = pygame.Rect((XMARGIN + (x * GEMSIZE),
                             YMARGIN + (y * GEMSIZE),
                             GEMSIZE, GEMSIZE))
            BOARDRECTS[x].append(r)

    while True:
        runGame()

def runGame():
    #Play through a single game. When game is over, function returns

    #Set up the board
    gameBoard = getBlankBoard()
    score = 0
    fillBoardAndAnimate(gameBoard,[],score)

    #Initialize variables for new game
    firstSelectedGem = None
    lastMouseDownX = None
    lastMouseDownY = None
    gameIsOver = False
    lastScoreDeduction = time.time()
    continueTextSurf = None

    while True: #MAIN GAME LOOP
        clickedSpace = None

        
        for event in pygame.event.get():
            if event.type == QUIT or (KEYUP == event.type and K_ESCAPE == event.key):
                pygame.quit()
                sys.exit()
            elif event.type == KEYUP and event.key == K_BACKSPACE:
                return
            elif event.type == MOUSEBUTTONUP:
                if gameIsOver:
                    return
                if event.pos == (lastMouseDownX, lastMouseDownY):
                    clickedSpace = checkForGemClick(event.pos)
                else:
                    #This is for mouse dragging the mouse
                    firstSelectedGem = checkForGemClick((lastMouseDownX, lastMouseDownY))
                    clickedSpace = checkForGemClick(event.pos)
                    if not firstSelectedGem or not clickedSpace:
                        #if not a valid drag, don't select either space
                        firstSelectedGem = None
                        clickedSpace = None
            elif event.type == MOUSEBUTTONDOWN:
                #this is the start of a mouse click or mouse drag
                lastMouseDownX, lastMouseDownY = event.pos
        
        if clickedSpace and not firstSelectedGem:
            #This is the first gem clicked on
            firstSelectedGem = clickedSpace
        elif clickedSpace and firstSelectedGem:
            #Two gems are clicked on and selected. Swap the gems
            swapGem1, swapGem2 = getSwappingGems(gameBoard, firstSelectedGem, clickedSpace)
            if swapGem1 == None and swapGem2 == None:
                firstSelectedGem = None
                continue

            #Show the swap animation
            boardCopy = getBoardCopyNoGems(gameBoard, (swapGem1, swapGem2))
            animateMovingGems(boardCopy, [swapGem1, swapGem2],[], score)

            #Swap the gems in the board data structure

        #Draw the board
        DISPLAYSURF.fill(BGCOLOR)
        drawBoard(gameBoard)
        ############################################################################################################################################
        drawScore(score)
        pygame.display.update()
        FPSCLOCK.tick(FPS)
            

def fillBoardAndAnimate(board, points, score):
    dropSlots = getDropSlots(board)
    while dropSlots != [[]] * BOARDWIDTH:
        #do the dropping animation as long as there are more gems to drop
        movingGems = getDroppingGems(board)
        for x in range(len(dropSlots)):
            if len(dropSlots[x]) != 0:
                #cause lowest gem in each slot to move DOWN
                movingGems.append({'imageNum': dropSlots[x][0], 'x':x, 'y':ROWABOVEBOARD, 'direction':DOWN})
                
        boardCopy = getBoardCopyNoGems(board, movingGems)
        animateMovingGems(boardCopy, movingGems, points, score)
        moveGems(board, movingGems)

        #Make the next row of gems from drop slots
        #Delete previous lowest gems
        for x in range(len(dropSlots)):
            if len(dropSlots[x]) == 0:
                continue
            board[x][0] = dropSlots[x][0]
            del dropSlots[x][0]
            
            
    





def animateMovingGems(board, gems, pointsText, score):
    #pointsText is a dictionary with keys 'x', 'y', and 'pointers'
    progress = 0
    while progress<100: #animation loop
        DISPLAYSURF.fill(BGCOLOR)
        drawBoard(board)
        for gem in gems: #Loop through gem list and draw each one
            drawMovingGem(gem, progress)
        drawScore(score)
        



def drawScore(score):
    scoreImg = BASICFONT.render(str(score), 1, SCORECOLOR)
    scoreRect = scoreImg.get_rect()
    scoreRect.bottomleft = (10, WINDOWHEIGHT - 6)
    DISPLAYSURF.blit(scoreImg, scoreRect)



        
def drawMovingGem(gem, progress):
    #Draw a gem sliding in the direction its 'direction' key says.
    moveX = 0
    moveY  = 0
    progress = progress * 0.01

    if gem['direction'] == UP:
        moveY = - int(progress * GEMSIZE)
    elif gem['direction'] == DOWN:
        moveY = int(progress * GEMSIZE)
    elif gem['direction'] == LEFT:
        moveX = - int(progress * GEMSIZE)
    elif gem['direction'] == RIGHT:
        moveX = int(progress * GEMSIZE)

    baseX = gem['x']
    baseY = gem['y']
    if baseY == ROWABOVEBOARD:
        baseY = -1

    pixelX = XMARGIN + (baseX * GEMSIZE)
    pixelY = YMARGIN + (baseY * GEMSIZE)

    r = pygame.Rect( (pixelX + moveX, pixelY + moveY, GEMSIZE, GEMSIZE) )
    DISPLAYSURF.blit(GEMIMAGES[gem['imageNum']], r)
    




        
            

def drawBoard(board):
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            pygame.draw.rect(DISPLAYSURF, GRIDCOLOR, BOARDRECTS[x][y], 1)
            gemToDraw = board[x][y]
            if gemToDraw != EMPTY_SPACE:
                DISPLAYSURF.blit(GEMIMAGES[gemToDraw], BOARDRECTS[x][y])

def getBoardCopyNoGems(board, gems):
    #Create and return copy of the board data structure without gems
    #Gems is a list of dictionaries with keys: x,y direction, imageNum

    boardCopy = copy.deepcopy(board)
    #Remove some of the gems
    for gem in gems:
        if gem['y'] != ROWABOVEBOARD:
            boardCopy[gem['x']][gem['y']] = EMPTY_SPACE
            return boardCopy

def canMakeMove(board):
    #Return True if the board is in a state where a matching
    #move can be made on it. Otherwise return False.

    #The patterns in oneOffPatters represent the gems that are configured
    #in a way where it only one move to make a triplet.
    oneOffPatterns = (((0,1), (1,0), (2,0)),
                      ((0,1), (1,1), (2,0)),
                      ((0,0), (1,1), (2,0)),
                      ((0,1), (1,0), (2,0)),
                      ((0,0), (1,0), (2,1)),
                      ((0,0), (1,1), (2,1)),
                      ((0,0), (0,2), (0,3)),
                      ((0,0), (0,1), (0,3)))
    
    # The x and y variables interate over each space on the board.
    # If we use + to represent the currentlu interated space on the
    # board, then this pattern: ((0,1), (1,0), (2,0)) refers to identical
    # gems being set like this:
    #
    #   +A
    #   B
    #   C
    #
    # That is, gem A is offset from the + by (0,1), gem B is offset by (1,0),
    # and gem C is offset by (2,0). In this case,  gem A can be swapped to the left
    # to form a vertical three-in-a-row triplet.
    #
    # There are eight possible ways for the gems to be one move away from forming
    # a triple, hence oneOffPattern has 8 patterns.

    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            for pat in oneOffPatters:
                # check each possible pattern of"match in next move"
                # to see if a possible move can be made.
                if (getGemAt(board, x+pat[0][0], y+pat[0][1]) == \
                    getGemAt(board, x+pat[1][0], y+pat[1][1]) == \
                    getGemAt(board, x+pat[2][0], y+pat[2][1]) != None) or \
                    (getGemAt(board, x+pat[0][1], y+pat[1][0]) == \
                    getGemAt(board, x+pat[1][1], y+pat[1][0]) == \
                    getGemAt(board, x+pat[2][1], y+pat[2][0]) != None):
                    return True # return True the first time you find a pattern
    return False # If you've gotten here, there are no matching patterns.
            



        

def getBlankBoard():
    #Create and return blank board data structure
    board = []
    for x in range(BOARDWIDTH):
        board.append([EMPTY_SPACE] * BOARDHEIGHT)
    return board

def checkForGemClick(pos):
    #Check to see if mouse click was on board
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            if BOARDRECTS[x][y].collidepoint(pos[0],pos[1]):
                return{'x':x, 'y':y}
    return None #Click was not on board

def getGemAt(board, x, y):
    if x < 0 or y < 0 or x >= BOARDWIDTH or y >= BOARDHEIGHT:
        return None
    else:
        return board[x][y]

def pullDownAllGems(board):
    # Pulls down all gems on the board to the bottom to fill any gaps
    for x in range(BOARDWIDTH):
        gemsInColumn= []
        for y in range(BOARDHEIGHT):
            if board[x][y] != EMPTY_SPACE:
                gemsInColumn.append(board[x][y])
        board[x] = ([EMPTY_SPACE] * (BOARDHEIGHT - len(gemsInColumn))) + gemsInColumn
        

def getDropSlots(board):
    # Creates a "drop slot" for each column and fills the slot with a
    # number of gems that column is lacking. This function assumes
    # that the gems have been gravity dropped already.
    boardCopy =  copy.deepcopy(board)
    pullDownAllGems(boardCopy)

    dropSlots = []
    for i in range(BOARDWIDTH):
        dropSlots.append([])

    # count the number of empty spaces in each column on the board
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT-1, -1, -1): # start from bottom, going up
            if boardCopy[x][y] == EMPTY_SPACE:
                possibleGems = list(range(len(GEMIMAGES)))
                for offsetX, offsetY in ((0, -1), (1, 0), (0, 1), (-1, 0)):
                    # Narrow down the possible gems we should put in rhe
                    # blank space so we don't end up putting an two of
                    # the same gems nect to each other when they drop.
                    neighborGem = getGemAt(boardCopy, x + offsetX, y + offsetY)
                    if neighborGem != None and neighborGem in possibleGems:
                        possibleGems.remove(neighborGem)

                newGem = random.choice(possibleGems)
                boardCopy[x][y] = newGem
                dropSlots[x].append(newGem)
    return dropSlots





                                        
                                        
def getDroppingGems(board):    
    #Find all the gems that have an empty space below
    boardCopy = copy.deepcopy(board)
    droppingGems = []
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT - 2, -1, -1):
            if boardCopy[x][y+1] == EMPTY_SPACE and boardCopy[x][y] != EMPTY_SPACE:
                #If teh space below a non-space is empty, drop the gem.
                droppinggems.append({'imageNum':boardCopy[x][y], 'x':x, 'y':y, 'direction':DOWN})
                boardCopy[x][y] = EMPTY_SPACE
    return droppingGems
                
                         
                         

            
                    
    


def getSwappingGems(board, firstXY, secondXY):
    #If the two gems are adjacent then their keys are set to the right direction value and swapped

    firstGem = {'imageNum': board[firstXY['x']][firstXY['y']], 'x': firstXY['x'], 'y':firstXY['y']}

    secondGem = {'imageNum': board[secondXY['x']][secondXY['y']], 'x': secondXY['x'], 'y':secondXY['y']}

    highlightedGem = None
    if firstGem['x'] == secondGem['x'] + 1 and firstGem['y'] == secondGem['y']:
        firstGem['direction'] = LEFT
        secondGem['direction'] = RIGHT
    elif firstGem['x'] == secondGem['x'] - 1 and firstGem['y'] == secondGem['y']:
        firstGem['direction'] = RIGHT
        secondGem['direction'] = LEFT
    elif firstGem['x'] == secondGem['x'] and firstGem['y'] == secondGem['y'] + 1:
        firstGem['direction'] = UP
        secondGem['direction'] = DOWN
    elif firstGem['x'] == secondGem['x'] and firstGem['y'] == secondGem['y'] - 1:
        firstGem['direction'] = DOWN
        secondGem['direction'] = UP
    else:#These  gems are not adjacent and can't be swapped
        return None, None

    return firstGem, secondGem

                 
                             
                                   
                                   
    
                                   
                                   

                                                      
        
    


    











if __name__ == '__main__':
    main()

