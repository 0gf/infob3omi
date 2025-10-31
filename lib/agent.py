class Agent:
    def __init__(self, id, type, start, end, graph, props, rng):
        self.id = id
        self.type = type
        self.graph = graph
        self.start = start
        self.end = end
        self.props = props
        self.rng = rng
        
        # current node pos and route
        self.node = start
        self.path = []
        self.edges = []
        self.edge_i = 0
        self.edge_progress = 0.0
        
        # state tracking
        self.active = True
        self.queued = False
        self.sleep = 0
        self.speed = props.get('speed', 1.0)
        
        self.find_route()

    # random steps
    def find_route(self):
        # try to find a valid route to destination by exploring random nodes
        for _ in range(50): # limit the amount of steps otherwise itll take really long
            path = [self.start]
            curr = self.start
            
            for _ in range(50):
                # get edges this agent type can use
                edges = [e for e in self.graph['adj_list'].get(curr, [])
                        if self.type in e['type'] or 'mixed' in e['type']]
                
                if not edges:
                    break
                
                edge = self.rng.choice(edges)
                next = edge['to']
                
                # dont go back to previous node
                if len(path) > 1 and next == path[-2]:
                    continue
                
                path.append(next)
                curr = next
                
                # found a route
                if curr == self.end:
                    self.path = path
                    self.build_edges()
                    return
        
        self.active = False

    def build_edges(self):
        # convert node path to edge list with distances
        # so that the agent knows how far it takes to go to this node
        self.edges = []
        for i in range(len(self.path) - 1):
            a, b = self.path[i], self.path[i + 1]
            for edge in self.graph['adj_list'].get(a, []):
                if edge['to'] == b and (self.type in edge['type'] or 'mixed' in edge['type']):
                    self.edges.append((a, b, edge['distance']))
                    break

    def update(self, green_light, queues, dt=1.0):
        if not self.active or not self.edges:
            return
        
        # at start of edge check if we can go through intersection, i.e., if the light is green
        if self.edge_progress == 0.0 and self.edge_i < len(self.edges):
            if self.type != green_light:
                # wrong light, wait in queue
                if not self.queued:
                    queues[self.type].append(self)
                    self.queued = True
                else:
                    self.sleep += dt
                return
            elif self.queued:
                # light changed, leave queue
                if self in queues[self.type]:
                    queues[self.type].remove(self)
                self.queued = False
                self.sleep = 0
        
        # move forward on current edge
        if self.edge_i < len(self.edges):
            _, next, dist = self.edges[self.edge_i]
            self.edge_progress += self.speed * dt
            
            # finished this edge
            if self.edge_progress >= dist:
                self.edge_i += 1
                self.edge_progress = 0.0
                self.node = next
                
                # reached destination
                if self.node == self.end:
                    self.active = False