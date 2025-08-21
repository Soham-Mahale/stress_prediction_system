import sys
from dataclasses import dataclass
import os

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler,OneHotEncoder

from src.exception import CustomException
from src.logger import logging
from src.utils import save_object


@dataclass
class DataTransformationConfig:
    preprocessor_obj_file_path=os.path.join("artifacts","preprocessor.pkl")

class DataTransformation:
    def __init__(self):
        self.data_transformation_config=DataTransformationConfig()

    def get_data_transformer_obj(self):
        try:
            numerical_columns=['anxiety_level', 'self_esteem', 'mental_health_history', 'depression',
       'headache', 'blood_pressure', 'sleep_quality', 'breathing_problem',
       'noise_level', 'living_conditions', 'safety', 'basic_needs',
       'future_career_concerns', 'social_support', 'peer_pressure',
       'extracurricular_activities', 'bullying']

            numerical_pipeline=Pipeline(
                steps=[('encoder',StandardScaler(with_mean=False))]
            )
            
            logging.info(f"Numerical_columns:{numerical_columns}")

            return numerical_pipeline

        except Exception as e:
            raise CustomException(e,sys)

    def initiate_data_transformation(self,train_path,test_path):
        try:
            train_df=pd.read_csv(train_path)
            test_df=pd.read_csv(test_path)

            train_df=train_df.drop(columns=['academic_performance', 'study_load', 'teacher_student_relationship'],axis=1)
            test_df=test_df.drop(columns=['academic_performance', 'study_load', 'teacher_student_relationship'],axis=1)


            logging.info("Read Train and Test data completed")
            logging.info("Obtating preprocessor model")

            preprocessing_obj=self.get_data_transformer_obj()

            target_column_name=['stress_level']

            input_feature_train_df=train_df.drop(columns=target_column_name,axis=1)
            target_feature_train_df=train_df[target_column_name]

            input_feature_test_df=test_df.drop(columns=target_column_name,axis=1)
            target_feature_test_df=test_df[target_column_name]

            logging.info(f"Apply preprocessing obj on training dataset and testing dataframe")

            input_feature_train_arr=preprocessing_obj.fit_transform(input_feature_train_df)
            input_feature_test_arr=preprocessing_obj.transform(input_feature_test_df)

            train_arr=np.c_[
                input_feature_train_arr,np.array(target_feature_train_df)
            ]
            test_arr=np.c_[input_feature_test_arr,np.array(target_feature_test_df)]

            logging.info("Saved preprocessing objects")
            
            save_object(
                obj=preprocessing_obj,
                file_path=self.data_transformation_config.preprocessor_obj_file_path  
                )
            
            return (
                train_arr,
                test_arr
            )

        except Exception as e:
            raise CustomException(e,sys)