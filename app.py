import streamlit as st
from jd_agent.agent import agent
from dotenv import load_dotenv
import os
import json

load_dotenv()

# Check for required API keys
required_keys = ["OPENAI_API_KEY"]
missing_keys = [key for key in required_keys if not os.getenv(key)]

if missing_keys:
    st.error(f"⚠️ Missing API keys in .env file: {', '.join(missing_keys)}")
    st.info("Please add the following to your .env file:\n" + 
            "\n".join([f"{key}=your_key_here" for key in missing_keys]))
    st.stop()

# Page config
st.set_page_config(page_title="JD Generator Agent", layout="wide", page_icon="📄")

st.title("📄 AI-Powered Job Description Generator")
st.write("Fill in the details below and let our AI agent generate a professional, ATS-ready job description.")

# ---------------------------------------------------------------
# SIDEBAR INPUT FIELDS
# ---------------------------------------------------------------
with st.sidebar:
    st.header("📋 Job Details")
    
    st.subheader("Company Information")
    client = st.text_input("Client/Company Name*", "TechCorp", 
                           help="Company name for 'About Us' section")
    
    st.subheader("Position Details")
    job_id = st.text_input("Job ID", "TC-1234")
    job_title = st.text_input("Job Title*", "Senior Python Developer")
    department = st.text_input("Department", "Engineering")
    positions_filled = st.text_input("Number of Positions", "2")
    
    st.subheader("Job Description")
    description = st.text_area("Additional Description", 
                               "Build scalable backend systems using modern technologies",
                               help="Brief overview of what the role entails")
    
    st.subheader("Requirements")
    experience = st.text_input("Total Experience Required", "6+ years")
    relevant_exp = st.text_input("Relevant Experience", "4+ years in Python development")
    education = st.text_input("Education Qualification", "Bachelor's in Computer Science or related field")
    skills = st.text_area("Required Skills (comma-separated)", 
                          "Python, FastAPI, AWS, Docker, PostgreSQL, Redis")
    
    st.subheader("Employment Terms")
    work_mode = st.selectbox("Work Mode", ["Hybrid", "Remote", "On-site"])
    location = st.text_input("Location", "Bangalore, India")
    employment_type = st.selectbox("Employment Type", 
                                   ["Full-time", "Part-time", "Contract", "Temporary"])
    salary = st.text_input("Maximum Salary/Budget", "25 LPA")
    
    st.markdown("---")
    generate_btn = st.button("🚀 Generate Job Description", type="primary", use_container_width=True)

# ---------------------------------------------------------------
# MAIN CONTENT AREA
# ---------------------------------------------------------------
if generate_btn:
    
    # Validate required fields
    if not client or not job_title:
        st.error("❌ Please fill in required fields: Client/Company Name and Job Title")
        st.stop()

    # Prepare user input
    user_input = f"""
    Client: {client}
    Job ID: {job_id}
    Job Title: {job_title}
    Description: {description}
    Department: {department}
    Experience: {experience}
    Relevant Experience: {relevant_exp}
    Skills: {skills}
    Max Salary: {salary}
    Work Mode: {work_mode}
    Location: {location}
    Employment Type: {employment_type}
    Positions Filled: {positions_filled}
    Education: {education}
    """

    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("🔄 Initializing AI agent...")
        progress_bar.progress(10)
        
        status_text.text("✔️ Validating input...")
        progress_bar.progress(20)
        
        # Run the agent
        with st.spinner("⏳ AI agent is working on your job description..."):
            result = agent.invoke({"user_input": user_input})
        
        # Check if validation failed
        if result.get("validation_result") and not result.get("validation_result").upper().startswith("VALID"):
            progress_bar.progress(0)
            status_text.text("")
            st.error(f"❌ Input Validation Failed: {result.get('validation_result')}")
            st.info("💡 Please check your input and ensure all required fields are filled correctly.")
            st.stop()
        
        progress_bar.progress(100)
        status_text.text("✅ Job Description Generated Successfully!")
        
        # Extract results
        final_markdown = result.get("final_markdown", "No output generated")
        final_json = result.get("final_json", "{}")
        final_text = result.get("final_text", "No output generated")
        quality_check = result.get("quality_check", "{}")
        rewrite_attempts = result.get("rewrite_attempts", 0)

        st.success("🎉 Your job description is ready!")
        
        # ---------------------------------------------------------------
        # TABS FOR DIFFERENT VIEWS
        # ---------------------------------------------------------------
        tab1, tab2, tab3, tab4 = st.tabs([
            "📄 Markdown", 
            "📊 JSON", 
            "📝 Plain Text", 
            "⚙️ Process Details"
        ])
        
        with tab1:
            st.markdown("### Final Job Description (Markdown)")
            st.markdown(final_markdown)
            
            st.download_button(
                label="📥 Download Markdown",
                data=final_markdown,
                file_name=f"{job_title.replace(' ', '_')}_JD.md",
                mime="text/markdown",
                use_container_width=True
            )
        
        with tab2:
            st.markdown("### Final Job Description (JSON)")
            
            # Pretty print JSON
            try:
                parsed_json = json.loads(final_json)
                st.json(parsed_json)
                
                st.download_button(
                    label="📥 Download JSON",
                    data=json.dumps(parsed_json, indent=2),
                    file_name=f"{job_title.replace(' ', '_')}_JD.json",
                    mime="application/json",
                    use_container_width=True
                )
            except:
                st.code(final_json, language="json")
                st.warning("⚠️ Could not parse JSON for display")
        
        with tab3:
            st.markdown("### Final Job Description (Plain Text)")
            st.text(final_text)
            
            st.download_button(
                label="📥 Download Text",
                data=final_text,
                file_name=f"{job_title.replace(' ', '_')}_JD.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with tab4:
            st.markdown("### Generation Process")
            
            # Quality Check Results
            with st.expander("📊 Quality Check Results", expanded=True):
                try:
                    quality_data = json.loads(quality_check)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Overall Score", f"{quality_data.get('score', 0)}/100")
                    with col2:
                        st.metric("Status", "✅ PASS" if quality_data.get('pass') else "❌ FAIL")
                    with col3:
                        st.metric("Rewrite Attempts", rewrite_attempts)
                    
                    st.markdown("#### Detailed Scores")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Structure", f"{quality_data.get('structure_score', 0)}/30")
                        st.metric("Tone", f"{quality_data.get('tone_score', 0)}/25")
                    with col2:
                        st.metric("Realism", f"{quality_data.get('realism_score', 0)}/25")
                        st.metric("Clarity", f"{quality_data.get('clarity_score', 0)}/20")
                    
                    if quality_data.get('issues'):
                        st.markdown("#### Issues Identified")
                        for issue in quality_data.get('issues', []):
                            st.warning(issue)
                            
                except:
                    st.text(quality_check)
            
            # Rewrite History
            with st.expander("🔄 Rewrite History"):
                if rewrite_attempts > 0:
                    st.warning(f"The draft was rewritten {rewrite_attempts} time(s) to meet quality standards.")
                    st.info("Each rewrite addressed specific issues identified in the quality check.")
                else:
                    st.success("Draft passed quality check on first attempt! No rewrites needed.")
            
            # Validation
            with st.expander("✅ Input Validation"):
                validation_result = result.get("validation_result", "Unknown")
                normalized_input = result.get("normalized_input", "N/A")
                
                if validation_result.upper().startswith("VALID"):
                    st.success(f"Validation: {validation_result}")
                else:
                    st.error(f"Validation: {validation_result}")
                
                st.markdown("**Normalized Input:**")
                st.text(normalized_input[:1000] + "..." if len(normalized_input) > 1000 else normalized_input)
        
    except Exception as e:
        progress_bar.progress(0)
        status_text.text("")
        st.error(f"❌ Error generating job description: {str(e)}")
        st.exception(e)
        st.info("💡 Tip: Check your API key and try again")

else:
    # Initial state - show instructions
    st.info("👈 Fill in the job details in the sidebar and click **Generate Job Description**")
    
    # Show example
    with st.expander("📖 How it works - New Workflow"):
        st.markdown("""
        This AI-powered agent follows an optimized pipeline:
        
        1. **Validation** ✔️
           - Checks required fields
           - Normalizes and structures input
           - Validates data quality
        
        2. **Draft Generation** ✍️
           - Creates first draft with all sections
           - Uses structured, professional format
           - Based on normalized input
        
        3. **Quality Check** 📊
           - Evaluates structure (30 points)
           - Assesses tone (25 points)
           - Checks realism (25 points)
           - Measures clarity (20 points)
           - **Pass threshold: 70/100**
        
        4. **Rewrite (if needed)** 🔄
           - Addresses identified issues
           - Improves problem areas
           - Max 3 attempts
        
        5. **Review** 👁️
           - ATS optimization
           - Final polish
           - Consistency check
        
        6. **Final Output** 🎯
           - Markdown format
           - JSON format
           - Plain text format
        
        **Powered by GPT-4 Turbo**
        """)
    
    with st.expander("✨ Key Features"):
        st.markdown("""
        - 🤖 **Intelligent Validation**: Ensures input quality before processing
        - 📊 **Quality Scoring**: Objective evaluation with detailed metrics
        - 🔄 **Self-Correcting**: Automatically rewrites to meet standards
        - 📝 **Multiple Formats**: Get your JD in Markdown, JSON, and plain text
        - 🎯 **ATS-Ready**: Optimized for Applicant Tracking Systems
        - 🔍 **Transparent Process**: View scores, attempts, and validation results
        - ⚡ **Fast & Efficient**: Streamlined workflow without unnecessary research delays
        """)
    
    with st.expander("🎯 Quality Standards"):
        st.markdown("""
        **Our quality check evaluates:**
        
        - **Structure (30%)**: All sections present, well-organized, logical flow
        - **Tone (25%)**: Professional, inclusive, engaging language
        - **Realism (25%)**: Achievable requirements, not overstuffed with unrealistic expectations
        - **Clarity (20%)**: Clear, concise writing without excessive jargon
        
        **Passing Score**: 70/100 or higher
        
        The system automatically rewrites (up to 3 times) to meet these standards.
        """)