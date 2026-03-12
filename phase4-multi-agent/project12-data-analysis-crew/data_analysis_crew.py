# data_analysis_crew.py
# Project 12: Data Analysis Crew
# Three specialized agents collaborate to clean, analyze, and report on business data.
# This demonstrates the data pipeline pattern used by business intelligence teams.

# Standard library imports
import os           # For file system operations and environment variables
import json         # For parsing structured data from agents
from datetime import datetime  # For timestamping reports

# Load environment variables from the .env file
from dotenv import load_dotenv
load_dotenv()  # Reads ANTHROPIC_API_KEY from .env

# TypedDict for defining the shared state structure
from typing import TypedDict, Optional

# LangGraph for building the multi-agent workflow
from langgraph.graph import StateGraph, END

# ChatAnthropic wrapper for Claude API
from langchain_anthropic import ChatAnthropic

# Message types for prompting Claude
from langchain_core.messages import HumanMessage, SystemMessage

# Pandas for data loading, cleaning, and analysis
import pandas as pd

# StringIO lets us feed CSV content from a string (not a file) to pandas
from io import StringIO


# ============================================================
# STEP 1: DEFINE THE SHARED STATE
# ============================================================
# State is shared across all three agents.
# Think of it as the project folder everyone on the team can access.

class DataAnalysisState(TypedDict):
    # Path to the CSV file being analyzed
    csv_path: str

    # A text summary of the raw data as loaded (before cleaning)
    # Describes column types, missing values, sample rows, etc.
    raw_data_summary: Optional[str]

    # The Data Cleaner's plan for improving data quality
    # Describes what needs to be fixed and why
    cleaning_plan: Optional[str]

    # A summary of the cleaned dataset after cleaning was applied
    # Describes what was fixed, final shape, quality metrics
    cleaned_data_summary: Optional[str]

    # The statistical findings from the Data Analyst
    # Includes trends, top performers, anomalies, key metrics
    analysis_findings: Optional[str]

    # The executive business report from the Business Insights Writer
    # Plain language recommendations for decision-makers
    business_report: Optional[str]

    # The actual cleaned pandas DataFrame stored as a CSV string
    # We store it as a string because TypedDict requires serializable types
    cleaned_data_csv: Optional[str]


# ============================================================
# STEP 2: INITIALIZE THE AI MODEL
# ============================================================

# Create the Claude model instance
llm = ChatAnthropic(
    model="claude-opus-4-6",                               # Most capable model
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),  # From .env
    max_tokens=4096                                    # Reports can be long
)


# ============================================================
# STEP 3: DEFINE AGENT SYSTEM PROMPTS
# ============================================================

# Agent 1: Data Engineer / Data Cleaner
CLEANER_SYSTEM_PROMPT = """You are a data engineer. Analyze this CSV data description and identify: missing values, duplicates, outliers, incorrect data types. Provide a cleaning plan.

When analyzing data quality:
1. Identify every column with missing values and suggest how to handle them (remove, fill with mean/median/mode, or flag)
2. Check for duplicate rows and identify the duplication pattern
3. Look for outliers — values that are statistically unusual (more than 3 standard deviations from the mean)
4. Verify data types make sense (dates should be dates, numbers should be numbers)
5. Check for consistency issues (same value written different ways, e.g., "North" vs "NORTH")
6. Provide a specific, actionable cleaning plan

Format your response as:
## Data Quality Report

### Dataset Overview
[Size, columns, general quality]

### Issues Found
[List each issue with column name, issue type, and count]

### Cleaning Plan
[Step-by-step plan to fix each issue]

### Expected Result After Cleaning
[What the clean dataset will look like]"""

# Agent 2: Data Analyst
ANALYST_SYSTEM_PROMPT = """You are a data analyst. Given cleaned data, perform: trend analysis, identify top performers, calculate key metrics, find anomalies.

When analyzing data:
1. Calculate summary statistics for all numeric columns
2. Identify the top 3 and bottom 3 performers in each relevant category
3. Look for trends over time if date columns are present
4. Calculate derived metrics where relevant (e.g., revenue per unit, growth rates)
5. Identify any anomalies or surprising patterns
6. Be specific with numbers — include actual values, percentages, and comparisons

Format your response as:
## Data Analysis Findings

### Key Metrics Summary
[Most important numbers at a glance]

### Performance Analysis
[Who is performing best/worst and by how much]

### Trend Analysis
[How metrics change over time]

### Anomalies and Notable Findings
[Surprising patterns, outliers in performance, unusual data points]

### Statistical Summary
[Means, medians, ranges for key numeric columns]"""

# Agent 3: Business Intelligence Consultant
INSIGHTS_SYSTEM_PROMPT = """You are a business intelligence consultant. Transform data analysis findings into executive-level business insights and recommendations.

When writing business insights:
1. Lead with the most impactful finding — what should the executive know first?
2. Translate statistical findings into business language (avoid jargon)
3. Every finding should connect to a business decision or action
4. Provide 3-5 specific, actionable recommendations
5. Quantify the potential impact of recommendations where possible
6. Keep it concise — executives are busy, every sentence must earn its place
7. Use confident, declarative language

Format your response as:
## Executive Business Intelligence Report

### Executive Summary
[3-5 sentences capturing the most important insights]

### Key Business Findings

#### Finding 1: [Title]
[Business context, what the data shows, what it means]

#### Finding 2: [Title]
[Business context, what the data shows, what it means]

[Continue for all significant findings]

### Strategic Recommendations
1. [Specific actionable recommendation with expected impact]
2. [Specific actionable recommendation with expected impact]
3. [Specific actionable recommendation with expected impact]

### Risk Factors
[What the data suggests could go wrong]

### Conclusion
[One paragraph summary and call to action]"""


# ============================================================
# STEP 4: DEFINE THE AGENT NODES
# ============================================================

def clean_node(state: DataAnalysisState) -> dict:
    """
    Node 1: Data Cleaner Agent
    Loads the CSV file using pandas, generates a data quality report,
    applies cleaning steps, and produces a cleaned dataset.
    Returns: raw_data_summary, cleaning_plan, cleaned_data_summary, cleaned_data_csv
    """
    # Announce which agent is working
    print("\n" + "="*60)
    print("🧹 Data Cleaner loading and cleaning data...")
    print(f"   File: {state['csv_path']}")
    print("="*60)

    # ---- STEP A: Load the raw CSV using pandas ----
    try:
        # pd.read_csv() loads the CSV file into a DataFrame
        # A DataFrame is like a spreadsheet in Python — rows and columns
        df = pd.read_csv(state["csv_path"])
        print(f"   ✅ Loaded {len(df)} rows × {len(df.columns)} columns")
    except FileNotFoundError:
        # File does not exist
        print(f"   ❌ File not found: {state['csv_path']}")
        return {
            "raw_data_summary": f"Error: File not found at {state['csv_path']}",
            "cleaning_plan": "Cannot proceed — file not found",
            "cleaned_data_summary": "No data to clean",
            "cleaned_data_csv": ""
        }

    # ---- STEP B: Generate a text description of the raw data ----
    # We will pass this description to the AI agent instead of the raw data
    # (AI works better with text descriptions than raw CSVs for large files)

    raw_summary_parts = []

    # Basic shape information
    raw_summary_parts.append(f"Dataset Shape: {len(df)} rows × {len(df.columns)} columns")

    # Column names and data types
    raw_summary_parts.append("\nColumn Information:")
    for col in df.columns:
        dtype = str(df[col].dtype)           # The data type (int64, float64, object, etc.)
        missing = df[col].isnull().sum()     # Count of missing/null values
        unique = df[col].nunique()           # Count of unique values
        raw_summary_parts.append(f"  - {col}: type={dtype}, missing={missing}, unique_values={unique}")

    # Sample rows to show the AI what the data looks like
    raw_summary_parts.append("\nFirst 5 Rows (sample):")
    raw_summary_parts.append(df.head(5).to_string())

    # Check for duplicate rows
    duplicate_count = df.duplicated().sum()
    raw_summary_parts.append(f"\nDuplicate Rows: {duplicate_count}")

    # Basic statistics for numeric columns
    raw_summary_parts.append("\nNumeric Column Statistics:")
    numeric_cols = df.select_dtypes(include=['number']).columns  # Get only numeric columns
    if len(numeric_cols) > 0:
        raw_summary_parts.append(df[numeric_cols].describe().to_string())

    # Combine all parts into one string
    raw_data_summary = "\n".join(raw_summary_parts)

    print(f"   Raw data summary generated: {len(raw_data_summary)} characters")

    # ---- STEP C: Ask the AI Data Cleaner to analyze quality and plan cleaning ----
    cleaner_prompt = f"""Please analyze the following dataset and provide a data quality report and cleaning plan.

DATASET SUMMARY:
{raw_data_summary}

Based on this information:
1. Identify all data quality issues (missing values, duplicates, outliers, type issues)
2. Provide a specific cleaning plan to address each issue
3. Describe what the cleaned dataset should look like"""

    # Call the Data Cleaner agent
    response = llm.invoke([
        SystemMessage(content=CLEANER_SYSTEM_PROMPT),  # Data engineer identity
        HumanMessage(content=cleaner_prompt)            # The task
    ])

    cleaning_plan = response.content

    # ---- STEP D: Apply the cleaning steps programmatically using pandas ----
    # We apply standard cleaning steps directly in Python
    # (rather than asking the AI to write pandas code, which could have errors)

    # Create a copy of the dataframe to avoid modifying the original
    df_clean = df.copy()

    # Remove exact duplicate rows
    rows_before = len(df_clean)
    df_clean = df_clean.drop_duplicates()    # Remove completely duplicate rows
    duplicates_removed = rows_before - len(df_clean)
    print(f"   Removed {duplicates_removed} duplicate rows")

    # Fill missing numeric values with the column median
    # Median is better than mean for data with outliers
    numeric_columns = df_clean.select_dtypes(include=['number']).columns
    for col in numeric_columns:
        missing_count = df_clean[col].isnull().sum()  # Count missing values
        if missing_count > 0:
            median_value = df_clean[col].median()     # Calculate the median
            df_clean[col] = df_clean[col].fillna(median_value)  # Fill with median
            print(f"   Filled {missing_count} missing values in '{col}' with median {median_value:.2f}")

    # Fill missing text/categorical values with "Unknown"
    text_columns = df_clean.select_dtypes(include=['object']).columns
    for col in text_columns:
        missing_count = df_clean[col].isnull().sum()  # Count missing values
        if missing_count > 0:
            df_clean[col] = df_clean[col].fillna("Unknown")  # Fill with "Unknown"
            print(f"   Filled {missing_count} missing values in '{col}' with 'Unknown'")

    # ---- STEP E: Generate a summary of the cleaned data ----
    cleaned_summary_parts = []
    cleaned_summary_parts.append(f"Cleaned Dataset Shape: {len(df_clean)} rows × {len(df_clean.columns)} columns")
    cleaned_summary_parts.append(f"Rows removed (duplicates): {duplicates_removed}")
    cleaned_summary_parts.append(f"Total missing values remaining: {df_clean.isnull().sum().sum()}")

    # Statistics for numeric columns in the clean data
    cleaned_summary_parts.append("\nCleaned Numeric Statistics:")
    if len(numeric_columns) > 0:
        cleaned_summary_parts.append(df_clean[numeric_columns].describe().to_string())

    # Group totals if relevant columns exist (look for revenue and units columns)
    if "revenue" in df_clean.columns:
        total_revenue = df_clean["revenue"].sum()
        cleaned_summary_parts.append(f"\nTotal Revenue: ${total_revenue:,.2f}")

    if "units_sold" in df_clean.columns:
        total_units = df_clean["units_sold"].sum()
        cleaned_summary_parts.append(f"Total Units Sold: {total_units:,}")

    # Group by region if that column exists
    if "region" in df_clean.columns and "revenue" in df_clean.columns:
        region_totals = df_clean.groupby("region")["revenue"].sum().sort_values(ascending=False)
        cleaned_summary_parts.append("\nRevenue by Region:")
        for region, rev in region_totals.items():
            cleaned_summary_parts.append(f"  {region}: ${rev:,.2f}")

    # Group by product if that column exists
    if "product" in df_clean.columns and "revenue" in df_clean.columns:
        product_totals = df_clean.groupby("product")["revenue"].sum().sort_values(ascending=False)
        cleaned_summary_parts.append("\nRevenue by Product:")
        for product, rev in product_totals.items():
            cleaned_summary_parts.append(f"  {product}: ${rev:,.2f}")

    # Group by sales_rep if that column exists
    if "sales_rep" in df_clean.columns and "revenue" in df_clean.columns:
        rep_totals = df_clean.groupby("sales_rep")["revenue"].sum().sort_values(ascending=False)
        cleaned_summary_parts.append("\nRevenue by Sales Rep:")
        for rep, rev in rep_totals.items():
            cleaned_summary_parts.append(f"  {rep}: ${rev:,.2f}")

    # Add all rows for the analyst to work with
    cleaned_summary_parts.append("\nFull Cleaned Dataset:")
    cleaned_summary_parts.append(df_clean.to_string())

    cleaned_data_summary = "\n".join(cleaned_summary_parts)

    # Store the cleaned dataframe as a CSV string for potential downstream use
    cleaned_data_csv = df_clean.to_csv(index=False)

    print(f"\n   ✅ Data cleaning complete!")
    print(f"   Final dataset: {len(df_clean)} rows × {len(df_clean.columns)} columns")

    # Return all the new state values
    return {
        "raw_data_summary": raw_data_summary,
        "cleaning_plan": cleaning_plan,
        "cleaned_data_summary": cleaned_data_summary,
        "cleaned_data_csv": cleaned_data_csv
    }


def analyze_node(state: DataAnalysisState) -> dict:
    """
    Node 2: Data Analyst Agent
    Takes the cleaned data summary and performs deep analysis:
    trends, top performers, anomalies, key metrics.
    Returns: analysis_findings
    """
    # Announce which agent is working
    print("\n" + "="*60)
    print("📊 Data Analyst performing analysis...")
    print("="*60)

    # Build the prompt for the analyst
    # We give it the full cleaned data summary including grouped statistics
    analyst_prompt = f"""Please perform a comprehensive data analysis on the following cleaned sales dataset.

CLEANED DATA SUMMARY AND STATISTICS:
{state['cleaned_data_summary']}

Please analyze:
1. Overall performance metrics (total revenue, units, averages)
2. Top 3 and bottom 3 performers by product
3. Top 3 and bottom 3 performers by region
4. Top 3 and bottom 3 performers by sales representative
5. Any trends or patterns over time (if date data is available)
6. Customer satisfaction patterns (if that data is available)
7. Any anomalies, outliers, or surprising findings
8. Relationships between variables (e.g., high units but low revenue = low-price products)"""

    # Call the Data Analyst agent
    response = llm.invoke([
        SystemMessage(content=ANALYST_SYSTEM_PROMPT),  # Analyst identity
        HumanMessage(content=analyst_prompt)            # The task
    ])

    # Extract the analysis findings
    analysis_findings = response.content

    # Show preview in terminal
    print(f"\n📊 Analysis Findings Preview (first 500 chars):")
    print("-" * 40)
    print(analysis_findings[:500] + "..." if len(analysis_findings) > 500 else analysis_findings)
    print("-" * 40)
    print(f"   Total findings: {len(analysis_findings)} characters")

    # Return the analysis findings to state
    return {"analysis_findings": analysis_findings}


def insights_node(state: DataAnalysisState) -> dict:
    """
    Node 3: Business Insights Writer Agent
    Takes the analysis findings and transforms them into executive-level
    business language with specific, actionable recommendations.
    Returns: business_report
    """
    # Announce which agent is working
    print("\n" + "="*60)
    print("💼 Business Intelligence Consultant writing report...")
    print("="*60)

    # Build the prompt for the BI consultant
    insights_prompt = f"""Please transform the following data analysis into an executive business intelligence report.

DATA ANALYSIS FINDINGS:
{state['analysis_findings']}

CLEANING CONTEXT (what data quality issues were found and resolved):
{state.get('cleaning_plan', 'No cleaning issues noted')[:500]}

Write an executive-level report that:
1. Opens with the most impactful business insight
2. Translates every statistical finding into business language
3. Provides 3-5 specific, actionable recommendations
4. Connects findings to real business decisions
5. Flags any risks or areas requiring attention"""

    # Call the Business Insights Writer agent
    response = llm.invoke([
        SystemMessage(content=INSIGHTS_SYSTEM_PROMPT),  # BI consultant identity
        HumanMessage(content=insights_prompt)            # The task
    ])

    # Extract the business report
    business_report = response.content

    # Show preview in terminal
    print(f"\n💼 Business Report Preview (first 500 chars):")
    print("-" * 40)
    print(business_report[:500] + "..." if len(business_report) > 500 else business_report)
    print("-" * 40)
    print(f"   Total report length: {len(business_report)} characters")

    # Return the business report to state
    return {"business_report": business_report}


def report_node(state: DataAnalysisState) -> dict:
    """
    Final Node: Save all outputs to the reports/ directory.
    Saves:
    - The data quality report and cleaning plan
    - The analysis findings
    - The full executive business report
    - A combined master report
    """
    # Announce the final save step
    print("\n" + "="*60)
    print("💾 Saving reports to reports/ directory...")
    print("="*60)

    # Create the reports directory if it does not exist
    os.makedirs("reports", exist_ok=True)

    # Create a timestamp for this run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create a safe name from the CSV filename
    csv_name = os.path.basename(state["csv_path"]).replace(".csv", "").replace(" ", "_")

    # ---- Save the data quality and cleaning report ----
    cleaning_path = f"reports/{csv_name}_data_quality_{timestamp}.md"
    with open(cleaning_path, "w", encoding="utf-8") as f:
        f.write(f"# Data Quality Report\n")
        f.write(f"**Dataset:** {state['csv_path']}\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Raw Data Overview\n\n")
        f.write("```\n")
        f.write(state.get("raw_data_summary", "No summary available"))
        f.write("\n```\n\n")
        f.write("## Cleaning Plan and Actions\n\n")
        f.write(state.get("cleaning_plan", "No cleaning plan available"))
    print(f"   📋 Data quality report: {cleaning_path}")

    # ---- Save the analysis findings ----
    analysis_path = f"reports/{csv_name}_analysis_{timestamp}.md"
    with open(analysis_path, "w", encoding="utf-8") as f:
        f.write(f"# Data Analysis Findings\n")
        f.write(f"**Dataset:** {state['csv_path']}\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(state.get("analysis_findings", "No analysis available"))
    print(f"   📊 Analysis findings: {analysis_path}")

    # ---- Save the executive business report ----
    business_report_path = f"reports/{csv_name}_executive_report_{timestamp}.md"
    with open(business_report_path, "w", encoding="utf-8") as f:
        f.write(state.get("business_report", "No report available"))
    print(f"   💼 Executive report: {business_report_path}")

    # ---- Save the cleaned data as CSV ----
    if state.get("cleaned_data_csv"):
        clean_csv_path = f"reports/{csv_name}_cleaned_{timestamp}.csv"
        with open(clean_csv_path, "w", encoding="utf-8") as f:
            f.write(state["cleaned_data_csv"])
        print(f"   🗂️  Cleaned data CSV: {clean_csv_path}")

    # ---- Save a combined master report ----
    master_path = f"reports/{csv_name}_master_report_{timestamp}.md"
    with open(master_path, "w", encoding="utf-8") as f:
        f.write(f"# Complete Data Analysis Report\n")
        f.write(f"**Dataset:** {state['csv_path']}\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Generated by:** 3-Agent AI Analysis Crew\n\n")
        f.write("---\n\n")
        f.write("# PART 1: DATA QUALITY\n\n")
        f.write(state.get("cleaning_plan", "No cleaning plan available"))
        f.write("\n\n---\n\n")
        f.write("# PART 2: DATA ANALYSIS\n\n")
        f.write(state.get("analysis_findings", "No analysis available"))
        f.write("\n\n---\n\n")
        f.write("# PART 3: EXECUTIVE INSIGHTS\n\n")
        f.write(state.get("business_report", "No report available"))
    print(f"   📚 Master report: {master_path}")

    # Display the executive report in the terminal
    print("\n" + "="*60)
    print("EXECUTIVE BUSINESS REPORT")
    print("="*60)
    print(state.get("business_report", "No report generated"))
    print("="*60)

    print(f"\n✅ All reports saved to reports/")
    return {}  # No state changes needed at the end


# ============================================================
# STEP 5: BUILD THE LANGGRAPH WORKFLOW
# ============================================================

def build_analysis_crew() -> StateGraph:
    """
    Builds the data analysis crew workflow.
    Flow: clean → analyze → insights → report → END
    This is a linear pipeline — no loops needed for data analysis.
    """
    # Create the workflow graph
    workflow = StateGraph(DataAnalysisState)

    # Register all nodes in the graph
    workflow.add_node("clean", clean_node)        # Data Cleaner agent
    workflow.add_node("analyze", analyze_node)    # Data Analyst agent
    workflow.add_node("insights", insights_node)  # Business Insights Writer agent
    workflow.add_node("report", report_node)       # Final output saver

    # Set the entry point
    workflow.set_entry_point("clean")

    # Define the pipeline flow — completely linear for data analysis
    workflow.add_edge("clean", "analyze")      # After cleaning, analyze
    workflow.add_edge("analyze", "insights")   # After analysis, write insights
    workflow.add_edge("insights", "report")    # After insights, save report
    workflow.add_edge("report", END)           # After saving, done

    # Compile the workflow
    compiled = workflow.compile()

    print("\n✅ Data analysis crew built!")
    print("   Flow: clean → analyze → insights → report → END")

    return compiled


# ============================================================
# STEP 6: MAIN ENTRY POINT
# ============================================================

def run_data_analysis_crew(csv_path: str):
    """
    Main function to run the full data analysis crew on a CSV file.
    Three agents will clean, analyze, and report on the data automatically.
    """
    print("\n" + "📊 "*20)
    print("DATA ANALYSIS CREW")
    print("📊 "*20)
    print("\nThis system uses THREE specialized AI agents:")
    print("   1. 🧹 Data Cleaner           — finds and fixes data quality issues")
    print("   2. 📊 Data Analyst           — identifies trends, patterns, top performers")
    print("   3. 💼 BI Insights Writer     — produces executive business recommendations")
    print(f"\nAnalyzing: {csv_path}")

    # Check that the file exists
    if not os.path.exists(csv_path):
        print(f"\n❌ Error: File not found: {csv_path}")
        print("Please check the file path and try again.")
        return None

    # Build the workflow
    app = build_analysis_crew()

    # Set up the initial state
    initial_state = {
        "csv_path": csv_path,             # The file to analyze
        "raw_data_summary": None,          # Will be filled by clean_node
        "cleaning_plan": None,             # Will be filled by clean_node
        "cleaned_data_summary": None,      # Will be filled by clean_node
        "analysis_findings": None,         # Will be filled by analyze_node
        "business_report": None,           # Will be filled by insights_node
        "cleaned_data_csv": None           # Will be filled by clean_node
    }

    # Run the pipeline
    print("\n⏳ Running data analysis crew... (this may take 60-90 seconds)")
    final_state = app.invoke(initial_state)

    print("\n" + "="*60)
    print("✅ DATA ANALYSIS CREW COMPLETE!")
    print("="*60)
    print("   Check the reports/ directory for all saved reports.")

    return final_state


# ============================================================
# STEP 7: RUN IF EXECUTED DIRECTLY
# ============================================================

if __name__ == "__main__":
    import sys  # For reading command-line arguments

    # Check if a CSV file was provided as a command-line argument
    if len(sys.argv) > 1:
        # User provided a file path
        csv_file = sys.argv[1]
    else:
        # Default to the sample sales data file
        csv_file = "sample_sales_data.csv"
        print(f"No file specified. Using default: {csv_file}")
        print("Usage: python data_analysis_crew.py <your_data.csv>")
        print()

    # Run the analysis
    run_data_analysis_crew(csv_file)
