# src/privacy/anonymization.py

import pandas as pd
import hashlib


class Anonymizer:
    """Class to anonymize PII (Personally Identifiable Information) in healthcare datasets."""

    def __init__(self, hash_patient_id=True):
        self.hash_patient_id = hash_patient_id

    def hash_string(self, value: str) -> str:
        """Return a hashed version of a string using SHA-256"""
        return hashlib.sha256(value.encode()).hexdigest()[:10]  # Shorten for readability

    def anonymize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Anonymize PII columns in the DataFrame"""
        df = df.copy()

        # Drop names
        if 'first_name' in df.columns:
            df.drop(columns=['first_name'], inplace=True)
        if 'last_name' in df.columns:
            df.drop(columns=['last_name'], inplace=True)

        # Mask zip code
        if 'zip_code' in df.columns:
            df['zip_code'] = df['zip_code'].astype(str).str[:3] + '**'

        # Convert DOB to age group if DOB exists
        if 'dob' in df.columns and 'age' not in df.columns:
            df['age'] = pd.to_datetime('today').year - pd.to_datetime(df['dob']).dt.year
            df.drop(columns=['dob'], inplace=True)

        # Hash patient_id (optional)
        if self.hash_patient_id and 'patient_id' in df.columns:
            df['patient_id'] = df['patient_id'].apply(self.hash_string)

        return df
