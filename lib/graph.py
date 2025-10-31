from collections import defaultdict

def build_graph(edges_config):
    graph = {'nodes': set(), 'adj_list': defaultdict(list)}
    for edge_data in edges_config:
        from_node, to_node, road_type, distance = edge_data
        graph['nodes'].add(from_node)
        graph['nodes'].add(to_node)
        graph['adj_list'][from_node].append({'to': to_node, 'type': road_type, 'distance': distance})
        
    return graph