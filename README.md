# Smart University Scheduler using Genetic Algorithms

This project is an intelligent two-part scheduling system designed to solve complex timetabling problems for a university. It uses Genetic Algorithms to first generate a conflict-free master schedule for all courses and then create an optimal, personalized schedule for individual students.

##  Key Features

- **Two-Part System:** Logically separates the master scheduling problem from the student scheduling problem.
- **Genetic Algorithm Core:** Utilizes the `pygad` library to handle complex optimization and find near-optimal solutions.
- **Constraint Handling:** Manages both hard constraints (e.g., no two lectures in the same room at the same time) and soft constraints (e.g., teacher time preferences).
- **Advanced Scheduling:** Includes features like demographic filtering and schedule diversification to enhance the quality of recommendations.

---

##  How It Works

The system operates in two distinct phases, demonstrated in two separate Jupyter Notebooks:

1.  **Part 1: Master Schedule Generation** (`1_Master_Schedule_Generation.ipynb`)
    -   This notebook takes all courses, classrooms, teachers, and their constraints as input.
    -   It runs a Genetic Algorithm to produce a valid and optimized `master_schedule.csv`.

2.  **Part 2: Student Schedule Generation** (`2_Student_Schedule_Generation.ipynb`)
    -   This notebook uses the `master_schedule.csv` created in Part 1.
    -   For a specific student, it finds the best possible personal timetable based on their registered courses, ensuring no time conflicts.

---

##  Technologies Used

-   **Language:** Python
-   **Libraries:**
    -   `pandas` for data manipulation.
    -   `pygad` for the Genetic Algorithm implementation.
    -   `Jupyter Notebook` for demonstration and analysis.

---

##  How to Run

To understand the project, please view the Jupyter Notebooks in the following order:

1.  Open and run the cells in `1_Master_Schedule_Generation.ipynb`.
2.  Then, open and run the cells in `2_Student_Schedule_Generation.ipynb`.

