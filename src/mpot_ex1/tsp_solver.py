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
        model.write(f"{model_name}.lp")

        # by default, Gurobi considers the incumbent solution to be optimal if the gap is <= 0.0001
        # this setting ensures that Gurobi doesn't stop prematurely in these cases
        model.Params.MIPGap = 0

        model.optimize()

        # TODO read solution values / attributes from `model`
        if model.Status == gp.GRB.OPTIMAL or (model.Status == gp.GRB.TIME_LIMIT and model.SolCount > 0):
            print("\n" + "=" * 40)
            print(f"Solution Found! Model: {model_name}")
            print(f"Optimal Objective: {model.ObjVal:.2f}")
            print(f"Solving Runtime: {model.Runtime:.2f} s")
            print(f"Explored Nodes: {model.NodeCount}")
            print(f"Final MIP Gap: {model.MIPGap * 100:.4f}%")
            print("=" * 40)

            # --- Critical Fix: Using the dictionary we created in create_model ---
            try:
                # We use model._x[u, v] instead of getVarByName to avoid NoneType errors
                active_edges = [
                    (u, v) for u, v in graph.edges
                    if model._x[u, v].X > 0.5
                ]
                # Reconstruct the Hamiltonian tour
                # tsplib95 usually uses nodes 1...N
                start_node = list(graph.nodes)[0]
                tour = [start_node]
                current = start_node
                while len(tour) < graph.number_of_nodes():
                    for u, v in active_edges:
                        if u == current:
                            tour.append(v)
                            current = v
                            break

                print(f"Complete Tour: {' -> '.join(map(str, tour))} -> {start_node}")

            except AttributeError:
                print("Error: model._x dictionary not found. Ensure it is defined in create_model.")

        elif model.Status == gp.GRB.INFEASIBLE:
            print("Error: Model is Infeasible. Computing IIS...")
            model.computeIIS()
            model.write("model.ilp")
        elif model.Status == gp.GRB.TIME_LIMIT:
            print("Time limit reached. No feasible solution was found.")
        else:
            print(f"Optimization stopped. Gurobi Status Code: {model.Status}")
