import os
import sys

import pandas as pd
import numpy as np
import dill
from sklearn.metrics import r2_score,accuracy_score
from sklearn.model_selection import GridSearchCV

from src.exception import CustomException

def save_object(file_path,obj):
    try:
        dir_path=os.path.dirname(file_path)

        os.makedirs(dir_path,exist_ok=True)

        with open(file_path,"wb") as file_obj:
            dill.dump(obj,file_obj)

    except Exception as e:
        raise CustomException(e,sys)
    
def evaluate_model(X_train,y_train,X_test,y_test,models,param):
    try:
        report={}
        
        for model_name,model in models.items():
            para=param[model_name]

            gs=GridSearchCV(model,para,cv=5)
            gs.fit(X_train,y_train)

            # model.fit(X_train,y_train)

            y_train_pred=gs.predict(X_train)

            y_test_pred=gs.predict(X_test)

            train_model_score=accuracy_score(y_train_pred,y_train)

            test_model_score=accuracy_score(y_test_pred,y_test)

            report[model_name] = {
                'test_accuracy': test_model_score
                }
            print(model_name,test_model_score)

        best_model_score=gs.best_score_
        best_model =gs.best_estimator_

        print(best_model_score,best_model)

        return best_model,best_model_score

    except Exception as e:
        raise CustomException(e,sys)
    
def load_object(file_path):
    try:
        with open(file_path,"rb") as file_obj:
            return dill.load(file_obj)

    except Exception as e:
        raise CustomException(e,sys)

def user_input_scaling_anxiety(user_input:int):
    original_max=67
    original_min=19
    scaled_input=original_min+((user_input-1)*((original_max + original_min)/9))

    return scaled_input


def user_input_scaling_depression(user_input:int):
    original_max=66
    original_min=16
    scaled_input=original_min+((user_input-1)*((original_max + original_min)/9))

    return scaled_input


def user_input_scaling_self_esteem(user_input:int):
    original_max=83
    original_min=19
    scaled_input=original_min+((user_input-1)*((original_max + original_min)/9))

    return scaled_input