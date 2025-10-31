import random
from collections import defaultdict, deque
from .agent import Agent

class Simulation:
    def __init__(self, config, graph):
        self.config = config
        self.graph = graph
        self.rng = random.Random()
        self.reset()

    def reset(self):
        self.agents = {}
        self.i = 0
        
        # tracking stats
        self.arrivals = defaultdict(int)
        self.departures = defaultdict(int)
        self.spawned = defaultdict(int)
        self.spawn_acc = defaultdict(float)
        
        # intersection queues by agent type
        self.queues = {
            'bicycle': deque(),
            'bus': deque(),
            'pedestrian': deque()
        }
        
        # traffic light state
        sim = self.config['SIMULATION']
        self.lights = sim['light_cycle']
        self.light_t = sim['light_duration']
        self.light_i = 0
        self.t = 0
        
        # bus priority system
        self.bus_prio = False
        self.bus_prio_sleep = 0

    def current_light(self):
        return self.lights[self.light_i]

    def bus_priority(self):
        # trigger priority if bus arrives
        if not self.queues['bus'] or self.bus_prio:
            return False
        
        for bus in self.queues['bus']:
            if bus.sleep > 0:
                self.bus_prio = True
                self.bus_prio_sleep = self.config['SIMULATION']['bus_priority_delay']
                return True
        return False

    def get_spawn_rate(self, type, props):
        # sample from configured distribution
        dist = props.get('spawn_rate_distribution', 'constant')
        
        if dist == 'constant':
            return props['spawn_rate']
        
        if dist == 'bimodal':
            p = props['spawn_rate_params']
            if self.rng.random() < 0.5:
                return max(0.0, self.rng.gauss(p['mode1_mean'], p['mode1_std']))
            else:
                return max(0.0, self.rng.gauss(p['mode2_mean'], p['mode2_std']))
        
        return props['spawn_rate']

    def spawn_agents(self):
        # create new agents based on spawn rates
        for type, props in self.config['AGENT_PROPERTIES'].items():
            rate = self.get_spawn_rate(type, props)
            self.spawn_acc[type] += rate
            
            # spawn whole agents when accumulator >= 1
            if self.spawn_acc[type] >= 1.0:
                count = int(self.spawn_acc[type])
                self.spawn_acc[type] -= count
                
                for _ in range(count):
                    start = self.rng.choice(props['entry_nodes'])
                    finish = [n for n in props['exit_nodes'] if n != start]
                    
                    if not finish:
                        continue
                    
                    end = self.rng.choice(finish)
                    agent = Agent(self.i, type, start, end, self.graph, props, self.rng)
                    
                    if agent.active:
                        self.agents[agent.id] = agent
                        self.arrivals[type] += 1
                        self.spawned[type] += 1
                        self.i += 1

    def update(self, dt=1.0):
        # check if buses need priority
        self.bus_priority()
        
        # handle bus priority countdown
        if self.bus_prio and self.bus_prio_sleep > 0:
            self.bus_prio_sleep -= dt
            if self.bus_prio_sleep <= 0:
                self.light_i = self.lights.index('bus')
                self.t = 0
                self.bus_prio = False
        else:
            # normal light cycling
            self.t += dt
            if self.t >= self.light_t:
                self.t = 0
                self.light_i = (self.light_i + 1) % len(self.lights)
                if self.current_light() != 'bus':
                    self.bus_prio = False
        
        light = self.current_light()
        self.spawn_agents()
        
        # update all agents and  clean up finished ones
        finished_agents = []
        for id, agent in self.agents.items():
            agent.update(light, self.queues, dt)
            if not agent.active:
                finished_agents.append(id)
                self.departures[agent.type] += 1
        
        # remove finished agents 
        for id in finished_agents:
            del self.agents[id]

    def calc_utilization(self, ticks):
        # calculate  for each agent type
        results = {}
        sim = self.config['SIMULATION']
        
        for type in self.lights:
            lambda_rate = self.arrivals[type] / ticks
            green_fraction = 1 / len(self.lights)
            mu = (sim['service_capacity'][type] / sim['light_duration']) * green_fraction
            rho = lambda_rate / mu if mu > 0 else float('inf')
            
            results[type] = {
                'λ': lambda_rate,
                'μ': mu,
                'ρ': rho
            }
        
        return results