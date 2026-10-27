import json
import requests
import streamlit as st
from openai import OpenAI
import os
from langchain.agents import create_agent

def get_weather_data(location: str = "Syracuse, NY") -> dict:
    """Finds the location and the current weather and returns the temperature,
    feels like, description, humidity, wind, low temperature, high temperature,
    chance of rain percentage, and chance of snow percentage"""

    if not location:
        location = "Syracuse"

    url = f'https://wttr.in/{location}?format=j1'
    response = requests.get(url, timeout=10)
    if response.status_code != 200:
        raise Exception(f'wttr.in error: status {response.status_code}')
    try:
        data = response.json()
    except ValueError:
        raise Exception(f'Could not find a location named {location}')

    current = data['current_condition'][0]
    today = data['weather'][0]

    max_rain_chance = max(int(hour['chanceofrain']) for hour in today['hourly'])

    return {
        'location': location,
        'temperature': float(current['temp_F']),
        'feels_like': float(current['FeelsLikeF']),
        'description': current['weatherDesc'][0]['value'].strip(),
        'humidity': int(current['humidity']),
        'wind_mph': float(current['windspeedMiles']),
        'high_today_f': float(today['maxtempF']),
        'low_today_f': float(today['mintempF']),
        'chance_of_rain_pct': max_rain_chance,
        'chance_of_snow_pct': max(int(h['chanceofsnow']) for h in today['hourly']),
    }

st.title("Lab 6 What to Wear Bot With LangChain")
st.write("Input a city and the bot will tell you what to wear today")

#openai_api_key = st.secrets["OPEN_AI_KEY"]
os.environ["OPENAI_API_KEY"] = st.secrets["OPEN_AI_KEY"]
#client = OpenAI(api_key=openai_api_key)

city = st.sidebar.text_input("Enter city")

agent = create_agent(
    model= "openai:gpt-5-mini" ,
    tools=[get_weather_data],
    system_prompt= "You are a helpful assistant that gives clothing and outdoor "
                    "activity recommendations based on current weather conditions. "
                    "Consider temperature, feels-like temperature, wind, humidity, "
                    "UV index, and chance of rain/snow when making suggestions."
)

if city:
    with st.chat_message("user"):
        st.write(f"What should I wear in {city}?")

    with st.chat_message("assistant"):
        with st.spinner("Checking the weather..."):
            result = agent.invoke(
                {"messages": [{"role": "user", "content": f"What should I wear in {city}?"}]}
            )
        answer = result["messages"][-1].content
        st.write(answer)
