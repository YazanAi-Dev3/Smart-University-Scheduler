# student_scheduler_ga.py

import pandas as pd
import pygad
import logging
from collections import defaultdict

class StudentData:
    """
    Prepares and holds all data required for scheduling a single student.
    """
    def __init__(self, student_id, master_schedule_df, registrations_df):
        logging.info(f"Initializing StudentData for student_id: {student_id}")
        self.student_id = student_id
        self.master_schedule = master_schedule_df
        self.registrations = registrations_df
        
        # This will hold the grouped lectures, e.g., {'CS101': [lec1, lec2], 'CS102': [lec3, lec4]}
        self.lecture_groups = defaultdict(list)
        self.student_courses = [] # The list of course_id's the student is taking
        
        self._prepare_student_data()

    def _prepare_student_data(self):
        """
        Filters data for the specific student and groups available lectures by course.
        """
        student_regs = self.registrations[self.registrations['student_id'] == self.student_id]
        if student_regs.empty:
            raise ValueError(f"No registration data found for student_id: {self.student_id}")
            
        self.student_courses = student_regs['course_id'].tolist()
        logging.info(f"Student {self.student_id} is registered in {len(self.student_courses)} courses: {self.student_courses}")

        # For each lecture in the master schedule, add it to the correct course group
        for _, lecture in self.master_schedule.iterrows():
            if lecture['course_id'] in self.student_courses:
                self.lecture_groups[lecture['course_id']].append(lecture.to_dict())
        
        # Ensure the student is registered for courses that actually exist in the master schedule
        for course in self.student_courses:
            if not self.lecture_groups[course]:
                logging.warning(f"No lectures found in master_schedule for registered course: {course}")


class StudentSchedulerGA:
    """
    Encapsulates the GA logic for finding an optimal schedule for a single student.
    """
    def __init__(self, student_data, ga_params):
        logging.info("Initializing StudentSchedulerGA...")
        self.student_data = student_data
        self.ga_params = ga_params

        # The number of genes is the number of courses the student is taking.
        self.num_genes = len(self.student_data.student_courses)
        
        # The value of each gene is the index of the chosen lecture for that course.
        self.gene_space = []
        for course_id in self.student_data.student_courses:
            num_available_lectures = len(self.student_data.lecture_groups[course_id])
            if num_available_lectures == 0:
                # This should not happen if data is clean, but as a safeguard:
                raise ValueError(f"Course {course_id} has no available lectures in the master schedule.")
            self.gene_space.append({'low': 0, 'high': num_available_lectures})

        self.ga_instance = self._create_ga_instance()

    def _decode_solution(self, solution):
        """Converts a solution [0, 2, 1] into a list of actual lecture dictionaries."""
        student_schedule = []
        for i, course_id in enumerate(self.student_data.student_courses):
            chosen_lecture_index = int(solution[i])
            # Select the chosen lecture from the available options for that course
            selected_lecture = self.student_data.lecture_groups[course_id][chosen_lecture_index]
            student_schedule.append(selected_lecture)
        return student_schedule

    def _fitness_function(self, ga_instance, solution, solution_idx):
        """
        Calculates the fitness of a student's schedule.
        The primary goal is to avoid time conflicts.
        """
        penalty = 0
        
        # Decode the chromosome into a readable schedule
        proposed_schedule = self._decode_solution(solution)
        
        # --- Hard Constraint: Time Conflict ---
        # A student cannot attend two lectures at the same time.
        booked_timeslots = set()
        for lecture in proposed_schedule:
            timeslot = lecture['timeslot']
            if timeslot in booked_timeslots:
                penalty += 1000  # High penalty for conflicts
            else:
                booked_timeslots.add(timeslot)
        
        # --- Soft Constraint: Minimize total study days (optional) ---
        # Encourages a more compact schedule.
        study_days = {lecture['Day'] for lecture in proposed_schedule}
        penalty += len(study_days) * 10 # Add 10 penalty points for each day student has to come

        fitness = 1.0 / (penalty + 1e-9)
        return fitness

    @staticmethod
    def _on_generation(ga_instance):
        """A callback to log progress."""
        logging.info(
            f"Gen {ga_instance.generations_completed} | "
            f"Best Fitness: {ga_instance.best_solutions_fitness[-1]:.6f}"
        )
        
    def _create_ga_instance(self):
        """Configures and returns the PyGAD instance."""
        return pygad.GA(
            num_generations=self.ga_params['generations'],
            num_parents_mating=self.ga_params['parents_mating'],
            fitness_func=self._fitness_function,
            sol_per_pop=self.ga_params['sol_per_pop'],
            num_genes=self.num_genes,
            gene_space=self.gene_space,
            parent_selection_type="sss",
            crossover_type="single_point",
            mutation_type="random",
            mutation_percent_genes=self.ga_params['mutation_percent'],
            on_generation=self._on_generation,
            suppress_warnings=True,
            save_best_solutions=True
        )

    def run(self):
        """Runs the GA and returns the best schedule found."""
        logging.info(f"Running GA for student {self.student_data.student_id}...")
        self.ga_instance.run()
        logging.info("GA finished.")

        best_solution, best_fitness, _ = self.ga_instance.best_solution()
        best_schedule_decoded = self._decode_solution(best_solution)
        
        return best_schedule_decoded