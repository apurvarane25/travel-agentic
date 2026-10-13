from langchain_core.tools import tool
import tools
import requests


def get_coordinates(city: str) -> tuple:
    """Get latitude and longitude for a city"""
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
    response = requests.get(url).json()

    if response['results']:
        result = response['results'][0]
        return result['latitude'], result['longitude']
    else:
        raise ValueError(f"City '{city}' not found")

@tool
def get_weather(city: str, start_date: str, end_date: str) -> str:
    """Get the weather info of the input date"""
    lat, lon = get_coordinates(city)

    if not end_date:
        end_date = start_date

    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&start_date={start_date}&end_date={end_date}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto"
    

    try:
        response = requests.get(url, timeout=10).json()
        data = response['daily']

        results = []
        for i, date in enumerate(data['time']):
            results.append(f"{date}: High {data['temperature_2m_max'][i]}°C, Low {data['temperature_2m_min'][i]}°C, Rain {data['precipitation_sum'][i]}mm")
    
        return "\n".join(results)
    except Exception as e:
        return f"Error fetching weather: {str(e)}"

@tool
def get_attractions(city: str, weather: str) -> str:
    """Get atrractions in the mentioned city based on the weather"""
    try:
        url = f"https://en.wikipedia.org/w/api.php?action=query&titles={city}&prop=extracts&explaintext=True&format=json"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        pages = data['query']['pages']
        page_content = list(pages.values())[0].get('extract', '')

        attractions_section = re.search(
            r'(?: Attractions|Tourist attractions|Point of interest)(.*?)(?=\n==\Z)',
            page_content,
            re.IGNORECASE | re.DOTALL
        )   

        print(f"Attractions in {city} are: {attractions_section}")

        if not attractions_section:
            return f"No attractions found for city{city}"

        attractions = re.findall(r'[•\-\*]\s*([^•\-\*\n]+)', attractions_section.group(1))
        attractions = [a.strip() for a in attractions if a.strip() and len(a.strip()) > 3][:10]
    
        is_rainy = "rain" in weather.lower()
        emoji = "🌧️" if is_rainy else "☀️"

        return f"{emoji} {', '.join(attractions)}"

    except Exception as e:
        return f"Error fetching attractions: {str(e)}"
