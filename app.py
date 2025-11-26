import streamlit as st
from main import GroqSocialMediaPlanner, get_brand_from_wikipedia

def main():
    st.set_page_config(page_title="Llama Content Planner", page_icon="🤖", layout="wide")
    
    st.title("🤖 Social Media Content Planner (Llama 3.3)")
    st.write("Generate full, copy-paste ready social media content with specific weekly themes.")

    with st.sidebar:
        st.header("Campaign Settings")
        brand = st.text_input("🏢 Brand name")
        industry = st.text_input("🏭 Industry (e.g., Tech, Fashion)")
        goals = st.text_area("🎯 Campaign goals", height=100)
        audience = st.text_input("👥 Target audience")
        weeks = st.slider("📅 Number of weeks", 1, 4, 2)
        platforms = st.multiselect(
            "📱 Platforms",
            ["instagram", "twitter", "linkedin", "facebook"],
            default=["instagram", "twitter"]
        )
        generate_btn = st.button("Generate Content Plan", type="primary")

    if generate_btn:
        if not brand:
            st.warning("Please enter a brand name.")
            return

        planner = GroqSocialMediaPlanner()
        if not getattr(planner, "groq_available", True):
            st.error("❌ Groq AI not available. Please check your API key.")
            return

        st.info("🔄 Generating unique content plan... This may take a few minutes.")
        
        # 1. Fetch Context
        wiki_info = get_brand_from_wikipedia(brand)
        brand_info = wiki_info if wiki_info else None
        
        # 2. Generate Plan
        content_plan = planner.create_content_plan(
            brand=brand,
            industry=industry or (wiki_info['industry'] if wiki_info else "General"),
            goals=goals,
            audience=audience,
            weeks=weeks,
            platforms=platforms,
            brand_info=brand_info
        )

        st.success("✅ Content plan generated successfully!")
        st.divider()

        # 3. Display Content
        st.header(f"📱 CONTENT STRATEGY: {brand.upper()}")

        # --- Color Palette ---
        if "color_palette" in content_plan and content_plan["color_palette"]:
            with st.expander("🎨 Brand Color Palette", expanded=True):
                cols = st.columns(5)
                for idx, c in enumerate(content_plan["color_palette"]):
                    color_hex = c.get('color', '#000000')
                    with cols[idx]:
                        st.markdown(
                            f"<div style='width:100%;height:60px;border-radius:8px;background-color:{color_hex};border:1px solid #ddd'></div>",
                            unsafe_allow_html=True
                        )
                        st.markdown(f"**{c.get('name', 'Color')}**")
                        st.caption(f"{color_hex}")
                        st.caption(f"*{c.get('meaning', '')}*")

        # --- Weekly Content ---
        for week in content_plan['weekly_content']:
            # CLEAR WEEKLY HEADER
            st.markdown(f"## 🗓️ {week['theme']}") 
            st.markdown(f"*{week['theme_description']}*")
            st.divider()
            
            tabs = st.tabs([p.capitalize() for p in platforms])
            
            for p_idx, platform in enumerate(platforms):
                with tabs[p_idx]:
                    posts = week['platform_content'].get(platform, [])
                    for post in posts:
                        with st.container():
                            st.subheader(f"Week {week['week']} - Day {post['day']}")
                            st.caption(f"Type: {post['post_type'].title()}")
                            
                            c1, c2 = st.columns([1, 2])
                            
                            with c1:
                                st.info(f"**💡 Idea:** {post['idea']}")
                                st.markdown(f"**📸 Visual Suggestion:**\n*{post['visual_description']}*")
                            
                            with c2:
                                st.markdown("**📋 Copy this Post:**")
                                st.text_area(
                                    label="content_area",
                                    value=post['full_post_text'],
                                    height=300,
                                    label_visibility="collapsed",
                                    key=f"w{week['week']}_d{post['day']}_{platform}"
                                )
                            st.divider()

if __name__ == "__main__":
    main()