import gurobipy as gp
import networkx as nx
from gurobipy import GRB


def create_model(model: gp.Model):
    graph: nx.DiGraph = model._graph
    formulation: str = model._formulation

    # see, e.g., https://docs.gurobi.com/projects/optimizer/en/current/reference/python.html TE

    print(f"{graph.number_of_nodes()=}, {graph.number_of_edges()=}")

    # common variables
    # see, e.g., https://docs.gurobi.com/projects/optimizer/en/current/reference/python/model.html#Model.addVars

    nodes = list(graph.nodes())
    n = len(nodes)
    x = model.addVars([(i, j) for i in nodes for j in nodes if i != j], vtype=GRB.BINARY, name="x")
    model._x = x
    # add reference to relevant variables for later use outside this function (e.g., reading solutions)
    # m._x = x

    # common constraints
    # see, e.g., https://docs.gurobi.com/projects/optimizer/en/current/reference/python/model.html#Model.addConstr
    for i in nodes:
        model.addConstr(gp.quicksum(x[i, j] for j in nodes if j != i) == 1)
        model.addConstr(gp.quicksum(x[j, i] for j in nodes if j != i) == 1)
    # TODO add common constraints here

    if formulation == "seq":
        u = model.addVars([i for i in nodes if i != 1], lb=1, ub=n - 1, vtype=GRB.CONTINUOUS, name="u")
        model._u = u
        
        for i in nodes:
            for j in nodes:
                if i != j and i != 1 and j != 1:
                    model.addConstr(u[i] + x[i, j] <= u[j] + (n - 2) * (1 - x[i, j]), name=f"mtz_{i}_{j}")        
        pass

    elif formulation == "scf":
        f = model.addVars([(i, j) for i in nodes for j in nodes if i != j], lb=0, ub=n - 1, vtype=GRB.CONTINUOUS, name="f")
        model._f = f

        model.addConstr(gp.quicksum(f[1, j] for j in nodes if j != 1) == n - 1, name="flow_source")

        for i in nodes:
            if i != 1:
                model.addConstr(gp.quicksum(f[j, i] for j in nodes if j != i) - gp.quicksum(f[i, j] for j in nodes if j != i) == 1, name=f"flow_cons_{i}")

        for i, j in x:
            model.addConstr(f[i, j] <= (n - 1) * x[i, j], name=f"cap_{i}_{j}")
        pass

    elif formulation == "mcf":

        commodities = [k for k in nodes if k != 1]
        f = model.addVars([(i, j, k) for i in nodes for j in nodes for k in commodities if i != j], lb=0, ub=1, vtype=GRB.CONTINUOUS, name="f")
        model._f = f

        for k in commodities:
            model.addConstr(
                gp.quicksum(f[1, j, k] for j in nodes if j != 1)
                - gp.quicksum(f[j, 1, k] for j in nodes if j != 1)
                == 1,
                name=f"source_{k}"
            )

        for k in commodities:
            model.addConstr(
                gp.quicksum(f[k, j, k] for j in nodes if j != k)
                - gp.quicksum(f[j, k, k] for j in nodes if j != k)
                == -1,
                name=f"sink_{k}"
            )

        for k in commodities:
            for i in nodes:
                if i != 1 and i != k:
                    model.addConstr(gp.quicksum(f[i, j, k] for j in nodes if j != i) - gp.quicksum(f[j, i, k] for j in nodes if j != i) == 0, name=f"flow_{i}_{k}")

        for i, j in x:
            for k in commodities:
                model.addConstr(f[i, j, k] <= x[i, j], name=f"cap_{i}_{j}_{k}")

        pass

    model.setObjective(
        gp.quicksum(graph[i][j]["weight"] * x[i, j] for i, j in x),
        GRB.MINIMIZE
    )
