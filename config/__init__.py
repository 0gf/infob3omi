import configparser
import ast

def parse(s):
    return [x.strip() for x in s.split(',')]

def load(filepath):
    parser = configparser.ConfigParser()
    if not parser.read(filepath):
        raise Exception

    config = {
        'SIMULATION': {
            'duration_seconds': parser.getint('SIMULATION', 'duration_seconds'),
            'light_cycle': parse(parser.get('SIMULATION', 'light_cycle')),
            'light_duration': parser.getint('SIMULATION', 'light_duration'),
            'bus_priority_delay': parser.getint('SIMULATION', 'bus_priority_delay'),
            'service_capacity': {
                'bicycle': parser.getint('SERVICE_CAPACITY', 'bicycle'),
                'pedestrian': parser.getint('SERVICE_CAPACITY', 'pedestrian'),
                'bus': parser.getint('SERVICE_CAPACITY', 'bus'),
            }
        },
        'AGENT_PROPERTIES': {},
        'GRAPH_EDGES': []
    }

    # load agent properties
    for section in parser.sections():
        if section.startswith('AGENT_'):
            agent = section.split('_')[1]
            config['AGENT_PROPERTIES'][agent] = {
                'speed': parser.getfloat(section, 'speed'),
                'spawn_rate_distribution': parser.get(section, 'spawn_rate_distribution', fallback='constant'),
                'spawn_rate_params': ast.literal_eval(parser.get(section, 'spawn_rate_params', fallback='{}')),
                'spawn_rate': parser.getfloat(section, 'spawn_rate'),
                'entry_nodes': parse(parser.get(section, 'entry_nodes')),
                'exit_nodes': parse(parser.get(section, 'exit_nodes')),
            }

    # load graph edges
    edges = parser.get('GRAPH_EDGES', 'edges')
    for line in edges.strip().splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            from_node, to_node, road_type, distance = [x.strip() for x in line.split(',')]
            config['GRAPH_EDGES'].append((from_node, to_node, [road_type], float(distance)))

    return config
