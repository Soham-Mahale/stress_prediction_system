from fastapi import FastAPI,Path,HTTPException,Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel,Field,computed_field,field_validator,model_validator
from typing import Annotated,Literal,Optional
import json
import pprint

from pymongo import MongoClient
from bson import ObjectId   
import pickle
import numpy as np
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage,AIMessage,SystemMessage


load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

app=FastAPI()

# another pc access
origins = [
    "http://localhost:5173",  # Vite React frontend
    "http://192.168.29.244:5173",  # If you access via LAN
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,         # Allow specific origins
    allow_credentials=True,
    allow_methods=["*"],           # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],           # Allow all headers
)



# utilities
def parse_tasks(tasks_dict):
    """
    Parse tasks from a solution payload into structured format.
    Supports AI output with numbered solution keys and separate subtasks lists.

    Output format:
    {
      "1": {
          "title": "...",
          "description": "...",
          "subtasks": {"1": "...", "2": "..."}
      }
    }
    """
    print("tasks_parsed",tasks_dict)
    structured_tasks = {}

    for key, value in tasks_dict.items():
        if not key.isdigit():
            continue

        raw_text = str(value).strip()
        title = raw_text
        description = ""
        subtasks = {}
        subtask_key = f"subtasks_{key}"

        # If subtasks are provided as a separate list
        if subtask_key in tasks_dict and isinstance(tasks_dict[subtask_key], list):
            if "Subtasks:" in raw_text:
                before, _ = raw_text.split("Subtasks:", 1)
            else:
                before = raw_text

            if ":" in before:
                title, description = [part.strip() for part in before.split(":", 1)]
            else:
                title = before.strip()
                description = ""

            for idx, item in enumerate(tasks_dict[subtask_key], start=1):
                if item is None:
                    continue
                subtasks[str(idx)] = str(item).strip()
        else:
            # Fallback parsing for tasks with inline "Subtasks:" text
            if "Subtasks:" in raw_text:
                before, after = raw_text.split("Subtasks:", 1)
                if ":" in before:
                    title, description = [part.strip() for part in before.split(":", 1)]
                else:
                    title = before.strip()
                    description = ""

                for line in after.split(";" if ";" in after else ","):
                    stripped = line.strip()
                    if not stripped:
                        continue
                    if stripped.startswith("*") or stripped.startswith("-"):
                        cleaned_line = stripped.lstrip("*- ").strip()
                        if cleaned_line:
                            subtasks[str(len(subtasks) + 1)] = cleaned_line
                    else:
                        subtasks[str(len(subtasks) + 1)] = stripped
            else:
                if ":" in raw_text:
                    title, description = [part.strip() for part in raw_text.split(":", 1)]
                else:
                    title = raw_text
                    description = ""

        structured_tasks[key] = {
            "title": title,
            "description": description,
            "subtasks": subtasks
        }

    return structured_tasks

def load_data()->list[dict]:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["stress_management_system"]
    collection = db["users"]
    data = collection.find()
    return list(data)

def save_data(data):
    client = MongoClient("mongodb://localhost:27017/")
    db = client["stress_management_system"]
    collection = db["users"]

    if isinstance(data, dict):
        collection.insert_one(data)
    elif isinstance(data, list) and data:
        collection.insert_many(data)
    else:
        raise ValueError("save_data requires a dict or non-empty list")
        


#new patient creation and get patient details
class Patient(BaseModel):
    name:Annotated[str,Field(...,description="Name of patient",examples=['Soham Mahale'])]
    mobile_no:Annotated[int,Field(...,description="Mobile number of patient",examples=[9876543210])]
    dob:Annotated[str,Field(...,description="Date of Birth of patient",examples=['2000-01-01'])]
    gender:Annotated[str,Literal[Field(...,description='Gender of patient',examples=['Male','Female','Other'])]]
    email:Annotated[str,Field(None,description="Email of patient",examples=['soham@example.com'])]
    password:Annotated[str,Field(...,min_length=6,description="Password of patient",examples=['password123'])]
    streak:Annotated[int,Field(0,description="Streak of patient")]

    @field_validator('mobile_no')
    @classmethod
    def mobile_validator(cls,value):
        if len(str(value))==10:

            data=load_data()

            for patient in data:
                if patient.get("mobile_no")==value:
                    
                    raise HTTPException(status_code=400,detail="Mobile number already exists")

            return value
        raise HTTPException(status_code=400,detail="Mobile number must be 10 digits")

    @field_validator('email')
    @classmethod    
    def email_validator(cls,value):
        value=value.lower()
        value=value.strip()
        if "@" not in value:
            raise HTTPException(status_code=400,detail="Invalid email address")
        return value

    @computed_field
    @property
    def age(self)->int:
        from datetime import datetime
        dob=datetime.strptime(self.dob,"%Y-%m-%d")
        today=datetime.today()
        age=today.year-dob.year

        return age

class Patient_features(BaseModel):
    # mental health features
    anxiety:Annotated[int,Field(...,ge=0,le=10)]
    self_esteem:Annotated[int,Field(...,ge=0,le=10)]
    mental_health_history:Annotated[int,Field(...,ge=0,le=1)]
    depression:Annotated[int,Field(...,ge=0,le=10)]

    # health features
    headache:Annotated[int,Field(...,ge=0,le=5)]
    blood_pressure:Annotated[int,Field(...,ge=1,le=3)]
    sleep_quality:Annotated[int,Field(...,ge=0,le=5)]
    breathing_problems:Annotated[int,Field(...,ge=0,le=5)]

    #environmental features
    noise_level:Annotated[int,Field(...,ge=0,le=5)]
    living_condition:Annotated[int,Field(...,ge=0,le=5)]
    safety:Annotated[int,Field(...,ge=0,le=5)]
    basic_needs:Annotated[int,Field(...,ge=0,le=5)]
    future_carrer_concern:Annotated[int,Field(...,ge=0,le=5,examples=[3])]
    social_support:Annotated[int,Field(...,ge=0,le=3,examples=[3])]
    peer_pressure:Annotated[int,Field(...,ge=0,le=5,examples=[2])]    
    extracuricular_activities:Annotated[int,Field(...,ge=0,le=5,examples=[4])]
    bullying:Annotated[int,Field(...,ge=0,le=5,examples=[2])]

    @model_validator(mode='after')
    @classmethod
    def update_variables(cls,values):

        values.anxiety=values.anxiety*2
        values.self_esteem=values.self_esteem*3
        values.depression=int(values.depression*2.5)
        print(values)
        return values

class Update_Patient(BaseModel):
    name:Optional[Annotated[str,Field(None,description="Name of patient",examples=['Soham Mahale'])]]
    mobile_no:Optional[Annotated[int,Field(None,description="Mobile number of patient",examples=[9876543210])]]
    dob:Optional[Annotated[str,Field(None,description="Date of Birth of patient",examples=['01-01-2000'])]]
    gender:Optional[Annotated[str,Field(None,description='Gender of patient',examples=['Male','Female','Other'])]]
    email:Optional[Annotated[str,Field(None,description="Email of patient",examples=['soham@example.com'])]]
    password:Optional[Annotated[str,Field(None,min_length=6,description="Password of patient",examples=['password123'])]]

    @field_validator('mobile_no')
    @classmethod    
    def mobile_validator(cls,value):
        if len(str(value))!=10:
            raise HTTPException(status_code=400,detail="Mobile number must be 10 digits")
        return value
    
    @field_validator('email')
    @classmethod
    def email_validator(cls,value):
        value=value.lower()
        value=value.strip()
        if "@" not in value:
            raise HTTPException(status_code=400,detail="Invalid email address")
        return value
    
    @computed_field
    @property
    def age(self)->int:
        from datetime import datetime
        dob=datetime.strptime(self.dob,"%d-%m-%Y")
        today=datetime.today()
        age=today.year-dob.year

        return age
    

class MobileUpdate(BaseModel):
    mobile_no:Annotated[int,Field(...,description="New mobile number",examples=[9876543210])]

    @field_validator('mobile_no')
    @classmethod
    def mobile_validator(cls,value):
        if len(str(value))!=10:
            raise HTTPException(status_code=400,detail="Mobile number must be 10 digits")
        return value


@app.post("profile/create")
def create_patient(patient: Patient):
    data=patient.model_dump()

    save_data(data)
    if "_id" in data:
        data["_id"] = str(data["_id"])

    key=['_id','name']
    result=dict()
    for item,value in data.items():
        if item in key:
            result[item]=value

    return JSONResponse(status_code=201, content=result)

@app.post("/predict_stress_level")
def predict_stress_level(patient_features: Patient_features,id:str=Query(...,description="Unique patient id",examples=["64b8f0f5e1b1c8b5f6d7e9a1"])):

    model=pickle.load(open('artifacts/model.pkl','rb'))
    preprocessor=pickle.load(open('artifacts/preprocessor.pkl','rb'))

    client=MongoClient("mongodb://localhost:27017/")
    db=client['stress_management_system']
    collection=db['users']
    

    features=np.array([list(patient_features.model_dump().values())])

    features=preprocessor.transform(features)

    prediction=model.predict(features)

    stress_level=prediction[0]

    stress_mapping={0:'High',1:'Moderate',2:'Low'}

    collection.update_one({'_id':ObjectId(id)},{'$set':{'features':patient_features.model_dump(),'stress_level':stress_level}})

    return JSONResponse(status_code=200,content={"stress_level":stress_mapping[stress_level]})



@app.post("/generate_tasks/{mobile_no}")
def generate_tasks(mobile_no:str):
    client=MongoClient("mongodb://localhost:27017/")
    db=client['stress_management_system']
    collection=db['users']

    patient_data=collection.find_one({'mobile_no':int(mobile_no)})

    if not patient_data:
        raise HTTPException(status_code=404,detail="Patient not found")

    patient_features=Patient_features(**patient_data['features'])

    stress_level=patient_data['stress_level']

    stress_mapping={0:'High',1:'Moderate',2:'Low'}

    # Prompt for chat model
    info_prompt=ChatPromptTemplate(
            [
                SystemMessage
                (
                    content=
                    """->You are an helpful and empathetic mental wellness assistance.\n
                    ->Your goal is to provide supportive, actionable advice and tasks which are performable based on a person's stress level.\n
                    ->There are 3 progessive stress levels:
                        1 = Small or Minor stress caused by burnout, fatigue, etc.(No need of doctor consultance).\n
                        2 = Medium or Mediocar level stress(recommend going for doctor consultance).\n
                        3 = Sever and Large level stress(Strongly recommend doctor consultance).\n
                    ->On this stress level you have to give soltuions such as mental exercises, breathing exercises etc.To help and support the person in stress and to remove his/her stress.Dont forget to recommend the doctor consultancy when required.\n
                    ->Provide suggestion in task format example:cycling,exercising,breathing exercises.In clear, number list on given stress level only.Keep your tone warm and encouraging.\n
                    ->Give the soltion in json or dict format first the main body and then the 9 to 15 solutions and there descriptive name.\n
                    example: "main body": "Here some descriptiona and humble text to help the person in stress",
                       "solutions": "1(only number value)":"description of solution 1 and also suggest subtasks for the task description.",
                                     "2":"description of solution 2 and also suggest subtasks for the task description.",
                                     "3":"description of solution 3 and also suggest subtasks for the task description.",
                                     "4":"description of solution 4 and also suggest subtasks for the task description.",
                                     "5":"description of solution 5 and also suggest subtasks for the task description.",
                                     "6":"description of solution 6 and also suggest subtasks for the task description.",
                                     "7":"description of solution 7 and also suggest subtasks for the task description.",
                                     "8":"description of solution 8 and also suggest subtasks for the task description.",
                                     "9":"description of solution 9 and also suggest subtasks for the task description.",
                                     "10":"description of solution 10 and also suggest subtasks for the task description."
                                     "11":"description of solution 11 and also suggest subtasks for the task description.",
                                     "12":"description of solution 12 and also suggest subtasks for the task description."
                                     "13":"description of solution 13 and also suggest subtasks for the task description.",
                                     "14":"description of solution 14 and also suggest subtasks for the task description.",
                                     "15":"description of solution 15 and also suggest subtasks for the task description."
            ->Make sure the solutions are actionable and easy to follow.\n
            ->Give subtasks as string with ";" as separator But dont forget to add key "Subtask:" in descriptions.  
            -> structure= "{"1":"title:decription.Subtasks:subtask_1;subtask2}"
            ->Dont suggest data in any other format except json or dict.\n
            ->output should start with json or dict only dont specify it that its json or dict format example '''json/dict dont do it.\n
            """
                ),
                HumanMessage(
                    content=f"""The stress level of patient={stress_level}.\n
                    Here are some input that describe patient well{patient_features}.\n
                    Use this features and give suggetions on this conditions.
                    Suggest the solutions to the patients on the given stress level only.\n
                    """
                )
            ]
        )

    # Initialize the chat model    
    llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.6,
    google_api_key=api_key
    )

    final_prompt=info_prompt.invoke({"stress_level":stress_level})

    response=llm.invoke(final_prompt)


    # Extract JSON content from the response 
    # starting index of json
    for i in range(len(response.content)):
        if response.content[i]=='{':
            keep_start=i
            break

    # ending index of json
    for i in range(len(response.content)):
        if response.content[i]=='}':
            keep_end=i+3
            break

    json_content=response.content[keep_start:keep_end]

    json_content=eval(json_content)

    parsing_info=json_content

    # Parse tasks into structured format with title and subtasks
    structured_tasks = parse_tasks(parsing_info['solutions'])

    collection.update_one({'_id':ObjectId(patient_data["_id"])},{'$set':{'tasks':structured_tasks}})

    return JSONResponse(status_code=200,content={"stress_level":stress_mapping[stress_level],
    "suggestions":structured_tasks})



        

@app.put("/profile/update/{mobile_no}")
def update_patient(mobile_no: str, updated_patient_data: Update_Patient):

    client = MongoClient("mongodb://localhost:27017/")
    db = client["stress_management_system"]
    collection = db["users"]

    updated_data = {k: v for k, v in updated_patient_data.model_dump().items() if v is not None}

    if not updated_data:
        return JSONResponse(status_code=400, content={"detail": "No update fields provided"})

    collection.update_one({'mobile_no':int(mobile_no)},{'$set':updated_data})

    return JSONResponse(status_code=200, content=updated_data)


@app.put("/profile/mobile_no/{mobile_no}")
def update_patient_mobile_no(mobile_no: str, mobile_update: MobileUpdate):
    client = MongoClient("mongodb://localhost:27017/")
    db = client["stress_management_system"]
    collection = db["users"]

    current_patient = collection.find_one({'mobile_no': int(mobile_no)})
    if not current_patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    existing_patient = collection.find_one({'mobile_no': int(mobile_update.mobile_no)})
    if existing_patient and existing_patient['_id'] != current_patient['_id']:
        raise HTTPException(status_code=400, detail="Mobile number already exists")

    collection.update_one({'mobile_no':int(mobile_no)},{'$set':{'mobile_no':mobile_update.mobile_no}})

    return JSONResponse(status_code=200, content={"detail":"Mobile number updated successfully","mobile_no":mobile_update.mobile_no})


@app.put("/profile/delete/{mobile_no}")
def delete_patient(mobile_no:int):

    client = MongoClient("mongodb://localhost:27017/")
    db = client["stress_management_system"]
    collection = db["users"]

    data=list(collection.find())
    for i in data:
        if i['mobile_no']==int(mobile_no):
            collection.delete_one({'mobile_no':int(mobile_no)})
            break

    return JSONResponse(status_code=200, content={"detail":"Patient deleted successfully"})

@app.post("/login")
def patient_login(credentials: dict):
    try:
        client = MongoClient("mongodb://localhost:27017/")
        db=client['stress_management_system']
        collection=db['users']

        if collection.find_one({'mobile_no':int(credentials['mobile_no']),'password':credentials['password']}):
            data=collection.find_one({'mobile_no':int(credentials['mobile_no']),'password':credentials['password']})

            data['_id']=str(data['_id'])
            data.pop('password')
            print(f"data: {data} type: {type(data)} ")
            return JSONResponse(status_code=200,content={'detail':"Login Sucessful",
                                                         'data':data})

        return JSONResponse(status_code=401,content={'detail':"Invalid Credentials"})
    
    except Exception as e:
        return JSONResponse(status_code=500,content={'detail':f"Internal Server Error: {e}"})


@app.get("/profile/{_id}")
def get_patient(_id:str=Path(...,description="Unique patient id",examples=["64b8f0f5e1b1c8b5f6d7e9a1"])):
    client = MongoClient("mongodb://localhost:27017/")
    db = client["stress_management_system"]
    collection = db["users"]
    obj_id = ObjectId(_id)
    data=collection.find_one({"_id":obj_id},{'Password':0})
    if not data:
        raise HTTPException(status_code=404,detail="Patient not found")

    data["_id"] = str(data["_id"])
    
    return JSONResponse(status_code=200, content=data)

@app.post("/get_all_tasks")
def get_all_tasks(id:str=Query(...,description="Unique patient id",examples=["64b8f0f5e1b1c8b5f6d7e9a1"])):
    client = MongoClient("mongodb://localhost:27017/")
    db = client["stress_management_system"]
    collection = db["users"]

    data =collection.find_one({'_id':ObjectId(id)})['tasks']
    if not data:
        raise HTTPException(status_code=404,detail="No tasks found")

    # data["_id"] = str(data["_id"])
    return data

    