import gurobipy as gp
from gurobipy import GRB

# Parameters
n = 18
k = 3



model = gp.Model("task3_SportsLeague")


# This implementation is the same as the ILP formulation in the pdf, EXCEPT for the indexing.
# As it is common, the indizes run from 1...n in the pdf, but from 0...n-1 in the code.


w = model.addVars([(i, j) for i in range(0, n) for j in range(0, n) if i != j], vtype=GRB.INTEGER, lb=0, ub=2, name="w")
d = model.addVars([(i, j) for i in range(0, n) for j in range(i + 1, n)], vtype=GRB.INTEGER, lb=0, ub=2, name="d")
p = model.addVars(n, vtype=GRB.INTEGER, lb=0, name="p")

model.setObjective(p[k-1], GRB.MAXIMIZE)





for i in range(n):
    for j in range(i + 1, n):
        model.addConstr(w[i, j] + d[i, j] <= 2, name=f"outcome_{i + 1}_{j + 1}")

# this uses the symmetry mentioned in the ILP formulation 
for i in range(n):
    win_pts = gp.quicksum(3 * w[i, j] for j in range(0, n) if i != j)
    win_pts = gp.quicksum(3 * w[i, j] for j in range(i + 1, n)) + \
               gp.quicksum(3 * (2 - w[j, i] - d[j, i]) for j in range(0, i))  

    draw_pts = gp.quicksum(1 * d[i, j] for j in range(i + 1, n)) + \
               gp.quicksum(1 * d[j, i] for j in range(0, i))  
    
    model.addConstr(p[i] == win_pts + draw_pts, name=f"total_pts_{i + 1}")

for i in range(0, n - 1):
    model.addConstr(p[i] <= p[i + 1], name=f"order_{i + 1}")




model.optimize()

if model.status == GRB.OPTIMAL:
    max_relegated_score = int(model.objVal)
    guaranteed_safety = max_relegated_score + 1
    
    print()
    print()
    print()
    print("========================================")
    print(f"Results for n={n}, k={k}:")
    print(f"Max points for k-th team: {max_relegated_score}")
    print(f"Points needed for safety: {guaranteed_safety}")
    print("========================================")
else:
    print("ERROR - not optimal solution found")

