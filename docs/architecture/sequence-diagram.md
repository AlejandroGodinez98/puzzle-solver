sequenceDiagram
    autonumber

    actor User
    participant React as React Frontend
    participant Controller as PuzzleController
    participant Service as PuzzleService
    participant Client as ImageProcessingClient
    participant Python as FastAPI
    participant OCR as OCR Engine
    participant Registry as PuzzleSolverRegistry
    participant Solver as PuzzleSolver

    User->>React: Select puzzle type
    User->>React: Submit puzzle

    alt Image Upload

        React->>Controller: POST /{type}/solve-image

        Controller->>Service: solveImage(type, file)

        Service->>Client: extract(type, file)

        Client->>Python: HTTP POST image + type

        Python->>OCR: Extract puzzle data

        OCR-->>Python: Board + metadata

        Python-->>Client: JSON response

        Client-->>Service: Extracted puzzle

    else Structured JSON

        React->>Controller: POST /{type}/solve

        Controller->>Service: solve(type, puzzleData)

    end

    Service->>Registry: getSolver(type)

    Registry-->>Service: Selected solver

    Service->>Solver: solve(puzzleData)

    Solver-->>Service: PuzzleResult

    Service-->>Controller: PuzzleResult

    Controller-->>React: HTTP 200 + JSON

    React-->>User: Display solution