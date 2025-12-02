from django.shortcuts import render
from django.conf import settings
import requests


def home(request):
    """
    Home page view.
    Shows the brand and a search bar.
    """
    return render(request, 'gallery/home.html')


def search_images(request):
    """
    Search results page with pagination using Pexels API.
    """
    query = request.GET.get('q', '').strip()

    try:
        page = int(request.GET.get('page', '1'))
        if page < 1:
            page = 1
    except ValueError:
        page = 1

    PER_PAGE = 24

    images = []
    error_message = None
    has_next = False

    if query:
        api_key = getattr(settings, 'PEXELS_API_KEY', None)

        if not api_key:
            error_message = "Pexels API key not configured. Please add it in settings.py or environment."
        else:
            url = "https://api.pexels.com/v1/search"
            params = {
                "query": query,
                "per_page": PER_PAGE,
                "page": page,
            }
            headers = {
                "Authorization": api_key
            }

            try:
                response = requests.get(url, headers=headers, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    photos = data.get("photos", [])

                    for photo in photos:
                        src = photo.get("src", {})
                        images.append({
                            "thumb_url": src.get("medium") or src.get("small"),
                            "full_url": src.get("original") or src.get("large"),
                            "photographer": photo.get("photographer"),
                            "photographer_url": photo.get("photographer_url"),
                            "page_url": photo.get("url"),
                        })

                    if len(photos) == PER_PAGE:
                        has_next = True
                else:
                    error_message = f"Pexels API error (status {response.status_code})."
            except requests.RequestException:
                error_message = "Unable to connect to Pexels API. Please try again later."

    context = {
        "query": query,
        "images": images,
        "error_message": error_message,
        "page": page,
        "has_next": has_next,
        "has_prev": page > 1,
        "next_page": page + 1,
        "prev_page": page - 1,
    }
    return render(request, 'gallery/results.html', context)


def favorites(request):
    """
    Favorites page – images are managed completely in localStorage.
    Backend only serves the template.
    """
    return render(request, 'gallery/favorites.html')
