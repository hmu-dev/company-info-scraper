import json
import logging
import os

from scrapegraphai.graphs import SmartScraperGraph

logging.basicConfig(
    filename="scrape_test.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Load OPENAI_API_KEY from environment
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")
if not os.environ["OPENAI_API_KEY"]:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

graph_config = {
    "llm": {
        "api_key": os.environ["OPENAI_API_KEY"],
        "model": "gpt-3.5-turbo",
    },
}


def batch_scrape(urls, prompt, config):
    results = []
    for url in urls:
        try:
            scraper = SmartScraperGraph(prompt=prompt, source=url, config=config)
            result = scraper.run()
            if result is None:
                raise ValueError("Scraper returned None")
            # Basic validation
            profile = result.get("profile", {})
            media = result.get("media", [])
            has_profile = isinstance(profile, dict) and all(
                key in profile
                for key in [
                    "About Us (including locations)",
                    "Our Culture",
                    "Our Team",
                    "Noteworthy & Differentiated",
                ]
            )
            has_media = isinstance(media, list) and len(media) > 0
            media_valid = (
                all("url" in m and "type" in m for m in media) if has_media else True
            )
            error = None
            if not has_profile:
                error = "Incomplete profile"
            if not media_valid:
                error = (error + " " if error else "") + "Invalid media format"
            logging.info(
                f"URL: {url} - Profile OK: {has_profile} - Media OK: {has_media and media_valid} - Error: {error}"
            )
            results.append({"url": url, "result": result, "error": error})
        except Exception as e:
            logging.error(f"URL: {url} - Error: {str(e)}")
            results.append(
                {"url": url, "result": {"profile": {}, "media": []}, "error": str(e)}
            )  # Graceful failure with empty result
    return results


def test_prompts(urls, prompts, config, batch_size=20):
    comparisons = {}
    for prompt_name, prompt in prompts.items():
        batch_urls = urls[:batch_size]
        results = batch_scrape(batch_urls, prompt, config)
        success_count = sum(1 for r in results if r["error"] is None)
        avg_media = sum(
            len(r["result"].get("media", [])) for r in results if r["result"]
        ) / len(results)
        comparisons[prompt_name] = {
            "success_rate": success_count / batch_size,
            "avg_media_count": avg_media,
            "errors": [r["error"] for r in results if r["error"]],
            "results": results,
        }
        logging.info(
            f"Tested {prompt_name} - Success Rate: {success_count / batch_size:.2f} - Avg Media: {avg_media:.2f}"
        )
    return comparisons


if __name__ == "__main__":
    with open("test_urls.json", "r") as f:
        all_urls = json.load(f)

    # Use default prompt from ai_scrapper.py
    default_prompt = """Please extract information from the provided website to create a company profile. Organize the extracted content into the following four distinct sections, ensuring each section is clearly delineated and contains relevant details: About Us (including locations): This section should provide a concise overview of the company, its mission, and its primary activities. Crucially, identify and list all physical locations associated with the company. Our Culture: Describe the core values, working environment, and overall ethos of the company. Look for descriptions of how the company operates, its philosophy, and what it emphasizes in its internal and external interactions. Our Team: Identify key individuals, leadership, or significant roles within the company. If specific team members are highlighted, include their names and relevant contributions or backgrounds. Noteworthy & Differentiated: This section is for unique selling propositions, special features, awards, or any aspects that make the company stand out from its competitors. Look for innovative services, unique offerings, or distinctive operational models. For each section, aim for clear, descriptive language. The overall profile should be comprehensive yet concise, suitable for a mobile app experience. Pay close attention to details that highlight the company's identity and what makes it unique. Keep the response less than 500 words. Additionally, extract any media (videos and images) that are relevant to company branding (i.e. logos, and media about the company). These images will be used to populate an about-us section for the given company in a recruiting app. Respond in strict JSON format with two main keys: 'profile' (an object with the four sections as keys, each containing a string description) and 'media' (an array of objects, each with 'url' and 'type' ('image' or 'video'))."""

    prompts = {
        "Prompt1": """Output ONLY valid JSON. Do not include any additional text, explanations, or wrappers. Ensure the JSON is parseable without errors. """
        + default_prompt,
        "Prompt2": default_prompt
        + """ Example output: {'profile': {'About Us (including locations)': 'Description...', 'Our Culture': 'Description...', 'Our Team': 'Description...', 'Noteworthy & Differentiated': 'Description...'}, 'media': [{'url': 'http://example.com/logo.png', 'type': 'image'}]}. Follow this structure exactly.""",
        "Prompt3": default_prompt
        + """ If a section or media is unavailable, use 'Not available' for strings or empty array for media. Ensure all four profile keys are always present.""",
    }

    results = test_prompts(all_urls, prompts, graph_config)

    with open("prompt_comparison.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    print("Prompt testing complete. Comparison saved to prompt_comparison.json")
    logging.info("Prompt test completed")
