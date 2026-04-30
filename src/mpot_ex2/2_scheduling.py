import argparse
import os
from pathlib import Path

import gurobipy as gp
import numpy as np
from gurobipy import GRB


def read_instance_file(filename: str | os.PathLike) -> tuple[np.ndarray, np.ndarray]:
    with open(Path(filename), mode="r", encoding="utf-8") as f:
        n_jobs = int(f.readline())
        n_machines = int(f.readline())

        # skip comment line
        f.readline()

        proc_times = []
        for _ in range(n_jobs):
            proc_times_j = [int(p) for p in f.readline().split()]
            assert len(proc_times_j) == n_machines
            proc_times.append(proc_times_j)
        processing_times = np.array(proc_times, dtype=np.int32)

        # skip comment line
        f.readline()
        machine_seq = []
        for _ in range(n_jobs):
            machine_seq_j = [int(h) for h in f.readline().split()]
            assert set(machine_seq_j) == set(range(n_machines))
            machine_seq.append(machine_seq_j)
        machine_sequences = np.array(machine_seq, dtype=np.int32)

        return processing_times, machine_sequences


def build_model(model: gp.Model, objective: str, processing_times: np.ndarray, machine_sequences: np.ndarray):
    n_jobs, n_machines = processing_times.shape

    # Big-M (tight version)
    M = int(np.sum(processing_times))

    # Variables S_{j,h} and C_j from (1) - (2)
    S = model.addVars(n_jobs, n_machines, lb=0, name="S")
    C = model.addVars(n_jobs, lb=0, name="C")

    # x_{j,k,h} variables from (3), (5)
    x = model.addVars([(j, k, h) for j in range(n_jobs) for k in range(n_jobs) if j != k for h in range(n_machines)],vtype=GRB.BINARY,name="x")

    # Precedence constraint (4)
    for j in range(n_jobs):
        for l in range(n_machines - 1):
            h_1 = machine_sequences[j, l]
            h_2 = machine_sequences[j, l + 1]
            model.addConstr(S[j,h_2] >= S[j,h_1] + processing_times[j,h_1])

    # Reversals constraint (5)
    for h in range(n_machines):
        for j in range(n_jobs):
            for k in range(j + 1, n_jobs):
                model.addConstr(x[j,k,h] + x[k,j,h] == 1)

    # Starting time constraints (6)
    for h in range(n_machines):
        for j in range(n_jobs):
            for k in range(n_jobs):
                if j != k:
                    model.addConstr(S[j,h] + processing_times[j,h] <= S[k,h] + M * (1 - x[j,k,h]))

    # Completion time constraints (7)
    for j in range(n_jobs):
        last_machine = machine_sequences[j, -1]
        model.addConstr(C[j] == S[j,last_machine] + processing_times[j,last_machine])

    # Objective function (a)
    if objective == "completion-times":
        model.setObjective(gp.quicksum(C[j] for j in range(n_jobs)), GRB.MINIMIZE)

    # Objective funtction (b)
    elif objective == "makespan":
        Cmax = model.addVar(lb=0, name="Cmax")
        for j in range(n_jobs):
            model.addConstr(Cmax >= C[j])
        model.setObjective(Cmax, GRB.MINIMIZE)

    # store variables for later inspection
    model._S = S
    model._x = x
    model._C = C

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--filename", default="instances/2-scheduling-instance.dat")
    parser.add_argument("--objective", choices=["completion-times", "makespan"], default="completion-times")
    args = parser.parse_args()

    objective = args.objective
    processing_times, machine_sequences = read_instance_file(args.filename)
    n_jobs, n_machines = processing_times.shape

    model = gp.Model(f"2-scheduling-{objective}")
    build_model(model, objective, processing_times, machine_sequences)

    model.update()
    model.optimize()

    S = model._S
    machine_names = ["A", "B", "C", "D"]

    for h in range(n_machines):
        order = sorted(range(n_jobs), key=lambda j: S[j, h].X)
        print(f"{machine_names[h]}: {' -> '.join(str(j+1) for j in order)}")
        
    model.close()
