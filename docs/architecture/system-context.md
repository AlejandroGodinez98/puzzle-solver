```mermaid
flowchart TB
    User["User"]

    System["Puzzle Solver System"]

    User -->|"Selects puzzle type and submits puzzle"| System
    System -->|"Returns puzzle solution"| User

    style System fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
```