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

## Setup

1. Clone this repo
2. Install dependencies: `pip install -r requirements.txt`
3. Add your Gemini API keys to `.streamlit/secrets.toml` (see `secrets.toml.example`)
4. Run: `streamlit run app.py`
