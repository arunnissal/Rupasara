from django.shortcuts import render
from django.conf import settings
import requests
import base64


def home(request):
    return render(request, 'gallery/home.html')


def search_images(request):
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
            error_message = "Pexels API key not configured. Please add it in settings.py."
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
    return render(request, 'gallery/favorites.html')


def _generate_with_stability(prompt: str):
    """
    Call Stability AI image API.
    Returns (image_data_uri, error_message).
    """
    api_key = getattr(settings, "STABILITY_API_KEY", None)
    if not api_key:
        return None, "Stability AI key not configured. Add STABILITY_API_KEY in settings."

    # Example demo endpoint – adjust if Stability docs suggest a different free endpoint
    url = "https://api.stability.ai/v2beta/demo/generate/stable-diffusion-xl"

    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    files = {
        "prompt": (None, prompt),
        "output_format": (None, "png"),
    }

    try:
        resp = requests.post(url, headers=headers, files=files, timeout=60)

        if resp.status_code == 200:
            import base64
            b64 = base64.b64encode(resp.content).decode("utf-8")
            return f"data:image/png;base64,{b64}", None

        # Special handling for quota/credits issues
        if resp.status_code == 402:
            return None, "Stability AI: payment/credits required (status 402). Free quota may be exhausted."

        # Try parse JSON error if any
        try:
            data = resp.json()
            detail = data.get("message") or data.get("error") or ""
        except Exception:
            detail = ""

        return None, f"Stability AI error (status {resp.status_code}). {detail}".strip()

    except requests.RequestException:
        return None, "Unable to reach Stability AI. Please try again."


def _generate_with_flux(prompt: str):
    api_key = getattr(settings, "FLUX_API_KEY", "866e8146-3720-40bb-b95d-a4b4f8e97d0b")
    api_url = getattr(settings, "FLUX_API_URL", "https://api.bfl.ml/v1/image")

    if not api_url:
        return None, "FLUX API URL not configured. Set FLUX_API_URL in settings/environment."

    if not api_key:
        return None, "FLUX API key not configured. Set FLUX_API_KEY in settings/environment."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    body = {
        "prompt": prompt,
        # "model": "flux-schnell",   # or whatever model id docs say
        # other params from docs…
    }

    try:
        resp = requests.post(api_url, headers=headers, json=body, timeout=60)

        if resp.status_code == 200:
            import base64
            try:
                # case 1: raw bytes
                b64 = base64.b64encode(resp.content).decode("utf-8")
                return f"data:image/png;base64,{b64}", None
            except Exception:
                pass

            try:
                # case 2: JSON with base64 field
                data = resp.json()
                b64 = (
                    data.get("image_base64")
                    or data.get("image")
                    or data.get("data")
                )
                if b64:
                    return f"data:image/png;base64,{b64}", None
            except Exception:
                pass

            return None, "FLUX API returned success but response format is not handled. Adjust parsing in _generate_with_flux()."

        try:
            data = resp.json()
            detail = data.get("message") or data.get("error") or ""
        except Exception:
            detail = ""

        return None, f"FLUX API error (status {resp.status_code}). {detail}".strip()

    except requests.RequestException:
        return None, "Unable to reach FLUX image service. Please try again."

def ai_studio(request):
    """
    AI Studio page.
    - GET: show prompt form
    - POST: send prompt to selected provider and display result
    """
    generated_image_data = None
    error_message = None
    prompt = ""
    provider = "stability"  # default tab
    style = ""              # optional future use

    if request.method == "POST":
        prompt = (request.POST.get("prompt") or "").strip()
        provider = request.POST.get("provider") or "stability"
        style = (request.POST.get("style") or "").strip()

        if not prompt:
            error_message = "Please enter a prompt."
        else:
            # Optionally combine style text into prompt:
            # if style and style.lower() not in prompt.lower():
            #     prompt = f"{prompt}, {style}"

            if provider == "flux":
                generated_image_data, error_message = _generate_with_flux(prompt)
            else:
                provider = "stability"  # normalize
                generated_image_data, error_message = _generate_with_stability(prompt)

    context = {
        "prompt": prompt,
        "generated_image_data": generated_image_data,
        "error_message": error_message,
        "provider": provider,
        "style": style,
    }
    return render(request, "gallery/ai_studio.html", context)
