import snap
from sets import Set
import matplotlib.pyplot as plt
import random
import collections
import numpy as np
import itertools

SUFFIX = "bk-comp"
COLORS = itertools.cycle(["r", "b", "g", "c", "m", "y", "k", "w"])
GRAPH_LIST = [("MAL-recommendation", "mal-rec-graph"), ("brightkite", "Brightkite_edges.txt")]
#("Actors-graph","imdb_actor_edges.tsv"), ("Facebook","facebook_combined.txt")]
DATA_SOURCE = "uniq-mal-dump.txt"


def calculate_degree_dist(filename):
    graph = snap.LoadEdgeList(snap.PUNGraph, filename)
    degmap = {}
    for node in graph.Nodes():
        deg = node.GetOutDeg()
        if not deg in degmap:
            degmap[deg] = 0
        degmap[deg] += 1
    print "average degree of graph is " + str(calculate_mean_degree_sep(degmap))
    for i in degmap:
        degmap[i] = degmap[i] /float(graph.GetNodes())
    return degmap


def get_x_y_deg(degmap):
    x = []
    y = []

    for item in degmap:
        x.append(item)
        y.append(degmap[item])
    
    return x,y

def get_id_to_name(src, dst):
    with open(dst, 'w') as output:
        with open(src) as f:
            for line in f.readlines():
                split_line = line.split("|")
                output.write(split_line[0] + "," + split_line[1] + "\n")
    
def create_edge_list(filename):
    graph = snap.TUNGraph.New()
    with open(filename) as f:
        lines = f.readlines()
        for line in lines:
            anime_id = int(line.split("|")[0])
            graph.AddNode(anime_id)

        # Add edges
        for line in lines:
            split_line = line.split("|")
            anime_id = int(split_line[0])
            recs = split_line[5].split(",")
            for i in recs:
                if not i or not i.isdigit():
                    break
                if graph.IsNode(int(i)):
                    graph.AddEdge(anime_id, int(i))
    snap.SaveEdgeList(graph, "mal-rec-graph")
                
def find_nonexistent_anime():
    anime_id_set = Set()
    rec_id_set = Set()
    with open(DATA_SOURCE) as f:
        for line in f.readlines():
            split_line = line.split("|")
            anime_id = int(split_line[0])
            anime_id_set.add(anime_id)
            recs = split_line[5].split(",")
            for i in recs:
                if not i or not i.isdigit():
                    break
                if int(i) < 35000:
                    rec_id_set.add(int(i))

    for i in rec_id_set:
        if i not in anime_id_set:
            print i

def get_dist_distribution(filename, sample_count):
    distance_dst = collections.defaultdict(int)
    graph = snap.LoadEdgeList(snap.PUNGraph, filename)
    node_list = []
    for node in graph.Nodes():
        node_list.append(node.GetId())
    for i in range(0, sample_count):
        sample_pair = random.sample(node_list, 2)
        dist = snap.GetShortPath(graph, sample_pair[0], sample_pair[1], False)
        if dist > 0:
            distance_dst[dist] += 1
    print "spid is " + str(calculate_spid(distance_dst)) + " for " + str(sample_count) + " samples"
    for item in distance_dst:
        distance_dst[item] /= float(sample_count)
    return distance_dst

def get_degree_separation(filename, sample_count):
    degree_dst = collections.defaultdict(int)
    nv = snap.TIntV()
    graph = snap.LoadEdgeList(snap.PUNGraph, filename)
    node_list = []
    for node in graph.Nodes():
        node_list.append(node.GetId())
    if sample_count < len(node_list):
        samples = random.sample(node_list, sample_count)
    else:
        samples = node_list
    for sample in samples:
        hop = 1
        nodes_at_hop = snap.GetNodesAtHop(graph, sample, hop, nv, False)
        while nodes_at_hop > 0:
            degree_dst[hop]+= nodes_at_hop
            hop+=1
            nodes_at_hop = snap.GetNodesAtHop(graph, sample, hop, nv, False)
    print "average degree of separation is " + str(calculate_mean_degree_sep(degree_dst))
    for item in degree_dst:
        degree_dst[item] /= float(len(node_list) * sample_count)
    return degree_dst

def calculate_mean_degree_sep(distance_dist):
    degree_list = []
    for item in distance_dist:
        for i in range(0, distance_dist[item]):
            degree_list.append(item)
    return np.mean(degree_list)

def pdf_to_cdf(distribution):
    keys = sorted(distribution.keys())
    curr_sum = 0
    for key in keys:
        distribution[key] += curr_sum
        curr_sum = distribution[key]

def calculate_spid(distance_dist):
    degree_list = []
    for item in distance_dist:
        for i in range(0, distance_dist[item]):
            degree_list.append(item)
    return np.std(degree_list) ** 2 / np.mean(degree_list)

def get_two_hop_dist(filename):
    nv = snap.TIntV()
    graph = snap.LoadEdgeList(snap.PUNGraph, filename)
    two_hop = collections.defaultdict(int)
    ratio_list = []
    for node in graph.Nodes():
        nodes_at_two_hop = snap.GetNodesAtHop(graph, node.GetId(), 2, nv, False)
        nodes_at_one_hop = snap.GetNodesAtHop(graph, node.GetId(), 1, nv, False)
        if nodes_at_two_hop > 0 :
            two_hop[nodes_at_two_hop] += 1
            ratio_list.append(float(nodes_at_two_hop)/nodes_at_one_hop)

    print "mean ratio of two hop to one hop was " + str(np.mean(ratio_list))

    for i in two_hop:
        two_hop[i] = two_hop[i] /float(graph.GetNodes())
    return two_hop

def get_clustering_coeff(filename):
    graph = snap.LoadEdgeList(snap.PUNGraph, filename)
    degree_list = []
    coeff_list = []
    avg_coeff = collections.defaultdict(int)
    for node in graph.Nodes():
        avg_coeff[node.GetOutDeg()] = (avg_coeff[node.GetOutDeg()] + snap.GetNodeClustCf(graph, node.GetId())) / 2.0
        degree_list.append(node.GetOutDeg())
        coeff_list.append(snap.GetNodeClustCf(graph, node.GetId()))
    return avg_coeff
    #return degree_list, coeff_list

def plot_two_hop():
    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel('sizes of two hop neighborhood')
    plt.ylabel('proportion of nodes')
    for graph in GRAPH_LIST:
        print "###" + graph[0] + "###"
        two_hop_dist = get_two_hop_dist(graph[1])
        plt.scatter(two_hop_dist.keys(), two_hop_dist.values(), color = next(COLORS), label = graph[0])
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.05),
          ncol=3)
    plt.savefig('two-hop' + SUFFIX + '.png', bbox_inches='tight')
    plt.clf()
    #plt.show()

def plot_dist_distribution():
    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel('distance of shortest path between two nodes')
    plt.ylabel('proportion of samples')
    for graph in GRAPH_LIST:
        print "###" + graph[0] + "###"
        dist = get_dist_distribution(graph[1], 5000)
        plt.plot(dist.keys(), dist.values(), color = next(COLORS), label = graph[0])
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.05),
          ncol=3)
    plt.savefig('dist' + SUFFIX + '.png', bbox_inches='tight')
    plt.clf()
    #plt.show()  

def plot_degree_dist():
    plt.xscale('log')
    plt.yscale('log')

    plt.xlabel('degree k')
    plt.ylabel('proportion of nodes with degree k')
    for graph in GRAPH_LIST:
        print "###" + graph[0] + "###"
        deg = calculate_degree_dist(graph[1])
        x,y = get_x_y_deg(deg)
        plt.scatter(x, y, color = next(COLORS), label = graph[0])
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.05),
          ncol=3)
    plt.savefig('degree-distribution' + SUFFIX +'.png', bbox_inches='tight')
    plt.clf()

def plot_degree_separation():
    plt.xscale('log')
    plt.yscale('log')

    plt.xlabel('degree of separation k')
    plt.ylabel('proportion of nodes pairs with separation k')
    for graph in GRAPH_LIST:
        print "###" + graph[0] + "###"
        sep = get_degree_separation(graph[1], 5000)
        plt.plot(sep.keys(), sep.values(), color = next(COLORS), label = graph[0])
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.05),
          ncol=3)
    plt.savefig('separation-distribution' + SUFFIX + '.png', bbox_inches='tight')
    plt.clf()

def plot_clustering_coeff():
    plt.xscale('log')
    plt.yscale('log')

    plt.xlabel('node degree')
    plt.ylabel('clustering coefficient')
    for graph in GRAPH_LIST:
        print "###" + graph[0] + "###"
        avg_coeff = get_clustering_coeff(graph[1])
        plt.scatter(avg_coeff.keys(), avg_coeff.values(), color = next(COLORS), label = graph[0])
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.05),
          ncol=3)
    plt.savefig('clustering-coeff' + SUFFIX + '.png', bbox_inches='tight')
    plt.clf()



if __name__ == "__main__":
    plot_clustering_coeff()
    COLORS = itertools.cycle(["r", "b", "g", "c", "m", "y", "k", "w"])
    plot_two_hop()
    COLORS = itertools.cycle(["r", "b", "g", "c", "m", "y", "k", "w"])
    plot_dist_distribution()
    COLORS = itertools.cycle(["r", "b", "g", "c", "m", "y", "k", "w"])
    plot_degree_dist()
    COLORS = itertools.cycle(["r", "b", "g", "c", "m", "y", "k", "w"])
    plot_degree_separation()
