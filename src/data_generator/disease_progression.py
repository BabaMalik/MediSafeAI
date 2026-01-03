#### Disease Progression Model

# src/data_generator/disease_progression.py
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


class DiseaseProgressionModel:
    """Simulate realistic disease progression over time"""

    def __init__(self, base_deterioration_rate=0.03, intervention_effectiveness=0.7):
        self.base_deterioration_rate = base_deterioration_rate
        self.intervention_effectiveness = intervention_effectiveness

    def simulate_progression(self, patient_data, start_date=None, end_date=None, visit_interval_days=30, num_visits=None, time_interval_days=None):
        """
        Simulate disease progression with vitals and lab measurements over time

        Args:
            patient_data: Patient information dictionary
            start_date: Start date for simulation (optional if num_visits provided)
            end_date: End date for simulation (optional if num_visits provided)
            visit_interval_days: Days between visits (default 30)
            num_visits: Number of visits to simulate (alternative to start/end dates)
            time_interval_days: Alias for visit_interval_days
        """
        # Handle alternative parameter names
        if time_interval_days is not None:
            visit_interval_days = time_interval_days

        # If num_visits provided, calculate dates
        if num_visits is not None:
            from datetime import datetime
            start_date = datetime.now().date() if start_date is None else start_date
            from datetime import timedelta
            end_date = start_date + timedelta(days=visit_interval_days * (num_visits - 1))

        # Ensure we have dates
        if start_date is None or end_date is None:
            from datetime import datetime, timedelta
            start_date = datetime.now().date()
            end_date = start_date + timedelta(days=365)  # Default to 1 year
        patient_id = patient_data['patient_id']

        # Initialize with baseline health metrics based on patient condition
        has_diabetes = patient_data['diabetes'] == 1
        has_hypertension = patient_data['hypertension'] == 1
        has_heart_disease = patient_data['heart_disease'] == 1
        age = patient_data['age']

        # Set baseline values with appropriate physiological ranges
        baseline = {
            'systolic_bp': 120 + (20 if has_hypertension else 0) + (age // 20),
            'diastolic_bp': 80 + (10 if has_hypertension else 0) + (age // 30),
            'heart_rate': 75 + (10 if has_heart_disease else 0) - (age // 20),
            'blood_glucose': 100 + (80 if has_diabetes else 0),
            'cholesterol': 180 + (40 if has_heart_disease else 0) + (age // 10),
            'body_temp': 98.6,
            'respiratory_rate': 16 + (2 if has_heart_disease else 0),
            'weight': max(110, 150 + np.random.normal(0, 15)) - (age * 0.1)
        }

        # Calculate how many readings we'll have
        current_date = start_date
        visits = []
        deterioration_factor = 1.0

        # Generate progression across visits
        while current_date <= end_date:
            visit_data = {
                'patient_id': patient_id,
                'visit_date': current_date
            }

            # Simulate natural disease progression with some random variation
            for metric, base_value in baseline.items():
                # Add natural progression and random noise
                if metric in ['systolic_bp', 'diastolic_bp', 'blood_glucose', 'cholesterol']:
                    # These metrics tend to increase with disease progression
                    progression = base_value * (
                            1 +
                            self.base_deterioration_rate * deterioration_factor *
                            np.random.uniform(0.5, 1.5)
                    )
                elif metric in ['weight']:
                    # Weight can increase or decrease depending on condition
                    change = np.random.normal(0, 2)
                    progression = base_value + change
                elif metric in ['heart_rate', 'respiratory_rate']:
                    # These might fluctuate but not necessarily increase
                    progression = base_value * (
                            1 +
                            np.random.normal(0, 0.1)
                    )
                else:
                    # Other metrics remain relatively stable
                    progression = base_value * (
                            1 +
                            np.random.normal(0, 0.02)
                    )

                visit_data[metric] = progression

            # Add lab results that would typically be measured
            visit_data['hemoglobin_a1c'] = 5.7 + (2.5 if has_diabetes else 0) * deterioration_factor
            visit_data['white_blood_cell'] = 7500 + np.random.normal(0, 1000)
            visit_data['creatinine'] = 1.0 + (0.5 if has_diabetes else 0) * deterioration_factor

            # Disease-specific metrics
            if has_diabetes:
                visit_data['insulin_level'] = max(2, 15 - (5 * deterioration_factor) + np.random.normal(0, 1))

            if has_heart_disease:
                visit_data['ejection_fraction'] = max(25, 60 - (10 * deterioration_factor) + np.random.normal(0, 3))
                visit_data['troponin'] = min(0.5, 0.01 * deterioration_factor + np.random.exponential(0.02))

            # Add intervention effects (simulating treatments)
            if current_date.month % 3 == 0:  # Quarterly major intervention
                intervention_effectiveness = np.random.uniform(0.3, 0.8)
                deterioration_factor = max(1.0, deterioration_factor * (1 - intervention_effectiveness))
                visit_data['intervention'] = 'major'
            elif current_date.month % 2 == 0:  # Bi-monthly minor intervention
                minor_effectiveness = np.random.uniform(0.1, 0.3)
                deterioration_factor = max(1.0, deterioration_factor * (1 - minor_effectiveness))
                visit_data['intervention'] = 'minor'
            else:
                visit_data['intervention'] = 'none'
                deterioration_factor *= 1.1  # Natural disease progression continues

            visits.append(visit_data)

            # Move to next visit
            current_date += timedelta(days=visit_interval_days)

        df = pd.DataFrame(visits)
        # Add visit numbers
        df.insert(0, 'visit_number', range(1, len(df) + 1))
        return df

    def simulate_progression_by_visits(self, patient_data, num_visits=12, time_interval_days=30):
        """
        Convenient wrapper to simulate progression by number of visits instead of dates

        Args:
            patient_data: Patient information dictionary
            num_visits: Number of visits to simulate
            time_interval_days: Days between visits

        Returns:
            DataFrame with progression data
        """
        from datetime import datetime, timedelta

        start_date = datetime.now().date()
        # Calculate end date based on number of visits
        end_date = start_date + timedelta(days=time_interval_days * (num_visits - 1))

        df = self.simulate_progression(
            patient_data,
            start_date,
            end_date,
            visit_interval_days=time_interval_days
        )

        # Add visit numbers
        df.insert(0, 'visit_number', range(1, len(df) + 1))

        return df

