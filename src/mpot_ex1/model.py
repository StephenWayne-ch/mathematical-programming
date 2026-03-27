import gurobipy as gp
import networkx as nx
from gurobipy import GRB


def create_model(model: gp.Model):
    graph: nx.DiGraph = model._graph
    formulation: str = model._formulation

    # see, e.g., https://docs.gurobi.com/projects/optimizer/en/current/reference/python.html

    print(f"{graph.number_of_nodes()=}, {graph.number_of_edges()=}")

    # create common variables
    # see, e.g., https://docs.gurobi.com/projects/optimizer/en/current/reference/python/model.html#Model.addVars

    # TODO add your common variables here
    nodes = list(graph.nodes())
    x = model.addVars([(i, j) for i in nodes for j in nodes if i != j], vtype=GRB.BINARY, name="x")
    model._x = x
    # add reference to relevant variables for later use outside this function (e.g., reading solutions)

    # TODO create references to your common variables
    # m._x = x

    # create common constraints
    # see, e.g., https://docs.gurobi.com/projects/optimizer/en/current/reference/python/model.html#Model.addConstr
    for i in nodes:
        model.addConstr(gp.quicksum(x[i, j] for j in nodes if j != i) == 1)
        model.addConstr(gp.quicksum(x[j, i] for j in nodes if j != i) == 1)
    # TODO add common constraints here

    # create model-specific variables and constraints

    # SEQ
    if formulation == "seq":
        u = model.addVars([i for i in nodes if i != 1], lb=1, ub=n - 1, vtype=GRB.CONTINUOUS, name="u")
        model._u = u
        
        for i in nodes:
            for j in nodes:
                if i != j and i != 1 and j != 1:
                    model.addConstr(u[i] + x[i, j] <= u[j] + (n - 2) * (1 - x[i, j]), name=f"mtz_{i}_{j}")        
        pass

    # SCF
    elif formulation == "scf":
        # TODO add your SCF constraints here
        pass

    # MCF
    elif formulation == "mcf":
        # TODO add your MCF constraints here
        pass

    model.setObjective(
        gp.quicksum(graph[i][j]["weight"] * x[i, j] for i, j in x),
        GRB.MINIMIZE
    )
