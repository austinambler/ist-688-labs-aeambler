import asyncio, os, time
import streamlit as st
import requests
from agents import Agent, Runner, function_tool

def get_current_weather(location=None):

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


@function_tool
def get_weather(location: str = "Syracuse, NY") -> dict:
    """This tool gets the weather and returns the location, temperature, feels_like, description,
    humidity, wind, high today, low today, chance of rain percentage, and chance of snow percentage"""
    return get_current_weather(location) 


os.environ["OPENAI_API_KEY"] = st.secrets["OPEN_AI_KEY"]
MODEL = "gpt-5-mini"

weather_agent = Agent(
    name="Weather agent",
    instructions=(
        "You are a weather reporter. Always call the get_weather tool for the "
        "location the user asks about (default to Syracuse, NY if none is given). "
        "Then summarize the facts clearly and concisely: location, current temperature "
        "and feels-like, conditions, humidity, wind, today's high and low, and the "
        "chance of rain and snow. Report only the facts. Do not give advice, "
        "clothing suggestions, or activity suggestions. If the tool returns an "
        "error, say the weather could not be retrieved and why."
    ),
    tools=[get_weather],
    model=MODEL,
)

stylist_agent = Agent(
    name="Stylist agent",
    instructions=(
        "You are a practical personal stylist. You will be given a weather report. "
        "Recommend what to wear based only on that report: layers, outerwear, "
        "footwear, and accessories (umbrella, hat, gloves, sunglasses, etc.). "
        "Account for the feels-like temperature, wind, and rain/snow chances. "
        "Keep it to a short, concrete list with a one-line reason for each item. "
        "Do not invent weather details that aren't in the report."
    ),
    model=MODEL,
)

activity_agent = Agent(
    name="Activity agent",
    instructions=(
        "You are a local activity planner. You will be given a weather report. "
        "Suggest 3-5 activities that suit the conditions, mixing outdoor and indoor "
        "options where it makes sense. If the weather is poor for outdoor plans, "
        "say so and lean toward indoor ideas. Include a best time of day when the "
        "report supports it. Keep each suggestion to one or two sentences. "
        "Do not invent weather details that aren't in the report."
    ),
    model=MODEL,
)


manager_agent = Agent(
    name="Manager",
    instructions=(
        "You coordinate a team of specialist tools to answer the user's question "
        "about their day. Follow this order:\n"
        "1. First, call weather_report with the user's location to get the weather facts.\n"
        "2. Then call outfit_recommendation and activity_recommendation, passing the "
        "full weather report text as the input to each (they cannot see it otherwise).\n"
        "3. Combine the results into one friendly answer with three short sections: "
        "Weather, What to wear, and What to do.\n"
        "Do not make up facts, and do not skip the weather step. If the weather "
        "report fails, tell the user and stop instead of guessing."
    ),
    tools=[
        weather_agent.as_tool(
            tool_name="weather_report",
            tool_description=(
                "Gets the current weather and today's forecast for a location and "
                "returns a factual summary. Input: a location name, e.g. 'Syracuse, NY'."
            ),
        ),
        stylist_agent.as_tool(
            tool_name="outfit_recommendation",
            tool_description=(
                "Recommends what to wear. Input: the full weather report text "
                "from weather_report."
            ),
        ),
        activity_agent.as_tool(
            tool_name="activity_recommendation",
            tool_description=(
                "Suggests activities suited to the weather. Input: the full weather "
                "report text from weather_report."
            ),
        ),
    ],
    model=MODEL,
)


@st.cache_resource
def get_event_loop():
    return asyncio.new_event_loop()

def run(agent, prompt):
    start = time.perf_counter()
    result = get_event_loop().run_until_complete(Runner.run(agent, prompt))
    return result, time.perf_counter() - start

city = st.sidebar.text_input("Enter city")

if st.sidebar.button("Get Advice"):
    location = city.strip() if city else "Syracuse, NY"

    with st.chat_message("assistant"):
        with st.spinner("Checking the weather and thinking..."):
            try:
                result = asyncio.run(
                    Runner.run(
                        manager_agent,
                        f"What should I wear and do today in {location}?",
                    )
                )
                st.write(result.final_output)
            except Exception as e:
                st.error(str(e))