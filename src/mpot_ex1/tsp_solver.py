import argparse
import os
import sys
from pathlib import Path

import gurobipy as gp
import networkx as nx
import tsplib95

from mpot_ex1.model import create_model


def read_instance(instance_path: str | os.PathLike) -> nx.DiGraph:
    problem = tsplib95.load(instance_path)
    graph = problem.get_graph()
    graph.remove_edges_from(nx.selfloop_edges(graph))
    return graph.to_directed()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ILP-based TSP solver")
    parser.add_argument(
        "--instance", type=str, required=True, help="path to instance file"
    )
    parser.add_argument("--formulation", required=True, choices=["seq", "scf", "mcf"])

    args = parser.parse_args()

    inst = Path(args.instance).stem
    model_name = f"{inst}_{args.formulation}"

    graph = read_instance(args.instance)

    # context handlers take care of disposing resources correctly
    with gp.Model(model_name) as model:
        model._graph = graph
        model._formulation = args.formulation

        create_model(model)
        model.update()

        # sanity check to ensure that the model is an ILP
        if not model.IsMIP:
            sys.exit(
                f"Error: Your formulation for '{args.formulation}' is not a (mixed) integer linear program."
            )
        if model.IsQP or model.IsQCP:
            sys.exit(f"Error: Your formulation for '{args.formulation}' is non-linear.")

        # write model to file in readable format (useful for debugging)
        # model.write(f"{model_name}.lp")

        # by default, Gurobi considers the incumbent solution to be optimal if the gap is <= 0.0001
        # this setting ensures that Gurobi doesn't stop prematurely in these cases
        model.Params.MIPGap = 0

        model.optimize()

        # TODO read solution values / attributes from `model`
