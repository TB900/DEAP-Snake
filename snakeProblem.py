# This code defines the agent (as in the playable version) in a way that can be called and executed from an evolutionary algorithm. The code is partial and will not execute. You need to add to the code to create an evolutionary algorithm that evolves and executes a snake agent.
import copy
import random
import curses
import random
import operator
import numpy 
import csv
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
MUTPB = 0.8 # Mutation rate for eaMuPlusLambda (current implementation MUPB = 1.0)
CXPB = 0.1 # Crossover rate
NGEN = 300 # Number of generations
MU = 800 # Population size
LAMBDA = MU*2 # Used in the unused eaMuPlusLambda

# Returns the next coordinate the snake will be on depending on it's direction
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

# Returns true if the input isn't a wall, else false
def checkWall(coord):
	return (coord[0] == 0 or coord[0] == (YSIZE-1) or coord[1] == 0 or coord[1] == (XSIZE-1))

# This class can be used to create a basic player object (snake agent)
class SnakePlayer(list):
	global S_RIGHT, S_LEFT, S_UP, S_DOWN
	global XSIZE, YSIZE

	def __init__(self):
		self.direction = S_RIGHT
		self.body = [ [4,10], [4,9], [4,8], [4,7], [4,6], [4,5], [4,4], [4,3], [4,2], [4,1], [4,0] ]
		self.score = 0
		self.ahead = []
		self.food = []

	def _reset(self):
		self.direction = S_RIGHT
		self.body[:] = [ [4,10], [4,9], [4,8], [4,7], [4,6], [4,5], [4,4], [4,3], [4,2], [4,1], [4,0] ]
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
	
	# Snake carries on in same direction
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
	
	
		
	# These functions are the local obstacle sensing ahead and ahead of ahead of the snake
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
		
		
	
	# Returns the coordinate to the right of the snake's head given it's direction 
	def get_right(self, right_coord):
		if (self.direction == S_RIGHT):
			right_coord[0]+=1
		elif (self.direction == S_LEFT):
			right_coord[0]-=1
		elif (self.direction == S_UP):
			right_coord[1]+=1
		else:
			right_coord[0]-=1
		return right_coord
	
	# Returns the coordinate to the left of the snake's head given it's direction
	def get_left(self, left_coord):
		if (self.direction == S_RIGHT):
			left_coord[0]-=1
		elif (self.direction == S_LEFT):
			left_coord[0]+=1
		elif (self.direction == S_UP):
			left_coord[1]-=1
		else:
			left_coord[0]+=1
		return left_coord
		
		
		
	# These functions are the local obstacle sensing to the right and left ahead of the snake
	# There are also functions for further right and left local sensing functions
	def sense_obstacle_right(self):
		right_coord = self.get_right(self.get_head())
		return (right_coord in self.body) or checkWall(right_coord)
		
	def if_obstacle_right(self, out1, out2):
		return partial(if_then_else, self.sense_obstacle_right, out1, out2)

	def sense_obstacle_left(self):
		left_coord = self.get_left(self.get_head())
		return (left_coord in self.body) or checkWall(left_coord)
		
	def if_obstacle_left(self, out1, out2):
		return partial(if_then_else, self.sense_obstacle_left, out1, out2)
	
	def sense_next_obstacle_right(self):
		right_coord = self.get_right(self.get_head())
		right_coord = self.get_right(right_coord)
		return (right_coord in self.body) or checkWall(right_coord)
	
	def if_next_obstacle_right(self, out1, out2):
		return partial(if_then_else, self.sense_next_obstacle_right, out1, out2)
	
	def sense_next_obstacle_left(self):
		left_coord = self.get_left(self.get_head())
		left_coord = self.get_left(left_coord)
		return (left_coord in self.body) or checkWall(left_coord)
	
	def if_next_obstacle_left(self, out1, out2):
		return partial(if_then_else, self.sense_next_obstacle_left, out1, out2)
		
	def sense_next_obstacle_right_ahead(self):
		right_coord = self.get_right(self.getNextLocation())
		return (right_coord in self.body) or checkWall(right_coord)
	
	def if_next_obstacle_right_ahead(self, out1, out2):
		return partial(if_then_else, self.sense_next_obstacle_right_ahead, out1, out2)
	
	def sense_next_obstacle_left_ahead(self):
		left_coord = self.get_left(self.getNextLocation())
		return (left_coord in self.body) or checkWall(left_coord)
	
	def if_next_obstacle_left_ahead(self, out1, out2):
		return partial(if_then_else, self.sense_next_obstacle_left_ahead, out1, out2)
	
	
	
	# These functions are for detecting whether the snake is surrounded if it moves right, left or ahead
	def sense_surrounded_right(self):
		return self.sense_obstacle_left() and self.sense_obstacle_ahead()
		
	def if_surrounded_right(self, out1, out2):
		return partial(if_then_else, self.sense_surrounded_right, out1, out2)
	
	def sense_surrounded_left(self):
		return self.sense_obstacle_right() and self.sense_obstacle_ahead()
		
	def if_surrounded_left(self, out1, out2):
		return partial(if_then_else, self.sense_surrounded_left, out1, out2)
		
	def sense_surrounded_ahead(self):
		return self.sense_obstacle_right() and self.sense_obstacle_left()
	
	def if_surrounded_ahead(self, out1, out2):
		return partial(if_then_else, self.sense_surrounded_ahead, out1, out2)


	
	# These functions are for sensing the snake's current direction
	def sense_move_right(self):
		return self.direction == S_RIGHT

	def if_move_right(self, out1, out2):
		return partial(if_then_else, self.sense_move_right, out1, out2)
		
	def sense_move_left(self):
		return self.direction == S_LEFT
	
	def if_move_left(self, out1, out2):
		return partial(if_then_else, self.sense_move_left, out1, out2)
	
	def sense_move_up(self):
		return self.direction == S_UP
	
	def if_move_up(self, out1, out2):
		return partial(if_then_else, self.sense_move_up, out1, out2)
	
	def sense_move_down(self):
		return self.direction == S_DOWN
	
	def if_move_down(self, out1, out2):
		return partial(if_then_else, self.sense_move_down, out1, out2)
	
	
	
	# These functions are the local food sensing to the ahead, ahead of ahead, right and left ahead of the snake
	# There are extra functions for local food sensing further right and left of the snake
	def if_food_ahead(self, out1, out2):
		return partial(if_then_else, self.sense_food_ahead, out1, out2)
	
	def sense_next_food_ahead(self):
		next_coord = self.getNextLocation()
		return next_coord in self.food
	
	def if_next_food_ahead(self, out1, out2):
		return partial(if_then_else, self.sense_next_food_ahead, out1, out2)
	
	def sense_food_right(self):
		right_coord = self.get_right(self.get_head())
		return right_coord in self.food
		
	def if_food_right(self, out1, out2):
		return partial(if_then_else, self.sense_food_right, out1, out2)

	def sense_food_left(self):
		left_coord = self.get_left(self.get_head())
		return left_coord in self.food
		
	def if_food_left(self, out1, out2):
		return partial(if_then_else, self.sense_food_left, out1, out2)
		
	def sense_next_food_right(self):
		right_coord = self.get_right(self.get_head())
		right_coord = self.get_right(right_coord)
		return right_coord in self.food
	
	def if_next_food_right(self, out1, out2):
		return partial(if_then_else, self.sense_next_food_right, out1, out2)
	
	def sense_next_food_left(self):
		left_coord = self.get_left(self.get_head())
		left_coord = self.get_left(left_coord)
		return left_coord in self.food
	
	def if_next_food_left(self, out1, out2):
		return partial(if_then_else, self.sense_next_food_left, out1, out2)
	
	def sense_next_food_right_ahead(self):
		right_coord = self.get_right(self.getNextLocation())
		return right_coord in self.food
	
	def if_next_food_right_ahead(self, out1, out2):
		return partial(if_then_else, self.sense_next_obstacle_right_ahead, out1, out2)
	
	def sense_next_food_left_ahead(self):
		left_coord = self.get_left(self.getNextLocation())
		return left_coord in self.food
	
	def if_next_food_left_ahead(self, out1, out2):
		return partial(if_then_else, self.sense_next_obstacle_left_ahead, out1, out2)
	
	
	
	# These functions are for sensing the general location of the food depending on the snake's current position
	def checkFoodDirection(self):
		head = self.get_head()
		food = self.food[0]
		dir_y = head[0] - food[0]
		dir_x = head[1] - food[1]
		return [dir_y, dir_x]
	
	def sense_food_is_right(self):
		coord = self.checkFoodDirection()
		return coord[1] < 0
	
	def if_food_is_right(self, out1, out2):
		return partial(if_then_else, self.sense_food_is_right, out1, out2)
	
	def sense_food_is_left(self):
		coord = self.checkFoodDirection()
		return coord[1] > 0
	
	def if_food_is_left(self, out1, out2):
		return partial(if_then_else, self.sense_food_is_left, out1, out2)
	
	def sense_food_is_up(self):
		coord = self.checkFoodDirection()
		return coord[0] > 0
	
	def if_food_is_up(self, out1, out2):
		return partial(if_then_else, self.sense_food_is_up, out1, out2)
		
	def sense_food_is_down(self):
		coord = self.checkFoodDirection()
		return coord[0] < 0
	
	def if_food_is_down(self, out1, out2):
		return partial(if_then_else, self.sense_food_is_down, out1, out2)
		
		
		
	# These functions sense whether food is on the same axis as the snake and whether they're left or right
	def sense_food_on_x_axis_up(self):
		coord = self.checkFoodDirection()
		return coord[1] == 0 and coord[0] > 0
		
	def if_food_on_x_axis_up(self, out1, out2):
		return partial(if_then_else, self.sense_food_on_x_axis_up, out1, out2)
	
	def sense_food_on_x_axis_down(self):
		coord = self.checkFoodDirection()
		return coord[1] == 0 and coord[0] < 0
		
	def if_food_on_x_axis_down(self, out1, out2):
		return partial(if_then_else, self.sense_food_on_x_axis_down, out1, out2)
	
	def sense_food_on_y_axis_right(self):
		coord = self.checkFoodDirection()
		return coord[0] == 0 and coord[1] < 0
		
	def if_food_on_y_axis_right(self, out1, out2):
		return partial(if_then_else, self.sense_food_on_y_axis_right, out1, out2)
	
	def sense_food_on_y_axis_left(self):
		coord = self.checkFoodDirection()
		return coord[0] == 0 and coord[1] > 0
		
	def if_food_on_y_axis_left(self, out1, out2):
		return partial(if_then_else, self.sense_food_on_y_axis_left, out1, out2)
	
	
# This function places a food item in the environment
def placeFood(snake):
	food = []
	while len(food) < NFOOD:
		potentialfood = [random.randint(1, (YSIZE-2)), random.randint(1, (XSIZE-2))]
		if not (potentialfood in snake.body) and not (potentialfood in food):
			food.append(potentialfood)
	snake.food = food  # let the snake know where the food is
	return( food )

# This function check whether there is free space for food to be placed
def checkFood(snake):
	for y in xrange(0, YSIZE): # For all the tiles on the board, check if they're free
		for x in xrange(0, XSIZE):
			coord = [y,x]
			if not (coord in snake.body) and not (coord in snake.food) and not (checkWall(coord)):
				return True
	return False


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
	
	steps = 0
	timer = 0
	collided = False
	while not collided and not timer == XSIZE * YSIZE:

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
			#timer = 0
		else:    
			last = snake.body.pop()
			win.addch(last[0], last[1], ' ')
			timer += 1 # timesteps since last eaten
		
		win.addch(snake.body[0][0], snake.body[0][1], 'o')

		collided = snake.snakeHasCollided()
		hitBounds = (timer == ((2*XSIZE) * YSIZE))
		
		steps += 1

	curses.endwin()

	#print collided
	#print hitBounds
	#print snake.score
	#raw_input("Press to continue...")

	return snake.score, steps

# This outline function provides partial code for running the game with an evolved agent
# There is no graphical output, and it runs rapidly, making it ideal for
# you need to modify it for running your agents through the game for evaluation
# which will depend on what type of EA you have used, etc.
# Feel free to make any necessary modifications to this section.
def runGame(individual):
	global snake
	global pset
	
	routine = gp.compile(individual, pset)

	snake._reset()
	food = placeFood(snake)
	timer = 0
	steps = 0
	while not snake.snakeHasCollided() and not timer == XSIZE * YSIZE:

		## EXECUTE THE SNAKE'S BEHAVIOUR HERE ##
		routine()
		
		snake.updatePosition()
		
		if snake.body[0] in food:
			snake.score += 1
			if not (checkFood(snake)): # Check whether there's any coords free for food
				print("YOU WIN!!! MAX SCORE: 133 ACHIEVED!!!")
				return snake.score, steps # If not return; CONGRATS ON MAX SCORE!!!
			else: # If coords free, then place food
				food = placeFood(snake)
				timer = 0
		else:    
			snake.body.pop()
			timer += 1 # timesteps since last eaten
		
		steps += 1
	
	return snake.score, steps


def main(random_seed):
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
	#pset.addPrimitive(snake.if_next_obstacle_right, 2)
	#pset.addPrimitive(snake.if_next_obstacle_left, 2)
	#pset.addPrimitive(snake.if_next_obstacle_right_ahead, 2)
	#pset.addPrimitive(snake.if_next_obstacle_left_ahead, 2)
	
	#pset.addPrimitive(snake.if_surrounded_right, 2)
	#pset.addPrimitive(snake.if_surrounded_left, 2)
	#pset.addPrimitive(snake.if_surrounded_ahead, 2)
	
	pset.addPrimitive(snake.if_move_up, 2)
	pset.addPrimitive(snake.if_move_down, 2)
	pset.addPrimitive(snake.if_move_left, 2)
	pset.addPrimitive(snake.if_move_right, 2)
	
	pset.addPrimitive(snake.if_food_ahead, 2)
	pset.addPrimitive(snake.if_next_food_ahead, 2)
	pset.addPrimitive(snake.if_food_right, 2)
	pset.addPrimitive(snake.if_food_left, 2)
	#pset.addPrimitive(snake.if_next_food_right, 2)
	#pset.addPrimitive(snake.if_next_food_left, 2)
	#pset.addPrimitive(snake.if_next_food_right_ahead, 2)
	#pset.addPrimitive(snake.if_next_food_left_ahead, 2)
	
	#pset.addPrimitive(snake.if_food_is_right, 2)
	#pset.addPrimitive(snake.if_food_is_left, 2)
	#pset.addPrimitive(snake.if_food_is_up, 2)
	#pset.addPrimitive(snake.if_food_is_down, 2)
	
	pset.addPrimitive(snake.if_food_on_x_axis_up, 2)
	pset.addPrimitive(snake.if_food_on_x_axis_down, 2)
	pset.addPrimitive(snake.if_food_on_y_axis_right, 2)
	pset.addPrimitive(snake.if_food_on_y_axis_left, 2)
	
	pset.addTerminal(snake.changeDirectionUp)
	pset.addTerminal(snake.changeDirectionDown)
	pset.addTerminal(snake.changeDirectionLeft)
	pset.addTerminal(snake.changeDirectionRight)
	pset.addTerminal(snake.moveForward)
	
	# Give the snake's score objective a higher priority to the survivability objective
	creator.create("FitnessMax", base.Fitness, weights=(2.0, 1.0))
	creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax, pset=pset)
	
	toolbox = base.Toolbox()
	
	# Attribute generator
	toolbox.register("expr_init", gp.genGrow, pset=pset, min_=1, max_=7)
	
	# Structure initializers
	toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.expr_init)
	toolbox.register("population", tools.initRepeat, list, toolbox.individual)
	
	def evalSteps(individual):
		score, steps = runGame(individual)
		return steps,
	
	def evalScore(individual):
		score, steps = runGame(individual)
		return score,
	
	# Evaluates the individual by running the game and then returns the score for
	# first objective and steps * score for second objective
	def evalScoreAndSteps(individual):
		score, steps = runGame(individual)
		return score, steps * score
		
	def evalScoreAndStepsVisual(individual):
		score, steps = displayStrategyRun(individual)
		return score, steps * score
	
	toolbox.register("evaluate", evalScoreAndSteps) # Evaluation method
	toolbox.register("evaluate_visual", evalScoreAndStepsVisual) # Visual Evaluation method
	toolbox.register("select", tools.selNSGA2) # Selection operator (generational)
	toolbox.register("select_sample", tools.selStochasticUniversalSampling) # Selection operator (varying population)
	toolbox.register("mate", gp.cxOnePoint) # Crossover operator
	toolbox.register("mutate", gp.mutInsert, pset=pset) # Mutation operator

	# staticLimits to reduce bloat
	toolbox.decorate("mate", gp.staticLimit(key=operator.attrgetter("height"), max_value=17)) 
	toolbox.decorate("mutate", gp.staticLimit(key=operator.attrgetter("height"), max_value=17))
	
	random.seed(random_seed)
	
	pop = toolbox.population(n=MU)
	hof = tools.ParetoFront()
	
	stats_fit = tools.Statistics(key=lambda ind: ind.fitness.values)
	stats_size = tools.Statistics(key=len)
	mstats = tools.MultiStatistics(fitness=stats_fit, size=stats_size)
	mstats.register("avg", numpy.mean, axis=0)
	mstats.register("std", numpy.std, axis=0)
	mstats.register("min", numpy.min, axis=0)
	mstats.register("max", numpy.max, axis=0)
	
	# Old algorithm
	# pop, log = algorithms.eaMuPlusLambda(pop, toolbox, MU, LAMBDA, MUTPB, CXPB, NGEN, mstats, halloffame=hof)
	
	print "Using random seed " + str(random_seed) + " for this run..."
	
	logbook = tools.Logbook()
	logbook.header = "gen", "evals", "fitness", "size"
	logbook.chapters["fitness"].header = "avg", "std", "min", "max"
	logbook.chapters["size"].header = "avg", "min", "max"
	
	invalid_ind = [ind for ind in pop if not ind.fitness.valid]
	fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
	for ind, fit in zip(invalid_ind, fitnesses):
		ind.fitness.values = fit
	
	# No selection performed just initialising crowding distances
	pop = toolbox.select(pop, len(pop))
	
	if hof is not None:
		hof.update(pop)
	
	gen=0
	evals=len(invalid_ind)
	
	record = mstats.compile(pop)
	logbook.record(gen=0, evals=len(invalid_ind), **record)
	print(logbook.stream)
	
	# CSV file generator
	csv_file = open("stats" + str(random_seed) + ".csv", "w")
	with csv_file:
		writer = csv.writer(csv_file)
		writer.writerow(["---Fitness Snake Score---", "---Fitness Steps(steps*score)---", "---Size---"])
		writer.writerow(["gen", "evals", "avg", "std", "min", "max", "avg", "std", "min", "max", "avg", "min", "max"])
		writer.writerow([gen, evals, logbook.chapters["fitness"].select("avg")[gen][0], logbook.chapters["fitness"].select("std")[gen][0], logbook.chapters["fitness"].select("min")[gen][0],
		logbook.chapters["fitness"].select("max")[gen][0], logbook.chapters["fitness"].select("avg")[gen][1], logbook.chapters["fitness"].select("std")[gen][1], logbook.chapters["fitness"].select("min")[gen][1],
		logbook.chapters["fitness"].select("max")[gen][1], logbook.chapters["size"].select("avg")[gen], logbook.chapters["size"].select("min")[gen], logbook.chapters["size"].select("max")[gen]])
	
	gen+=1
	
	# While the maximum generations isn't exceeded or the maximum score isn't reached...
	while gen < NGEN+1 and logbook.chapters["fitness"].select("max")[gen-1][0] != 133:
		
		# Varies the population
		offspring = toolbox.select_sample(pop, len(pop))
		offspring = [toolbox.clone(ind) for ind in offspring]
		
		# Crossover operation
		for ind in range(1, len(offspring), 2):
			if random.random() <= CXPB:
				offspring[ind], offspring[ind-1] = toolbox.mate(offspring[ind-1], offspring[ind])
				del offspring[ind].fitness.values
				del offspring[ind-1].fitness.values
		
		# Mutation operation
		for mutant in offspring:
			toolbox.mutate(mutant)
			del mutant.fitness.values
		
		invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
		
		# Visualise final generation
		# if gen == NGEN-1:
			# fitnesses = toolbox.map(toolbox.evaluate_visual, invalid_ind)
		# else:
			# fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
		
		# Normal Non-visual Run
		fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
		
		for ind, fit in zip(invalid_ind, fitnesses):
			ind.fitness.values = fit
			
		if hof is not None:
			hof.update(offspring)
		
		current_evals = len(invalid_ind)
		
		# Select population for next generation using (n+n) method
		pop[:] = toolbox.select(pop + offspring, MU)
		record = mstats.compile(pop)
		logbook.record(gen=gen, evals=len(invalid_ind), **record)
		print(logbook.stream)
		
		# Append to CSV the logbook result
		csv_file = open("stats" + str(random_seed) + ".csv", "a")
		with csv_file:
			writer = csv.writer(csv_file)
			writer.writerow([gen, current_evals, logbook.chapters["fitness"].select("avg")[gen][0], logbook.chapters["fitness"].select("std")[gen][0], logbook.chapters["fitness"].select("min")[gen][0],
			logbook.chapters["fitness"].select("max")[gen][0], logbook.chapters["fitness"].select("avg")[gen][1], logbook.chapters["fitness"].select("std")[gen][1], logbook.chapters["fitness"].select("min")[gen][1],
			logbook.chapters["fitness"].select("max")[gen][1], logbook.chapters["size"].select("avg")[gen], logbook.chapters["size"].select("min")[gen], logbook.chapters["size"].select("max")[gen]])
		
		gen+=1
		
	
	expr = tools.selBest(pop, 1)[0]
	# toolbox.evaluate_visual(expr) # Evaluates the best individual visually.
	nodes, edges, labels = gp.graph(expr)

	# Tree drawing
	# g = pgv.AGraph(nodeSep=1.0)
	# g.add_nodes_from(nodes)
	# g.add_edges_from(edges)
	# g.layout(prog="dot")

	# for i in nodes:
		# n = g.get_node(i)
		# n.attr["label"] = labels[i]

	# g.draw("tree.pdf")
	
	return pop, hof, mstats

if __name__ == "__main__":
	main(69) # This is a guaranteed 133 scorer! 
	
	# Run the algorithm on 3 random seeds
	for x in xrange(0,3):
		rand = random.randint(0, 100)
		main(rand)