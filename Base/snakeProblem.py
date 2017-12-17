# This code defines the agent (as in the playable version) in a way that can be called and executed from an evolutionary algorithm. The code is partial and will not execute. You need to add to the code to create an evolutionary algorithm that evolves and executes a snake agent.
import copy
import random
import curses
import random
import operator
import numpy 
from functools import partial
#import pygraphviz as pgv

from deap import algorithms
from deap import base
from deap import creator
from deap import tools
from deap import gp

S_RIGHT, S_LEFT, S_UP, S_DOWN = 0,1,2,3
XSIZE,YSIZE = 14,14
BOARD_SIZE = (YSIZE - 2) * (XSIZE - 2)
NFOOD = 1 # NOTE: YOU MAY NEED TO ADD A CHECK THAT THERE ARE ENOUGH SPACES LEFT FOR THE FOOD (IF THE TAIL IS VERY LONG)

def dir_map(dir, y, x):
	if (dir == S_RIGHT):
		return [y, x+1]
	elif (dir == S_LEFT):
		return [y, x-1]
	elif (dir == S_UP):
		return [y-1, x]
	else:
		return [y+1, x]
		
def progn(*args):
    for arg in args:
        arg()

def prog2(out1, out2): 
    return partial(progn,out1,out2)

def prog3(out1, out2, out3):     
    return partial(progn,out1,out2,out3)

def if_then_else(condition, out1, out2):
    out1() if condition() else out2()
	
def checkWall(coord):
	return (coord[0] == 0 or coord[0] == (YSIZE-1) or coord[1] == 0 or coord[1] == (XSIZE-1))

# This class can be used to create a basic player object (snake agent)
class SnakePlayer(list):
	global S_RIGHT, S_LEFT, S_UP, S_DOWN
	global XSIZE, YSIZE

	def __init__(self):
		self.direction = S_RIGHT
		self.body = [ [4,10], [4,9], [4,8], [4,7], [4,6], [4,5], [4,4], [4,3], [4,2], [4,1],[4,0] ]
		self.score = 0
		self.ahead = []
		self.food = []

	def _reset(self):
		self.direction = S_RIGHT
		self.body[:] = [ [4,10], [4,9], [4,8], [4,7], [4,6], [4,5], [4,4], [4,3], [4,2], [4,1],[4,0] ]
		self.score = 0
		self.ahead = []
		self.food = []

	def getAheadLocation(self):
		self.ahead = [ self.body[0][0] + (self.direction == S_DOWN and 1) + (self.direction == S_UP and -1), self.body[0][1] + (self.direction == S_LEFT and -1) + (self.direction == S_RIGHT and 1)]
		
	def getNextLocation(self):
		self.getAheadLocation()
		return dir_map(self.direction, self.ahead[0], self.ahead[1])

	def updatePosition(self):
		self.getAheadLocation()
		self.body.insert(0, self.ahead )

	## You are free to define more sensing options to the snake

	def changeDirectionUp(self):
		self.direction = S_UP

	def changeDirectionRight(self):
		self.direction = S_RIGHT

	def changeDirectionDown(self):
		self.direction = S_DOWN

	def changeDirectionLeft(self):
		self.direction = S_LEFT
	
	def moveForward(self):
		pass

	def snakeHasCollided(self):
		self.hit = False
		if self.body[0][0] == 0 or self.body[0][0] == (YSIZE-1) or self.body[0][1] == 0 or self.body[0][1] == (XSIZE-1): self.hit = True
		if self.body[0] in self.body[1:]: self.hit = True
		return( self.hit )

	def sense_wall_ahead(self):
		self.getAheadLocation()
		return( self.ahead[0] == 0 or self.ahead[0] == (YSIZE-1) or self.ahead[1] == 0 or self.ahead[1] == (XSIZE-1) )

	def sense_food_ahead(self):
		self.getAheadLocation()
		return self.ahead in self.food

	def sense_tail_ahead(self):
		self.getAheadLocation()
		return self.ahead in self.body
	
	def get_head(self):
		return [self.body[0][0], self.body[0][1]]
	
	def sense_obstacle_ahead(self):
		return self.sense_wall_ahead() or self.sense_tail_ahead()
	
	def if_obstacle_ahead(self, out1, out2):
		return partial(if_then_else, self.sense_obstacle_ahead, out1, out2)
	
	def sense_next_obstacle_ahead(self):
		next_coord = self.getNextLocation()
		return (next_coord in self.body) or checkWall(next_coord)
	
	def if_next_obstacle_ahead(self, out1, out2):
		return partial(if_then_else, self.sense_next_obstacle_ahead, out1, out2)
	
	def get_right(self):
		right_coord = self.get_head()
		if (self.direction == S_RIGHT):
			right_coord[0]+=1
		elif (self.direction == S_LEFT):
			right_coord[0]-=1
		elif (self.direction == S_UP):
			right_coord[1]+=1
		else:
			right_coord[0]-=1
		return right_coord
	
	def get_left(self):
		left_coord = self.get_head()
		if (self.direction == S_RIGHT):
			left_coord[0]-=1
		elif (self.direction == S_LEFT):
			left_coord[0]+=1
		elif (self.direction == S_UP):
			left_coord[1]-=1
		else:
			left_coord[0]+=1
		return left_coord
			
	def sense_obstacle_right(self):
		right_coord = self.get_right()
		return (right_coord in self.body) or checkWall(right_coord)

	def sense_obstacle_left(self):
		left_coord = self.get_left()
		return (left_coord in self.body) or checkWall(left_coord)
		
	def if_obstacle_right(self, out1, out2):
		return partial(if_then_else, self.sense_obstacle_right, out1, out2)
		
	def if_obstacle_left(self, out1, out2):
		return partial(if_then_else, self.sense_obstacle_left, out1, out2)
	
# This function places a food item in the environment
def placeFood(snake):
	food = []
	while len(food) < NFOOD:
		potentialfood = [random.randint(1, (YSIZE-2)), random.randint(1, (XSIZE-2))]
		if not (potentialfood in snake.body) and not (potentialfood in food):
			food.append(potentialfood)
	snake.food = food  # let the snake know where the food is
	return( food )


snake = SnakePlayer()


# This outline function is the same as runGame (see below). However,
# it displays the game graphically and thus runs slower
# This function is designed for you to be able to view and assess
# your strategies, rather than use during the course of evolution
def displayStrategyRun(individual):
	global snake
	global pset
	
	routine = gp.compile(individual, pset)
	
	curses.initscr()
	win = curses.newwin(YSIZE, XSIZE, 0, 0)
	win.keypad(1)
	curses.noecho()
	curses.curs_set(0)
	win.border(0)
	win.nodelay(1)
	win.timeout(120)

	snake._reset()
	food = placeFood(snake)

	for f in food:
		win.addch(f[0], f[1], '@')

	timer = 0
	collided = False
	while not collided and not timer == ((2*XSIZE) * YSIZE):

		# Set up the display
		win.border(0)
		win.addstr(0, 2, 'Score : ' + str(snake.score) + ' ')
 		win.getch()

		## EXECUTE THE SNAKE'S BEHAVIOUR HERE ##
		routine()

		snake.updatePosition()

		if snake.body[0] in food:
			snake.score += 1
			for f in food: win.addch(f[0], f[1], ' ')
			food = placeFood(snake)
			for f in food: win.addch(f[0], f[1], '@')
			timer = 0
		else:    
			last = snake.body.pop()
			win.addch(last[0], last[1], ' ')
			timer += 1 # timesteps since last eaten
		win.addch(snake.body[0][0], snake.body[0][1], 'o')

		collided = snake.snakeHasCollided()
		hitBounds = (timer == ((2*XSIZE) * YSIZE))

	curses.endwin()

	print collided
	print hitBounds
	print snake.score
	#raw_input("Press to continue...")

	return snake.score,


# This outline function provides partial code for running the game with an evolved agent
# There is no graphical output, and it runs rapidly, making it ideal for
# you need to modify it for running your agents through the game for evaluation
# which will depend on what type of EA you have used, etc.
# Feel free to make any necessary modifications to this section.
def runGame():
	global snake

	totalScore = 0

	snake._reset()
	food = placeFood(snake)
	timer = 0
	while not snake.snakeHasCollided() and not timer == XSIZE * YSIZE:

		## EXECUTE THE SNAKE'S BEHAVIOUR HERE ##
		
		snake.updatePosition()

		if snake.body[0] in food:
			snake.score += 1
			food = placeFood(snake)
			timer = 0
		else:    
			snake.body.pop()
			timer += 1 # timesteps since last eaten

		totalScore += snake.score
		
	return totalScore,


def main():
	global snake
	global pset

	## THIS IS WHERE YOUR CORE EVOLUTIONARY ALGORITHM WILL GO #
	pset = gp.PrimitiveSet("MAIN", 0)
	
	pset.addPrimitive(prog2, 2)
	pset.addPrimitive(prog3, 3)
	
	pset.addPrimitive(snake.if_obstacle_ahead, 2)
	pset.addPrimitive(snake.if_next_obstacle_ahead, 2)
	pset.addPrimitive(snake.if_obstacle_right, 2)
	pset.addPrimitive(snake.if_obstacle_left, 2)
	
	#pset.addPrimitive(snake.if_obstacle_up, 2)
	#pset.addPrimitive(snake.if_obstacle_down, 2)
	#pset.addPrimitive(snake.if_obstacle_left, 2)
	#pset.addPrimitive(snake.if_obstacle_right, 2)
	
	#pset.addPrimitive(snake.if_next_obstacle_up, 2)
	#pset.addPrimitive(snake.if_next_obstacle_down, 2)
	#pset.addPrimitive(snake.if_next_obstacle_left, 2)
	#pset.addPrimitive(snake.if_next_obstacle_right, 2)
	
	#pset.addPrimitive(snake.if_move_up, 2)
	#pset.addPrimitive(snake.if_move_down, 2)
	#pset.addPrimitive(snake.if_move_left, 2)
	#pset.addPrimitive(snake.if_move_right, 2)
	
	pset.addTerminal(snake.changeDirectionUp)
	pset.addTerminal(snake.changeDirectionDown)
	pset.addTerminal(snake.changeDirectionLeft)
	pset.addTerminal(snake.changeDirectionRight)
	pset.addTerminal(snake.moveForward, name="forward")
	
	creator.create("FitnessMax", base.Fitness, weights=(1.0,))
	creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax, pset=pset)
	
	toolbox = base.Toolbox()
	
	# Attribute generator
	toolbox.register("expr_init", gp.genGrow, pset=pset, min_=1, max_=5)
	
	# Structure initializers
	toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.expr_init)
	toolbox.register("population", tools.initRepeat, list, toolbox.individual)
	
	def evalSnake(individual):
		return displayStrategyRun(individual)
	
	toolbox.register("evaluate", evalSnake)
	toolbox.register("select", tools.selTournament, tournsize=5)
	toolbox.register("mate", gp.cxOnePoint)
	toolbox.register("expr_mut", gp.genHalfAndHalf, min_=1, max_=4)
	toolbox.register("mutate", gp.mutUniform, expr=toolbox.expr_mut, pset=pset)

	toolbox.decorate("mate", gp.staticLimit(key=operator.attrgetter("height"), max_value=17))
	toolbox.decorate("mutate", gp.staticLimit(key=operator.attrgetter("height"), max_value=17))
	
	random.seed(69)
	
	pop = toolbox.population(n=5)
	hof = tools.HallOfFame(1)
	
	stats = tools.Statistics(lambda ind: ind.fitness.values)
	stats.register("avg", numpy.mean)
	stats.register("std", numpy.std)
	stats.register("min", numpy.min)
	stats.register("max", numpy.max)
	
	pop, log = algorithms.eaSimple(pop, toolbox, 0.5, 0.5, 40, stats, halloffame=hof)
	
	expr = tools.selBest(pop, 1)[0]
	nodes, edges, labels = gp.graph(expr)

	# g = pgv.AGraph(nodeSep=1.0)
	# g.add_nodes_from(nodes)
	# g.add_edges_from(edges)
	# g.layout(prog="dot")

	# for i in nodes:
		# n = g.get_node(i)
		# n.attr["label"] = labels[i]

	# g.draw("tree.pdf")
	
	return pop, hof, stats
	
if __name__ == "__main__":
    main()
