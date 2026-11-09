"""Herramientas web: consulta del clima y búsquedas en Google."""
import json
import urllib.parse
import urllib.request
import webbrowser

WEATHER_CODES = {
    0: "despejado",
    1: "mayormente despejado",
    2: "parcialmente nublado",
    3: "nublado",
    45: "niebla",
    48: "niebla con escarcha",
    51: "llovizna ligera",
    53: "llovizna moderada",
    55: "llovizna densa",
    61: "lluvia leve",
    63: "lluvia moderada",
    65: "lluvia fuerte",
    71: "nevada ligera",
    73: "nevada moderada",
    75: "nevada intensa",
    80: "chubascos leves",
    81: "chubascos moderados",
    82: "chubascos violentos",
    95: "tormenta eléctrica",
}

def get_weather(city: str) -> str:
    """Obtiene el clima actual de una ciudad sin requerir claves de API (Open-Meteo).
    
    Args:
        city: Nombre de la ciudad o localidad (ej. 'Madrid', 'Bogota', 'Buenos Aires', 'Lima').
    """
    try:
        # 1. Geocodificación: obtener latitud y longitud
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1&language=es&format=json"
        req = urllib.request.Request(geo_url, headers={"User-Agent": "HadaAssistant/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            geo_data = json.loads(response.read().decode())

        if not geo_data.get("results"):
            return f"No se encontró la ubicación '{city}'."

        result = geo_data["results"][0]
        lat = result["latitude"]
        lon = result["longitude"]
        city_name = result.get("name", city)
        country = result.get("country", "")

        # 2. Obtener pronóstico actual
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m"
        )
        req_weather = urllib.request.Request(weather_url, headers={"User-Agent": "HadaAssistant/1.0"})
        with urllib.request.urlopen(req_weather, timeout=5) as response:
            w_data = json.loads(response.read().decode())

        curr = w_data.get("current", {})
        temp = curr.get("temperature_2m")
        feels_like = curr.get("apparent_temperature")
        humidity = curr.get("relative_humidity_2m")
        wind = curr.get("wind_speed_10m")
        code = curr.get("weather_code", 0)
        desc = WEATHER_CODES.get(code, "tiempo variable")

        return (
            f"Clima en {city_name} ({country}): {temp}°C (sensación de {feels_like}°C), "
            f"cielo {desc}. Humedad del {humidity}% y viento a {wind} km/h."
        )
    except Exception as e:
        return f"Error al consultar el clima para '{city}': {e}"

def search_google(query: str) -> str:
    """Abre el navegador web predeterminado y busca una consulta en Google.
    
    Args:
        query: Lo que el usuario quiere buscar en la web.
    """
    try:
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        webbrowser.open(url)
        return f"He abierto la búsqueda en Google para '{query}'."
    except Exception as e:
        return f"Error al abrir la búsqueda: {e}"

