import os
import sys
from dataclasses import dataclass

from catboost import CatBoostClassifier
from sklearn.ensemble import (
    AdaBoostClassifier,
    GradientBoostingClassifier,
    RandomForestClassifier
)

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier

from src.exception import CustomException
from src.logger import logging
from src.utils import save_object,evaluate_model

@dataclass
class ModelTrainerConfig:
    trained_model_file_path=os.path.join("artifacts",'model.pkl')

class ModelTrainer:
    def __init__(self):
        self.model_trainer_config=ModelTrainerConfig()

    def initiate_model_trainer(self,train_array,test_array):
        try:
            logging.info("Split training and test input data")
            X_train,y_train,X_test,y_test=(
                train_array[:,:-1],
                train_array[:,-1],
                test_array[:,:-1],
                test_array[:,-1]
            )
            models={
                "Decision Tree": DecisionTreeClassifier(),
                'Random Forest':RandomForestClassifier(),
                'Gradient Boosting':GradientBoostingClassifier(),
                'XGB Classifier':XGBClassifier(),
                'Catboosting Classifier':CatBoostClassifier(verbose=False),
                'Adaboosting Classifier':AdaBoostClassifier()
            }

            params={
                "Decision Tree": 
                {
                    'criterion':['gini','entropy'],
                    'max_depth':[10,20,30]
 
                },

                "Random Forest":
                {
                    'max_features':[10,20,30],
                    'max_depth':[10,20,30]
                },

                "Gradient Boosting":
                {
                    # 'loss':['squared_error', 'huber', 'absolute_error', 'quantile'],
                    'learning_rate':[.1,.01,.05,.001],
                    # 'subsample':[0.6,0.7,0.75,0.8,0.85,0.9],
                    # 'criterion':['squared_error', 'friedman_mse'],
                    # 'max_features':['auto','sqrt','log2'],
                    'n_estimators': [8,16,32,64,128,256]
                },

                "XGB Classifier":
                {
                    'learning_rate':[.1,.01,.05,.001],
                    'n_estimators': [8,16,32,64,128,256]
                },

                "Catboosting Classifier":
                {
                    'depth': [8,10,12],
                    'learning_rate': [0.01, 0.05, 0.1],
                    'iterations': [30,50,100],
                },

                "Adaboosting Classifier":
                {
                    'learning_rate':[.1,.01,0.5,.001],
                    # 'loss':['linear','square','exponential'],
                    'n_estimators': [8,16,32,45,64,128,256]
                }
                
            }

            best_model,best_model_score=evaluate_model(X_train=X_train,y_train=y_train,X_test=X_test,y_test=y_test,
                                             models=models,param=params)
            # print(model_report.items())
            # best_model_score=max(sorted(list((model_report.values()))))

            # best_model_name = list(models.keys())[list(model_report.values()).index(best_model_score)]
            
            # print(best_model_name,best_model_score)
            # best_model=models[best_model_name]
            
            if best_model_score<0.6:
                raise CustomException("No best model found")
            
            logging.info("Best Model found on both training and test dataset")

            save_object(file_path=self.model_trainer_config.trained_model_file_path,
                        obj=best_model)
            
            predicted=best_model.predict(X_test)

            accuracy_score_model=accuracy_score(predicted,y_test)

            return accuracy_score_model

        except Exception as e:
            raise CustomException(e,sys)
    
