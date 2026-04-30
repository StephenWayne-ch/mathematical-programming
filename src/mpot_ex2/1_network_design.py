import argparse
import os
from pathlib import Path

import gurobipy as gp
import networkx as nx
from gurobipy import GRB


def read_instance_file(filename: str | os.PathLike) -> nx.Graph:
    with open(Path(filename), mode="r", encoding="utf-8") as f:
        n_nodes = int(f.readline())
        n_edges = int(f.readline())

        graph = nx.Graph()

        # skip comment line
        f.readline()

        # read node lines
        for _ in range(n_nodes):
            line = f.readline()
            node_id, name, supply_demand = line.split()
            graph.add_node(int(node_id), name=name, supply_demand=int(supply_demand))

        # skip comment line
        f.readline()

        # read edge lines
        for _ in range(n_edges):
            line = f.readline()
            (
                edge_id,
                node_1,
                node_2,
                transport_cost,
                build_cost_1,
                build_cost_2,
                capacity_1,
                capacity_2,
            ) = line.split()
            graph.add_edge(
                int(node_1),
                int(node_2),
                id=int(edge_id),
                transport_cost=int(transport_cost),
                build_cost_1=int(build_cost_1),
                build_cost_2=int(build_cost_2),
                capacity_1=int(capacity_1),
                capacity_2=int(capacity_2),
            )

        return graph


def build_model(model: gp.Model, graph: nx.Graph):
    # note that nodes are 1-indexed
    directed_arcs = []
    undirected_edges = []

    for i, j in graph.edges():
        undirected_edges.append((i, j))
        directed_arcs.append((i, j))
        directed_arcs.append((j, i))
    # put your model building code here
    #
    x = model.addVars(directed_arcs, lb=0, vtype=GRB.CONTINUOUS, name='x')
    y1 = model.addVars(undirected_edges, vtype=GRB.BINARY, name="y1")
    y2 = model.addVars(undirected_edges, vtype=GRB.BINARY, name="y2")

    model.setObjective(
        gp.quicksum(
            graph.edges[i, j]["transport_cost"] * (x[i, j] + x[j, i])
            for i, j in undirected_edges
        )
        + gp.quicksum(
            graph.edges[i, j]["build_cost_1"] * y1[i, j]
            + graph.edges[i, j]["build_cost_2"] * y2[i, j]
            for i, j in undirected_edges
        ),
        GRB.MINIMIZE,
    )
    # if you want to access your variables outside this function, you can use
    model._x = x
    model._y1 = y1
    model._y2 = y2
    model._directed_arcs = directed_arcs
    model._undirected_edges = undirected_edges
    # to save a reference in the model itself
    #
    model.addConstrs(
        (y1[i, j] + y2[i, j] <= 1 for i, j in undirected_edges),
        name="build_choice",
    )
    model.addConstrs(
        (
            x[i, j] + x[j, i]
            <= graph.edges[i, j]["capacity_1"] * y1[i, j]
            + graph.edges[i, j]["capacity_2"] * y2[i, j]
            for i, j in undirected_edges
        ),
        name="capacity",
    )
    for n in graph.nodes():
        outflow = gp.quicksum(x[n, j] for j in graph.neighbors(n))
        inflow = gp.quicksum(x[j, n] for j in graph.neighbors(n))

        model.addConstr(
            outflow - inflow == graph.nodes[n]["supply_demand"],
            name=f"flow_balance_{n}",
        )
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--filename", default="instances/1-network-design-instance.dat")
    args = parser.parse_args()

    graph = read_instance_file(args.filename)

    model = gp.Model("1-network-design")
    build_model(model, graph)

    model.update()
    model.optimize()

    if model.status == GRB.OPTIMAL:
        print(f"Optimal objective value: {model.objVal}")
        print("\nChosen build options:")
        for i, j in model._undirected_edges:
            if model._y1[i, j].X > 0.5:
                print(
                    f"Edge ({i}, {j}) uses option 1, "
                    f"capacity={graph.edges[i, j]['capacity_1']}, "
                    f"build_cost={graph.edges[i, j]['build_cost_1']}"
                )
            elif model._y2[i, j].X > 0.5:
                print(
                    f"Edge ({i}, {j}) uses option 2, "
                    f"capacity={graph.edges[i, j]['capacity_2']}, "
                    f"build_cost={graph.edges[i, j]['build_cost_2']}"
                )
            else:
                print(f"Edge ({i}, {j}) is not built")
        print("\nFlows:")
        for i, j in model._directed_arcs:
            if model._x[i, j].X > 1e-6:
                print(f"x[{i},{j}] = {model._x[i, j].X}")
    model.close()
