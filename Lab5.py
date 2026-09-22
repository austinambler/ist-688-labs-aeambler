import json
import requests
import streamlit as st
from openai import OpenAI


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
    max_snow_chance = max(int(hour['chanceofsnow']) for hour in today['hourly'])

    return {
        'location': location,
        'temperature': float(current['temp_F']),
        'feels_like': float(current['FeelsLikeF']),
        'description': current['weatherDesc'][0]['value'].strip(),
        'humidity': int(current['humidity']),
        'wind_mph': float(current['windspeedMiles']),
        'uv_index': int(current['uvIndex']),
        'high_today_f': float(today['maxtempF']),
        'low_today_f': float(today['mintempF']),
        'chance_of_rain_pct': max_rain_chance,
        'chance_of_snow_pct': max_snow_chance,
    }


st.title("Lab 5 What to Wear Bot")
st.write("Enter a city in the sidebar and press Enter to get today's recommendations")

openai_api_key = st.secrets["OPEN_AI_KEY"]
client = OpenAI(api_key=openai_api_key)

city = st.sidebar.text_input("Enter city")

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather and today's forecast for a given city",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city name, e.g. 'Paris' or 'New York'. Defaults to Syracuse if not provided."
                    }
                },
                "required": []
            }
        }
    }
]

display_city = city if city else "Syracuse (default)"

messages = [
    {
        "role": "system",
        "content": (
            "You are a helpful assistant that gives clothing and outdoor "
            "activity recommendations based on current weather conditions. "
            "Consider temperature, feels-like temperature, wind, humidity, "
            "UV index, and chance of rain/snow when making suggestions."
        )
    },
    {
        "role": "user",
        "content": (
            f"What should I wear in {city if city else 'Syracuse'} today, "
            "and what are some good outdoor activities for this weather?"
        )
    }
]

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages,
    tools=tools,
    tool_choice="auto"
)

response_message = response.choices[0].message
messages.append(response_message.to_dict())

tool_calls = response_message.tool_calls

if tool_calls:
    tool_call_id = tool_calls[0].id
    tool_function_name = tool_calls[0].function.name
    tool_args = json.loads(tool_calls[0].function.arguments)

    if tool_function_name == "get_current_weather":
        try:
            results = get_current_weather(tool_args.get('location'))

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "name": tool_function_name,
                "content": json.dumps(results)
            })

            final_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )

            st.subheader(f"Weather in {display_city}")
            st.write(f"**{results['temperature']}°F** (feels like {results['feels_like']}°F), "
                     f"{results['description']}")
            st.write(f"High: {results['high_today_f']}°F / Low: {results['low_today_f']}°F  "
                     f"| Rain chance: {results['chance_of_rain_pct']}% "
                     f"| Wind: {results['wind_mph']} mph")

            st.subheader("Recommendations")
            st.write(final_response.choices[0].message.content)

        except Exception as e:
            st.error(str(e))
else:
    st.write(response_message.content)