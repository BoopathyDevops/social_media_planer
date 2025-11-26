from groq import Groq
from dotenv import load_dotenv
import os
import json
import requests
import re
from datetime import datetime

load_dotenv()

def get_brand_from_wikipedia(brand_name):
    headers = {'User-Agent': 'ContentPlannerApp/1.0 (contact@example.com)'}
    try:
        search_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query", "list": "search", "srsearch": brand_name + " company",
            "format": "json", "srlimit": 1
        }
        resp = requests.get(search_url, params=params, headers=headers, timeout=5)
        search_data = resp.json()
        results = search_data.get("query", {}).get("search", [])
        
        if results:
            page_title = results[0]["title"]
            summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{page_title.replace(' ', '_')}"
            sum_resp = requests.get(summary_url, headers=headers, timeout=5)
            sum_data = sum_resp.json()
            desc = sum_data.get('description', '').lower()
            if any(x in desc for x in ['company', 'brand', 'corporation', 'manufacturer', 'retailer', 'service']):
                return {
                    'found': True,
                    'industry': sum_data.get('description', 'N/A'),
                    'description': sum_data.get('extract', ''),
                    'brand_name': brand_name
                }
        return None
    except Exception as e:
        print(f"Wikipedia API Note: {e}")
        return None

class GroqSocialMediaPlanner:
    def __init__(self):
        self.api_key = os.getenv('GROQ_API_KEY')
        if not self.api_key:
            self.groq_available = False
            return

        try:
            self.client = Groq(api_key=self.api_key)
            self.model = "llama-3.3-70b-versatile"
            self.groq_available = True
        except Exception:
            self.groq_available = False

        self.platforms = {
            'instagram': {'limit': 2200, 'tags': 30},
            'twitter': {'limit': 280, 'tags': 3},
            'linkedin': {'limit': 3000, 'tags': 5},
            'facebook': {'limit': 63000, 'tags': 5}
        }

        # Explicit Themes for Progression
        self.weekly_themes = {
            1: "Brand Awareness & Introduction",
            2: "Education & Value Proposition",
            3: "Social Proof & Community Building",
            4: "Conversion & Sales Promotion"
        }

    def generate_content_with_groq(self, prompt):
        if not self.groq_available: return ""
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a creative social media strategist. Output strictly valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.6,
                response_format={"type": "json_object"}
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            try:
                chat_completion = self.client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=self.model,
                    temperature=0.6
                )
                return chat_completion.choices[0].message.content
            except Exception as e2:
                print(f"Generation Fatal Error: {e2}")
                return ""

    def create_content_plan(self, brand, industry, goals, audience, weeks, platforms, brand_info=None):
        print(f"🤖 Llama 3.3 generating {weeks}-week plan for {brand}...")
        
        content_plan = {
            'brand': brand,
            'timestamp': datetime.now().isoformat(),
            'weekly_content': [],
            'color_palette': self.generate_color_palette(brand, industry)
        }

        # Memory buffer to avoid repetition
        all_previous_ideas = []

        for week in range(1, weeks + 1):
            week_data = self.generate_weekly_content(
                brand, industry, goals, audience, week, platforms, 
                brand_info, all_previous_ideas
            )
            
            all_previous_ideas.extend(week_data['post_ideas'])
            content_plan['weekly_content'].append(week_data)

        self.save_content_plan(content_plan)
        return content_plan

    def generate_weekly_content(self, brand, industry, goals, audience, week, platforms, brand_info, previous_ideas):
        brand_desc = brand_info.get('description', '') if brand_info else ''
        
        # Determine Theme
        theme_name = self.weekly_themes.get(week, f"Strategic Focus Week {week}")
        
        # History Context
        history_context = ""
        if previous_ideas:
            history_str = "; ".join(previous_ideas[-15:])
            history_context = f"AVOID repeating these recent topics: {history_str}"

        ideas_prompt = f"""
        Context: {brand_desc}
        Brand: {brand} ({industry})
        Goals: {goals}
        Audience: {audience}
        
        CURRENT WEEK: Week {week}
        WEEKLY THEME: {theme_name}
        
        Constraint: {history_context}

        Generate a JSON object with a list of 7 UNIQUE post ideas specifically for "Week {week}: {theme_name}".
        Format: {{ "ideas": ["Idea 1", "Idea 2", "Idea 3", "Idea 4", "Idea 5", "Idea 6", "Idea 7"] }}
        """
        
        raw_response = self.generate_content_with_groq(ideas_prompt)
        parsed_data = self.extract_json_object(raw_response)
        ideas_list = parsed_data.get("ideas", [])
        
        if not ideas_list:
            ideas_list = [f"{theme_name} - Topic {i}" for i in range(1, 8)]

        # Generate Platform Content
        platform_content = {}
        for platform in platforms:
            platform_content[platform] = self.generate_platform_posts(
                ideas_list, brand, platform, goals, audience, week
            )

        return {
            'week': week,
            'theme': f"Week {week}: {theme_name}", # Explicit formatting for UI
            'theme_description': f"Focusing on {theme_name.lower()} to achieve {goals[:30]}...",
            'post_ideas': ideas_list,
            'platform_content': platform_content
        }

    def generate_platform_posts(self, ideas, brand, platform, goals, audience, week):
        posts = []
        
        for i, idea in enumerate(ideas[:7], 1):
            prompt = f"""
            Create a {platform} post for {brand}.
            Week: {week}
            Topic: {idea}
            Goal: {goals}
            
            Return strictly valid JSON with these keys:
            {{
                "hook": "First sentence",
                "body": "Main content",
                "cta": "Call to action",
                "hashtags": "string of hashtags",
                "visual_description": "Image description",
                "post_type": "Image/Video/Carousel"
            }}
            """
            
            response = self.generate_content_with_groq(prompt)
            data = self.extract_json_object(response)
            
            full_text = f"{data.get('hook', '')}\n\n{data.get('body', '')}\n\n👇 {data.get('cta', '')}\n\n{data.get('hashtags', '')}"
            
            posts.append({
                'day': i,
                'idea': idea,
                'visual_description': data.get('visual_description', 'Brand visual'),
                'full_post_text': full_text,
                'hook': data.get('hook', ''),
                'caption': data.get('body', ''),
                'hashtags': data.get('hashtags', ''),
                'post_type': data.get('post_type', 'Post')
            })
            
        return posts

    def generate_color_palette(self, brand, industry):
        prompt = f"""
        Generate 5 brand colors for {brand}.
        Return JSON: {{ "palette": [ {{"color": "#hex", "name": "Name", "meaning": "Meaning"}} ] }}
        """
        response = self.generate_content_with_groq(prompt)
        data = self.extract_json_object(response)
        return data.get("palette", [])

    def extract_json_object(self, text):
        if not text: return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        try:
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
            if match: return json.loads(match.group(1))
            
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1: return json.loads(text[start:end+1])
        except Exception:
            pass
        return {
            "hook": "Content Generated", 
            "body": text[:200] if text else "Error parsing content",
            "cta": "Link in bio", 
            "hashtags": "#" + str(datetime.now().year),
            "visual_description": "Standard Brand Image",
            "ideas": ["Idea 1", "Idea 2", "Idea 3", "Idea 4", "Idea 5", "Idea 6", "Idea 7"]
        }

    def save_content_plan(self, plan):
        filename = f"content_plan_{normalize_brand_key(plan['brand'])}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(plan, f, indent=2, ensure_ascii=False)
            print(f"💾 Content plan saved to {filename}")
        except Exception as e:
            print(f"Could not save file: {e}")

def normalize_brand_key(s):
    return ''.join(c for c in s.lower() if c.isalnum())

def main():
    print("Run app.py instead.")

if __name__ == "__main__":
    main()