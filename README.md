# MPOT, Exercise Sheet 1 Python Framework

This framework is provided to help you get started with implementing the TSP models on the first exercise sheet. Feel free to alter the code as you see fit.

It uses Python 3.14 and Gurobi 13 (via `gurobipy`).


## Using `uv`

The framework uses `uv` to manage the Python project and its dependencies.

### Installing `uv`

See https://docs.astral.sh/uv/getting-started/installation/ on how to install it.

### Setting up the virtual enrivonment

Run `uv sync` to set up the virtual environment with all dependencies.

### Adding dependencies

Run `uv add name_of_python_package` to add a new dependency to `pyproject.toml`.


## Installing Gurobi

The Gurobi version included with `gurobipy` supports only models with up to 2k variables and constraints.

For larger instances (which will be required for larger instances and formulations), you'll need a license. You can get a free academic named-user license to run Gurobi on your computer if you register with your TU-Wien-provided email address. See here for details: https://www.gurobi.com/features/academic-named-user-license/
Note that you'll need to be in the TU Wien network (Wi-Fi or VPN) to activate your license for the first time.


## Using the framework

Run

```
uv run src/mpot_ex1/tsp_solver.py -h
```

from the project root directory (the one containing `pyproject.toml`) to print the usage message.

You will need to run it for three instances (`--instance`)
* `instances/ulysses16.tsp`
* `instances/dantzig42.tsp`
* `instances/att48.tsp`

for three TSP formulations (`--formulation`)
* `seq`
* `scf`
* `mcf`