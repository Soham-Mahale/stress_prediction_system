from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage,AIMessage,SystemMessage


import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

stress_level=2
features={"anxiety_level":5,
        "carrer_tension":9,
        "bulling":2,
        "self_esteem":5,
        "confidence":3
          }

info_prompt=ChatPromptTemplate(
[
        SystemMessage
        (
            content=
            f"""->You are an helpful and empathetic mental wellness assistance.\n
            ->Your goal is to provide supportive, actionable advice based on a person's stress level.\n
            ->There are 3 progessive stress levels:
                1 = Small or Minor stress caused by burnout, fatigue, etc.(No need of doctor consultance).\n
                2 = Medium or Mediocar level stress(recommend going for doctor consultance).\n
                3 = Sever and Large level stress(Strongly recommend doctor consultance).\n
            ->On this stress level you have to give soltuions such as mental exercises, breathing exercises etc.To help and support the person in stress and to remove his/her stress.Dont forget to recommend the doctor consultancy when required.\n
            ->Provide suggestion in clear, number list on given stress level only.Keep your tone warm and encouraging.\n
            """
        ),
        HumanMessage(
            content=f"""The stress level of patient={stress_level}.\n
            Here are some input that describe patient well{features}.\n
            Use this features and give suggetions on this conditions.
            Suggest the solutions to the patients on the given stress level only.\n
            """
        )
    ]
)


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.6,
    google_api_key=api_key
)

final_prompt=info_prompt.invoke({"stress_level":stress_level})

# print(final_prompt)

response=llm.invoke(final_prompt)

print(response.content)




