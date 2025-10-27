import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import os

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyD9AqMnpmyZ2bd3tcRstyvT0F_FbqCxRAg"
genai.configure(api_key=GEMINI_API_KEY)

# Page configuration
st.set_page_config(
    page_title="ArchScope - Building Analysis AI",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: bold;
        border-radius: 10px;
        height: 3rem;
        border: none;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #764ba2 0%, #667eea 100%);
        transform: scale(1.05);
        transition: all 0.3s ease;
    }
    .stage-card {
        padding: 1rem;
        border-radius: 10px;
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    .deficiency-box {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .recommendation-box {
        background: #d1ecf1;
        border-left: 4px solid #0dcaf0;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar for controls
st.sidebar.title("🏗️ ArchScope")
st.sidebar.markdown("### Building Analysis Configuration")

# Construction stages
CONSTRUCTION_STAGES = {
    "Foundation & Sitework": {
        "focus": "Excavation depth, concrete quality, rebar placement, drainage systems, soil compaction",
        "common_issues": ["Cracks in foundation", "Improper drainage", "Inadequate footing depth", "Steel reinforcement issues"]
    },
    "Framing & Structure": {
        "focus": "Wood quality, spacing of studs/joists, alignment, load-bearing walls, structural integrity",
        "common_issues": ["Incorrect stud spacing", "Warped or damaged lumber", "Missing headers", "Improper load distribution"]
    },
    "Electrical Systems": {
        "focus": "Wiring installation, panel organization, outlet placement, code compliance, safety measures",
        "common_issues": ["Exposed wiring", "Improper grounding", "Inadequate circuit protection", "Code violations"]
    },
    "Plumbing Systems": {
        "focus": "Pipe installation, fixture placement, drainage slope, pressure testing, backflow prevention",
        "common_issues": ["Incorrect pipe slope", "Leaks at joints", "Improper fixture installation", "Water pressure issues"]
    },
    "Roofing & Insulation": {
        "focus": "Shingle quality, flashing details, ventilation, insulation coverage, waterproofing",
        "common_issues": ["Missing shingles", "Improper flashing", "Inadequate ventilation", "Roof leaks"]
    },
    "Interior Finishing": {
        "focus": "Drywall quality, flooring installation, trim work, paint quality, finish details",
        "common_issues": ["Cracks in drywall", "Uneven flooring", "Paint blemishes", "Trim gaps"]
    }
}

# Initialize session state
if 'analysis_history' not in st.session_state:
    st.session_state.analysis_history = []

# Header
st.markdown('<p class="main-header">ArchScope</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">AI-Powered Building Structure Analysis</p>', unsafe_allow_html=True)

# File upload
st.markdown("## 📸 Upload Building Image")
uploaded_file = st.file_uploader(
    "Choose an image file",
    type=['jpg', 'jpeg', 'png'],
    help="Upload an image of a building or construction site"
)

col1, col2 = st.columns([1, 1])

with col1:
    if uploaded_file is not None:
        # Display uploaded image
        # Reset file pointer to beginning for display
        uploaded_file.seek(0)
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_container_width=True)

with col2:
    if uploaded_file is not None:
        # Stage selection
        selected_stage = st.selectbox(
            "Select Construction Stage",
            options=list(CONSTRUCTION_STAGES.keys()),
            help="Choose the current construction stage to get specific analysis"
        )
        
        stage_info = CONSTRUCTION_STAGES[selected_stage]
        st.info(f"**Focus Areas:** {stage_info['focus']}")
        
        st.markdown("### Analysis Parameters")
        analysis_depth = st.slider("Analysis Depth", 1, 5, 3, 
                                    help="Depth of analysis (1=Quick, 5=Comprehensive)")
        
        include_recommendations = st.checkbox("Include Remediation Recommendations", value=True)
        
        safety_focus = st.checkbox("Prioritize Safety Concerns", value=True)

# Analysis button
if uploaded_file is not None:
    st.markdown("---")
    analyze_button = st.button("🔍 Analyze Building Image", use_container_width=True)
    
    if analyze_button:
        with st.spinner("Analyzing image with Gemini AI... This may take a moment."):
            try:
                # Prepare the prompt
                prompt = f"""
                You are an expert building inspector analyzing a construction site or building image.
                
                Construction Stage: {selected_stage}
                
                This stage typically focuses on: {stage_info['focus']}
                Common issues to watch for: {', '.join(stage_info['common_issues'])}
                
                Provide a detailed analysis with:
                1. Overall Assessment: A summary of the construction quality and progress
                2. Detected Deficiencies: List any structural issues, code violations, or quality concerns found
                3. Severity Rating: Rate each issue as Low, Medium, High, or Critical
                4. Remediation Recommendations: Specific, actionable steps to address each deficiency
                5. Compliance Status: Note if there are any code violations or safety concerns
                
                Analysis depth level: {analysis_depth} out of 5
                Safety prioritization: {"High" if safety_focus else "Standard"}
                
                Format your response in clear, professional sections suitable for building inspection reports.
                Be specific about measurements, locations, and technical details when possible.
                """
                
                # Get Gemini model - using gemini-1.5-flash for better vision support
                model = genai.GenerativeModel('gemini-2.0-flash')
                
                # Read image bytes
                uploaded_file.seek(0)
                image_bytes = uploaded_file.read()
                
                # Determine mime type
                file_extension = uploaded_file.name.split('.')[-1].lower()
                mime_type = f"image/{file_extension}" if file_extension in ['jpg', 'jpeg', 'png'] else "image/jpeg"
                
                # Prepare content for analysis
                content_parts = [
                    prompt,
                    {
                        "mime_type": mime_type,
                        "data": image_bytes
                    }
                ]
                
                # Analyze the image
                response = model.generate_content(content_parts)
                analysis_text = response.text
                
                # Display results
                st.markdown("---")
                st.markdown("## 📊 Analysis Results")
                
                # Parse and display the analysis
                paragraphs = analysis_text.split('\n\n')
                current_section = ""
                
                for para in paragraphs:
                    para = para.strip()
                    if not para:
                        continue
                    
                    # Check for section headers
                    if para.upper().startswith('OVERALL ASSESSMENT'):
                        st.markdown("### ✅ Overall Assessment")
                        current_section = "assessment"
                    elif para.upper().startswith('DETECTED DEFICIENCIES') or para.upper().startswith('DEFICIENCIES'):
                        st.markdown("### ⚠️ Detected Deficiencies")
                        current_section = "deficiencies"
                        st.markdown('<div class="deficiency-box">', unsafe_allow_html=True)
                    elif para.upper().startswith('REMEDIATION RECOMMENDATIONS') or para.upper().startswith('RECOMMENDATIONS'):
                        st.markdown("</div>", unsafe_allow_html=True)
                        st.markdown("### 🔧 Remediation Recommendations")
                        current_section = "recommendations"
                        st.markdown('<div class="recommendation-box">', unsafe_allow_html=True)
                    elif para.upper().startswith('COMPLIANCE STATUS') or para.upper().startswith('COMPLIANCE'):
                        st.markdown("</div>", unsafe_allow_html=True)
                        st.markdown("### 📋 Compliance Status")
                        current_section = "compliance"
                    else:
                        if current_section == "deficiencies":
                            st.markdown(f"⚠️ **{para}**")
                        elif current_section == "recommendations":
                            st.markdown(f"💡 {para}")
                        else:
                            st.markdown(para)
                
                # Close any open divs
                if current_section in ["deficiencies", "recommendations"]:
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # Store in history
                analysis_record = {
                    'stage': selected_stage,
                    'image': uploaded_file.name,
                    'analysis': analysis_text
                }
                st.session_state.analysis_history.append(analysis_record)
                
                st.success("✅ Analysis complete!")
                
                # Download analysis button
                st.markdown("---")
                analysis_file = io.StringIO(analysis_text)
                st.download_button(
                    label="📥 Download Full Analysis Report",
                    data=analysis_file.getvalue(),
                    file_name=f"archscope_analysis_{selected_stage.replace(' ', '_')}.txt",
                    mime="text/plain"
                )
                
            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                st.info("Please make sure your API key is valid and the image is clear and properly formatted.")

# Show analysis history
if st.session_state.analysis_history:
    with st.expander("📚 View Previous Analyses"):
        for i, record in enumerate(reversed(st.session_state.analysis_history[-5:]), 1):
            st.markdown(f"#### Analysis #{len(st.session_state.analysis_history) - i + 1}: {record['stage']}")
            st.text(record['analysis'][:200] + "...")
            st.markdown("---")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; padding: 2rem;'>"
    "ArchScope | AI-Powered Building Analysis | Powered by Google Gemini AI"
    "</div>",
    unsafe_allow_html=True
)
