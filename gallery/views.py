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
        api_key = getattr(settings, 'PEXELS_API_KEY', "a9xrBjC2MDMndwcn2Sxr07Ix0v0xsEuGtREkIUd0GHXorrHYRP0kCBTa")

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


def ai_studio(request):
    prompt = ""
    generated_image_data = None
    error_message = None

    if request.method == "POST":
        prompt = (request.POST.get("prompt") or "").strip()
        api_key = getattr(settings, "GEMINI_API_KEY", "AIzaSyBsIsLZ_zOwDVfhBqZzslVAYJT0TDfvyEw")

        if not prompt:
            error_message = "Please enter a prompt."
        elif not api_key:
            error_message = "Gemini API key not configured in environment."
        else:
            base_url = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash-latest:generateContent"
            url = f"{base_url}?key={api_key}"

            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "response_mime_type": "image/png"
                }
            }

            try:
                resp = requests.post(url, json=payload, timeout=90)

                if resp.status_code == 200:
                    data = resp.json()
                    try:
                        b64 = data["candidates"][0]["content"]["parts"][0]["inline_data"]["data"]
                        generated_image_data = f"data:image/png;base64,{b64}"
                    except Exception:
                        error_message = "Gemini responded but no image was found. Try another prompt."
                else:
                    error_message = f"Gemini error {resp.status_code}: {resp.text}"

            except Exception as e:
                error_message = f"Error talking to Gemini: {str(e)}"

    return render(request, "gallery/ai_studio.html", {
        "prompt": prompt,
        "generated_image_data": generated_image_data,
        "error_message": error_message,
    })
