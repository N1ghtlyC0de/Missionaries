---

# Missionaries and Cannibals Problem

## 📖 Overview
This repository implements the classic **Missionaries and Cannibals river crossing puzzle** using Python and graph-based state representation. The project models the problem as a search space, defines valid operations, and verifies the solution through state transitions until the desired final state is reached.

---

## 🧩 Problem Statement
Three missionaries and three cannibals must cross a river using a boat.  
Constraints:
- The boat can carry one or two passengers.
- At no point can cannibals outnumber missionaries on either riverbank (otherwise, missionaries are eaten).
- The objective is to move all characters safely across the river.

---

## ⚙️ State Representation
Each state is represented by the distribution of missionaries (M), cannibals (C), and the boat across the two sides of the river.

```python
m_izq, m_der, m_bote = [0], [3], [0]
c_izq, c_der, c_bote = [0], [3], [0]
boat_side = "Derecha"
```

- `m_izq`: missionaries on the left side  
- `m_der`: missionaries on the right side  
- `c_izq`: cannibals on the left side  
- `c_der`: cannibals on the right side  
- `boat_side`: current position of the boat (`Izquierda` or `Derecha`)

Boat position detection logic:
```python
boat_side = "Desconocido"
if boat_pos:
    boat_side = "Izquierda" if boat_pos[0] < mitad_pantalla else "Derecha"
```

---

## 🔄 Possible Operations
The boat can transport combinations of missionaries and cannibals:

- **Two missionaries together**
- **Two cannibals together**
- **One missionary and one cannibal**
- **Single missionary**
- **Single cannibal**

Each operation generates a new state, which must be validated against the safety constraint (missionaries ≥ cannibals on each side, unless missionaries = 0).

---

## 🎯 Final Objective
The puzzle is solved when all missionaries and cannibals are safely on the **left side** with the boat:

```python
if len(estado["izq"]["M"]) == 3 and len(estado["izq"]["C"]) == 3 and lado == "Izquierda":
    print("\n¡VICTORIA LOGRADA! El juego ha sido resuelto con éxito.")
    break
```

---

## 📂 Repository Contents
- **State Representation Diagrams** (`Definitions_Graph.svg`)  
- **Graph Solution** (`Solution_Graph.svg`)  
- **Python Implementation**: State validation, transitions, and solution search  
- **Documentation**: Explanation of graph modeling and algorithmic approach  

---

## 🚀 How to Run
1. Clone the repository:
   ```bash
   git clone https://github.com/N1ghtlyC0de/Missionaries.git
   ```
2. Navigate to the project folder:
   ```bash
   cd Missionaries
   ```
3. Run the Python script:
   ```bash
   python M&C.py
   ```
