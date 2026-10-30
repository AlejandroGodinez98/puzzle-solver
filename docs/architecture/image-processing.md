flowchart TD
    Image["Image + Puzzle Type"]

    Validation["Validate Image"]
    Preprocessing["Image Preprocessing<br/>OpenCV"]

    Type{"Puzzle Type?"}

    subgraph WordSearch["Word Search Extraction"]
        DetectLetters["Detect Letter Grid"]
        LetterOCR["Recognize Letters"]
        WordList["Extract Word List"]
        WordJSON["Generate Word Search JSON"]
    end

    subgraph Sudoku["Sudoku Extraction"]
        DetectGrid["Detect 9x9 Grid"]
        DigitOCR["Recognize Digits"]
        EmptyCells["Identify Empty Cells"]
        SudokuJSON["Generate Sudoku JSON"]
    end

    Response["Return JSON to Spring Boot"]

    Image --> Validation
    Validation --> Preprocessing
    Preprocessing --> Type

    Type -->|"WORD_SEARCH"| DetectLetters
    DetectLetters --> LetterOCR
    LetterOCR --> WordList
    WordList --> WordJSON

    Type -->|"SUDOKU"| DetectGrid
    DetectGrid --> DigitOCR
    DigitOCR --> EmptyCells
    EmptyCells --> SudokuJSON

    WordJSON --> Response
    SudokuJSON --> Response

    style WordJSON fill:#dcfce7,stroke:#16a34a,color:#166534
    style SudokuJSON fill:#dcfce7,stroke:#16a34a,color:#166534