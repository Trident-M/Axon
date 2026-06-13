# 🌸 Axon · AI Command Center

Axon is an autonomous multi-agent AI system that decomposes complex tasks into 
specialist sub-tasks, routes them through a quantum-inspired execution order, 
and synthesizes the results into a polished, SEO-optimized output — all wrapped 
in a sleek purple-sakura themed dashboard.

## How It Works (The Axon Pipeline)

Every task submitted to Axon flows through a 6-layer pipeline:

1. **DWSA Decomposer** — Breaks the user's request into 4–6 atomic, non-overlapping subtasks.
2. **Quantum Router** — A Qiskit quantum circuit (H-gates, Ry rotations weighted by 
   subtask priority, and entangled CX gates) determines the optimal execution order 
   for the agent swarm.
3. **Agent Swarm** — Specialist AI agents execute each subtask in quantum-determined 
   order, reading and writing to a shared **Quantum Brain** (a live memory store) to 
   avoid redundant work and build on each other's findings.
4. **Brain Synthesis** — A synthesizer agent unifies all agent outputs and brain 
   entries into one coherent response.
5. **Critic + Verifier** — Two independent audit agents check the synthesized output 
   for contradictions, weak reasoning, missing information, and overall consistency, 
   producing confidence scores.
6. **SEO Agent** — Optimizes and scores the final content (SEO score, readability, 
   keywords, meta description) before delivery.

The pipeline produces a final **AP Score** combining readability, SEO performance, 
and task complexity, along with a real-time confidence rating.

## Features

- 🤖 Multi-agent task execution with live "Quantum Brain" memory visualization
- ⚛ Real quantum circuit simulation (Qiskit + AerSimulator) for agent routing
- 🔍 Self-critic and verification layers for output quality assurance
- 📊 Live pipeline dashboards, agent mesh monitoring, and confidence metrics
- 🌸 Interactive 3D quantum sphere visualizer and animated sakura-themed UI
- 💬 Built-in customer help assistant

## Tech Stack

- **Frontend:** Streamlit
- **AI:** Google Gemini (gemini-2.5-flash) via `google-generativeai`
- **Quantum Simulation:** Qiskit + Qiskit Aer
- **Styling:** Custom CSS, animated SVG/Canvas elements

## ⚛️ The Quantum Routing Engine: Architectural Justification

A common question during technical evaluation is: *Why utilize a simulated quantum circuit (`Qiskit` + `AerSimulator`) for Directed Acyclic Graph (DAG) task routing instead of a traditional deterministic sorting algorithm?*

Axon implements a **Quantum-Inspired Heuristic Scheduler** to explore complex, co-dependent decision spaces for multi-agent workflows. When a user input is broken down by the Divisible Work Sharing Orchestration (DWSA) Decomposer, the resulting subtasks are rarely completely independent; they possess fluid priorities and execution constraints.

### Mathematical Mapping
1. **Qubit Initialization:** Each atomic subtask decomposed from the master prompt maps directly to an individual qubit ($q_i$).
2. **Superposition via Hadamard Gates ($H$):** We apply a Hadamard gate to every qubit to put the system into an equal superposition of all possible execution sequences. This allows the system to evaluate parallel arrangement spaces simultaneously.
3. **Priority Biasing via $Ry(\theta)$ Rotations:** Instead of flat sorting, task priority weights dynamically calculate a rotation angle $\theta$. Applying $Ry(\theta)$ shifts the probability amplitudes, biasing the eventual measurement toward mathematically optimal execution orders.
4. **Dependency Encoding via Controlled-NOT ($CX$) Gates:** Entanglement chains model hard topological constraints. If Task B depends heavily on the output of Task A, a $CX$ gate entangles $q_A$ and $q_B$, ensuring that invalid parallel sequences collapse to a zero-probability state upon observation.

### Execution Collapse
By running **512 shots** on the `AerSimulator`, we extract a clean, probabilistic frequency distribution. The highest-frequency state is measured to determine the final, absolute execution pipeline order. This provides an elegant, non-linear optimization model that natively scales as multi-agent interdependencies grow more complex.
