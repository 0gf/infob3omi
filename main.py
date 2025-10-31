import numpy as np
from pathlib import Path
import time
import argparse
from config import load
from lib.graph import build_graph
from lib.simulation import Simulation
from utils import log
from scipy import stats

def run(config):
    try:
        graph = build_graph(config['GRAPH_EDGES'])
        sim = Simulation(config, graph)
        
        ticks = config['SIMULATION']['duration_seconds']
        for _ in range(ticks):
            sim.update(dt=1.0)

        results = sim.calc_utilization(ticks)
        
        return {
            'bicycle': results['bicycle']['ρ'],
            'pedestrian': results['pedestrian']['ρ'],
            'bus': results['bus']['ρ']
        }
    except Exception as e:
        print(f"error in simulation: {e}")
        return None


def print_results(results, n):
    if not results['bicycle']:
        print("no results collected")
        return
    
    print("\nutilization (ρ) results:")
    if n == 1:
        print(f"{'type':<12} {'ρ':<10}")
        for t in ['bicycle', 'pedestrian', 'bus']:
            value = results[t][0]
            print(f"{t:<12} {value:.4f}")
    else:
        print(f"{'type':<12} {'mean (sd)':<17} {'confidence interval':<20}")
        for t in ['bicycle', 'pedestrian', 'bus']:
            values = np.array(results[t])
            mean = np.mean(values)
            sd = np.std(values, ddof=1)
            n = len(values)
            
            # 95% confidence interval
            ci = stats.t.interval(0.95, df=n-1, loc=mean, scale=sd/np.sqrt(n))
            ci_low, ci_high = ci

            print(f"{t:<12} {mean:.4f} ({sd:.4f})   [{ci_low:.4f}, {ci_high:.4f}]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=1, help="number of runs (default: 1)")
    parser.add_argument("--config", type=str, default="base.ini", help="config file (default: base.ini)")
    args = parser.parse_args()

    start = time.time()
    
    # load config
    cfg_path = Path(__file__).parent / 'config' / args.config
    log(f"loading {args.config}")
    config = load(cfg_path)
    
    # run simulations
    n = args.runs
    log(f"running {n} simulation{'s' if n > 1 else ''}...\n")
    
    results = {
        'bicycle': [],
        'pedestrian': [],
        'bus': []
    }
    
    for i in range(n):
        log(f"run {i + 1}/{n}")
        result = run(config)
        if result:
            results['bicycle'].append(result['bicycle'])
            results['pedestrian'].append(result['pedestrian'])
            results['bus'].append(result['bus'])
    
    # print results
    elapsed = time.time() - start
    log(f"completed in {elapsed:.2f}s")
    print_results(results, n)
