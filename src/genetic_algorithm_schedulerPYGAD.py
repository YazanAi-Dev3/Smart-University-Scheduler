# genetic_algorithm_scheduler.py

import pandas as pd
import pygad
import logging

class DataPreparer:
    """
    Handles loading and pre-processing of all necessary data for the scheduler.
    """
    def __init__(self, courses, classrooms, teacher_courses, teacher_preferences):
        logging.info("Initializing DataPreparer...")
        self.courses = courses
        self.classrooms = classrooms
        self.teacher_courses = teacher_courses
        self.teacher_preferences = teacher_preferences
        
        self.lectures_to_schedule = []
        self.timeslots = []
        self.teacher_pref_dict = {}
        
        self._prepare_data()
        logging.info("DataPreparer initialized successfully.")

    def _prepare_data(self):
        """
        Processes raw dataframes into structures needed by the GA.
        """
        logging.debug("Starting data preparation...")
        # Create a list of all individual lectures that need to be scheduled
        for _, row in self.teacher_courses.iterrows():
            teacher_id = row['teacher_id']
            course_id = row['course_id']
            num_lectures = self.courses[self.courses['course_id'] == course_id]['lectures_per_week'].iloc[0]
            for _ in range(num_lectures):
                self.lectures_to_schedule.append({'course_id': course_id, 'teacher_id': teacher_id})

        # Create a list of all possible timeslots
        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']
        hours = range(8, 17)  # 8 AM to 4 PM
        for day in days:
            for hour in hours:
                self.timeslots.append(f"{day}_{hour:02d}:00")

        # Store teacher preferences in a fast-access dictionary
        for _, row in self.teacher_preferences.iterrows():
            key = (row['teacher_id'], row['day'])
            if key not in self.teacher_pref_dict:
                self.teacher_pref_dict[key] = []
            self.teacher_pref_dict[key].append((row['preferred_start_time'], row['preferred_end_time']))

        logging.info(f"Data prepared: {len(self.lectures_to_schedule)} total lectures to schedule.")
        logging.debug(f"Total available timeslots: {len(self.timeslots)}.")
        logging.debug(f"Total available classrooms: {len(self.classrooms)}.")


class SchedulerGA:
    """
    Encapsulates the entire Genetic Algorithm logic using the PyGAD library.
    """
    def __init__(self, data_preparer, ga_params):
        logging.info("Initializing SchedulerGA...")
        self.data_preparer = data_preparer
        self.ga_params = ga_params
        
        # Define the structure of the solution (chromosome)
        self.num_lectures = len(self.data_preparer.lectures_to_schedule)
        self.num_genes = self.num_lectures * 2  # Each lecture has 2 genes: room_id_idx and timeslot_idx

        # Define the possible values for each gene
        self.gene_space = []
        for _ in range(self.num_lectures):
            # Gene for classroom index
            self.gene_space.append({'low': 0, 'high': len(self.data_preparer.classrooms)})
            # Gene for timeslot index
            self.gene_space.append({'low': 0, 'high': len(self.data_preparer.timeslots)})
        
        self.ga_instance = self._create_ga_instance()
        logging.info("PyGAD instance created and configured.")

    def _decode_solution(self, solution):
        """Converts a flat solution array from PyGAD into a readable schedule."""
        schedule = []
        for i in range(self.num_lectures):
            lecture_info = self.data_preparer.lectures_to_schedule[i]
            room_index = int(solution[i*2])
            timeslot_index = int(solution[i*2 + 1])
            
            lecture = {
                'course_id': lecture_info['course_id'],
                'teacher_id': lecture_info['teacher_id'],
                'room_id': self.data_preparer.classrooms['room_id'].iloc[room_index],
                'timeslot': self.data_preparer.timeslots[timeslot_index]
            }
            schedule.append(lecture)
        return schedule

    def _calculate_penalty(self, schedule):
        """Calculates the total penalty for a given schedule."""
        penalty = 0
        teacher_bookings, room_bookings = {}, {}
        
        for lecture in schedule:
            # Teacher Conflict
            teacher_key = (lecture['teacher_id'], lecture['timeslot'])
            if teacher_key in teacher_bookings: penalty += 1000
            else: teacher_bookings[teacher_key] = 1
            
            # Room Conflict
            room_key = (lecture['room_id'], lecture['timeslot'])
            if room_key in room_bookings: penalty += 1000
            else: room_bookings[room_key] = 1
            
            # Teacher Availability
            teacher_id, day, time = lecture['teacher_id'], *lecture['timeslot'].split('_')
            pref_key = (teacher_id, day)
            if pref_key in self.data_preparer.teacher_pref_dict:
                is_within_preference = any(start <= time < end for start, end in self.data_preparer.teacher_pref_dict[pref_key])
                if not is_within_preference: penalty += 500
            else:
                penalty += 500 # Assume unavailable if no preference is specified for the day
                
        return penalty

    def _fitness_function(self, ga_instance, solution, solution_idx):
        """The fitness function to be used by PyGAD."""
        schedule = self._decode_solution(solution)
        penalty = self._calculate_penalty(schedule)
        
        # PyGAD maximizes fitness, so we convert penalty (lower is better) to fitness (higher is better)
        fitness = 1.0 / (penalty + 1e-9) # Add epsilon to avoid division by zero
        return fitness
    
    @staticmethod
    def _on_generation(ga_instance):
        """A callback function to log progress after each generation."""
        logging.info(
            f"Generation {ga_instance.generations_completed} | "
            f"Best Fitness: {ga_instance.best_solutions_fitness[-1]:.6f}"
        )

    def _create_ga_instance(self):
        """Configures and returns a PyGAD instance."""
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
            # Suppress PyGAD's internal print statements to avoid clutter
            suppress_warnings=True,
            save_best_solutions=True
        )

    def run(self):
        """Runs the genetic algorithm and returns the best found schedule."""
        logging.info("Starting Genetic Algorithm evolution...")
        self.ga_instance.run()
        logging.info("Genetic Algorithm finished.")
        
        best_solution, best_fitness, _ = self.ga_instance.best_solution()
        best_schedule_decoded = self._decode_solution(best_solution)
        final_penalty = self._calculate_penalty(best_schedule_decoded)

        return best_schedule_decoded, final_penalty