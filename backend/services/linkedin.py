from config.settings import settings
import requests


def scrape_linkedin_profiles(search_keywords: str, max_profiles: int = 5):

    print("🔍 Searching via SerpAPI:", search_keywords)
    print("🔑 SERP KEY:", settings.serp_api_key)

    query = f'site:linkedin.com/in "{search_keywords}" -jobs -hiring'

    url = "https://serpapi.com/search"

    params = {
        "q": query,
        "api_key": settings.serp_api_key,
        "num": max_profiles
    }

    response = requests.get(url, params=params)
    data = response.json()

    profiles = []

    for result in data.get("organic_results", []):
        print("👉 Result:", result)

        profiles.append({
            "name": result.get("title", "Unknown"),
            "linkedin_url": result.get("link", ""),
            "current_title": result.get("snippet", ""),
            "location": "",
            "summary": result.get("snippet", ""),
            "experience": [],
            "education": [],
            "skills": [],
        })

    return profiles