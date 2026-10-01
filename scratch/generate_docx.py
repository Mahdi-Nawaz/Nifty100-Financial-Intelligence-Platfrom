import os
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE

def add_heading(doc, text, level, align=WD_ALIGN_PARAGRAPH.LEFT):
    heading = doc.add_heading(text, level=level)
    heading.alignment = align
    return heading

def add_paragraph(doc, text, align=WD_ALIGN_PARAGRAPH.LEFT, bold=False):
    p = doc.add_paragraph()
    p.alignment = align
    run = p.add_run(text)
    if bold:
        run.bold = True
    return p

def main():
    doc = Document()
    
    # Title Page
    for _ in range(3):
        doc.add_paragraph()
        
    title = add_paragraph(doc, "Nifty 100 Financial Intelligence Platform\nwith Explainable AI", WD_ALIGN_PARAGRAPH.CENTER, bold=True)
    title.runs[0].font.size = Pt(20)
    
    for _ in range(2):
        doc.add_paragraph()
        
    p = add_paragraph(doc, "Major Project Synopsis Report\n(EEC401)", WD_ALIGN_PARAGRAPH.CENTER, bold=True)
    p.runs[0].font.size = Pt(14)
    
    for _ in range(2):
        doc.add_paragraph()
        
    p = add_paragraph(doc, "Submitted by", WD_ALIGN_PARAGRAPH.CENTER, bold=True)
    p.runs[0].font.size = Pt(12)
    p.runs[0].italic = True
    
    doc.add_paragraph()
    
    p = add_paragraph(doc, "MAHDI NAWAZ", WD_ALIGN_PARAGRAPH.CENTER, bold=True)
    p.runs[0].font.size = Pt(14)
    
    for _ in range(2):
        doc.add_paragraph()
        
    p = add_paragraph(doc, "in partial fulfillment for the award of the\ndegree of", WD_ALIGN_PARAGRAPH.CENTER, bold=True)
    p.runs[0].italic = True
    
    doc.add_paragraph()
    
    p = add_paragraph(doc, "BACHELOR OF TECHNOLOGY", WD_ALIGN_PARAGRAPH.CENTER, bold=True)
    p.runs[0].font.size = Pt(14)
    
    doc.add_paragraph()
    
    p = add_paragraph(doc, "IN\nCOMPUTER SCIENCE AND ENGINEERING", WD_ALIGN_PARAGRAPH.CENTER, bold=True)
    p.runs[0].font.size = Pt(14)
    
    for _ in range(3):
        doc.add_paragraph()
        
    p = add_paragraph(doc, "At", WD_ALIGN_PARAGRAPH.CENTER, bold=True)
    
    for _ in range(2):
        doc.add_paragraph()
        
    p = add_paragraph(doc, "GNA UNIVERSITY, PHAGWARA\nOCTOBER 2026", WD_ALIGN_PARAGRAPH.CENTER, bold=True)
    p.runs[0].font.size = Pt(14)
    
    doc.add_page_break()
    
    # Abstract
    add_heading(doc, 'Abstract', 1, WD_ALIGN_PARAGRAPH.CENTER)
    
    abstract_text = (
        "In the modern digital era, the exponential growth of data across various sectors such as "
        "finance, healthcare, education, and technology has created a strong demand for "
        "efficient systems capable of analyzing and extracting meaningful insights from raw "
        "datasets. However, traditional financial data analysis methods often require significant expertise "
        "in programming, accounting, and domain knowledge, making them difficult for "
        "non-technical users and retail investors to utilize effectively.\n\n"
        "This project presents the Nifty 100 Financial Intelligence Platform with Explainable AI, "
        "which aims to automate the major stages of the financial analysis pipeline, including data "
        "aggregation (Profit & Loss, Balance Sheet, Cash Flow), financial ratio calculations, capital "
        "allocation analysis, and reporting. The system enables users to interact with structured financial "
        "data across the Nifty 100 universe and perform in-depth analysis seamlessly.\n\n"
        "Following data integration, the system conducts exploratory financial analysis, computes key metrics "
        "like Return on Equity (ROE) and Debt-to-Equity ratios, and evaluates the dataset for machine "
        "learning readiness to forecast future financial health. Based on these analyses, the system generates "
        "automated insights that help users better understand capital allocation patterns and sector median metrics.\n\n"
        "The system also provides functionality for generating downloadable comprehensive financial datasets "
        "and structured reports, making it suitable for practical use. The user interface is "
        "developed using Streamlit and FastAPI, ensuring a simple and interactive experience for users with "
        "minimal financial engineering background.\n\n"
        "A significant aspect of this project is the integration of Explainable AI, which focuses "
        "on providing reasoning behind the system's outputs, financial metric forecasts, and investment decisions. Although this "
        "feature is continually refined, the system is designed using a modular "
        "architecture that supports the integration of AI-based explanation models using platforms such as Hugging Face.\n\n"
        "In conclusion, the proposed system simplifies the financial analysis process, reduces manual "
        "effort, and enhances accessibility for investors and analysts. It demonstrates the effective application of "
        "data science, machine learning, and artificial intelligence techniques in developing an "
        "intelligent, scalable, and user-friendly analytical platform."
    )
    doc.add_paragraph(abstract_text)
    doc.add_page_break()
    
    # Table of Contents (Manual mock up for synopsis)
    add_heading(doc, 'Table of contents', 1, WD_ALIGN_PARAGRAPH.CENTER)
    
    toc_text = (
        "1. Introduction ............................................................................................................... 1\n"
        "   1.1 General Introduction to the topic ........................................................................ 1\n"
        "   1.2 Organization ........................................................................................................ 1\n"
        "   1.3 Area of Computer Science .................................................................................. 2\n"
        "   1.4 Hardware and Software Requirements................................................................ 2\n"
        "2. Problem definition ..................................................................................................... 4\n"
        "3. Objectives .................................................................................................................. 5\n"
        "4. Background ................................................................................................................ 6\n"
        "5. Methodology .............................................................................................................. 7\n"
        "6. Implementation details............................................................................................. 10\n"
        "7. Progress till date & the Remaining work................................................................. 14\n"
        "8. References................................................................................................................ 16"
    )
    doc.add_paragraph(toc_text)
    doc.add_page_break()
    
    # Chapter 1
    add_heading(doc, 'CHAPTER 1\nIntroduction', 1, WD_ALIGN_PARAGRAPH.RIGHT)
    
    add_heading(doc, '1.1 General introduction to the topic', 2)
    doc.add_paragraph(
        "Financial data analysis plays a crucial role in modern decision-making across the global economy. "
        "With the increasing availability of large corporate datasets, the need for efficient tools to analyze and interpret financial data has become essential. "
        "However, traditional analysis techniques often require significant expertise in "
        "programming, finance, and domain knowledge.\n\n"
        "To address these challenges, intelligent systems are being developed to automate "
        "various stages of financial data analysis. These systems aim to reduce manual effort, improve "
        "accuracy, and provide meaningful insights without requiring deep technical skills. The "
        "integration of Artificial Intelligence (AI) further enhances these systems by enabling "
        "automated decision-making and pattern recognition.\n\n"
        "This project focuses on developing an intelligent financial data analysis system that simplifies "
        "the process of analyzing datasets from Nifty 100 companies and generating insights. The system is designed to "
        "automate key steps such as financial ratio calculation, analysis, and reporting, thereby "
        "improving efficiency and accessibility. It aims to bridge the gap between complex financial data "
        "analysis techniques and users with limited technical knowledge, enabling more "
        "effective data-driven investment and business decision-making."
    )
    
    add_heading(doc, '1.2 Organization', 2)
    doc.add_paragraph(
        "This project has been developed as part of the academic curriculum for the degree of "
        "Bachelor of Technology in Computer Science and Engineering. The development of the "
        "system follows a structured and systematic approach, beginning with problem "
        "identification and requirement analysis, followed by system design, implementation, "
        "and evaluation.\n\n"
        "The system is organized using a modular architecture, where different components are "
        "responsible for specific functionalities. These modules include data aggregation, financial "
        "processing, ratio analysis, visualization, insight generation, and report generation. Each "
        "module operates independently while contributing to the overall workflow of the "
        "system. This modular design enhances maintainability, scalability, and ease of future "
        "enhancements.\n\n"
        "Overall, the project demonstrates the practical application of theoretical concepts "
        "learned and provides a foundation for developing more advanced intelligent systems."
    )
    
    add_heading(doc, '1.3 Area of Computer Science', 2)
    doc.add_paragraph(
        "The proposed project, “Nifty 100 Financial Intelligence Platform with Explainable AI”, lies "
        "primarily within the domains of Data Science, Artificial Intelligence, and Machine "
        "Learning, with supporting concepts from Software Engineering and Data "
        "Visualization.\n\n"
        "Data Science forms the foundation of the system, as it involves tasks such as data "
        "preprocessing, financial ratio calculations, and insight generation. Machine Learning concepts "
        "are applied to evaluate the readiness of datasets for building predictive models by "
        "analyzing factors such as financial stability and capital allocation patterns. The project also "
        "incorporates Artificial Intelligence to enable automated insight generation and support "
        "the development of explainable outputs.\n\n"
        "In addition, principles of Software Engineering are used to design the system using a "
        "modular architecture with frameworks like FastAPI and Streamlit, ensuring scalability and maintainability. Data Visualization "
        "techniques using Plotly and Matplotlib are also employed to represent complex financial data in graphical formats, making "
        "it easier for users to understand and interpret results.\n\n"
        "Overall, the project represents an interdisciplinary application of multiple computer "
        "science domains to build an intelligent and user-friendly financial intelligence system."
    )
    
    add_heading(doc, '1.4 Hardware and software requirements', 2)
    doc.add_paragraph(
        "The development and execution of the proposed system require both hardware and "
        "software components that support data processing, analysis, and user interaction. The "
        "system is designed to run on a basic computing environment, making it accessible to "
        "users with standard hardware configurations.\n\n"
        "Hardware Requirements:\n"
        "• RAM: Minimum 8 GB\n"
        "• Processor: Standard multi-core processor\n"
        "• Operating System: Windows 10 / Windows 11\n\n"
        "Software Requirements:\n"
        "• Programming Language: Python 3.10+\n"
        "• Development Environment: Visual Studio Code\n\n"
        "Libraries Used:\n"
        "The system utilizes various Python libraries for data processing, analysis, visualization, "
        "and system functionality:\n"
        "• Data Processing and Analysis: pandas, numpy, scipy, scikit-learn\n"
        "• Data Visualization: matplotlib, plotly\n"
        "• User Interface: streamlit\n"
        "• Backend & API: fastapi, uvicorn\n"
        "• File Handling: openpyxl\n"
        "• Report Generation: reportlab\n"
        "• Utilities: requests, python-dotenv, pytest"
    )
    doc.add_page_break()
    
    # Chapter 2
    add_heading(doc, 'CHAPTER 2\nProblem definition', 1, WD_ALIGN_PARAGRAPH.RIGHT)
    doc.add_paragraph(
        "In the current data-driven environment, large volumes of financial data are generated across "
        "various stock exchanges and corporate filings. However, raw "
        "data is often unstructured, incomplete, and distributed across multiple statements (Profit & Loss, "
        "Balance Sheet, Cash Flow), making it difficult to analyze directly. Before meaningful insights "
        "can be extracted, the data must undergo several preprocessing steps, including cleaning, "
        "aggregation, and ratio calculation.\n\n"
        "Traditional financial analysis tools and techniques require users to have a strong "
        "understanding of accounting principles, programming, and data handling. This creates a barrier for "
        "retail investors and non-technical users who may need to analyze corporate fundamentals but lack the necessary expertise. As "
        "a result, the process becomes time-consuming, inefficient, and prone to human errors. "
        "Moreover, many existing systems focus primarily on generating outputs such as raw numbers "
        "or stock charts, but they do not provide sufficient explanations for underlying fundamental metrics.\n\n"
        "Another challenge is the absence of integrated systems that can perform multiple tasks "
        "such as data aggregation, metric calculation, peer group ranking, and reporting in a single platform. Users "
        "often rely on multiple fragmented tools, which increases complexity and reduces productivity. "
        "Therefore, there is a need for an intelligent and user-friendly system that can automate "
        "the financial analysis process, reduce manual effort, and provide meaningful fundamental insights along "
        "with understandable explanations. The system should be capable of handling raw "
        "datasets of the Nifty 100 universe, performing analysis, and generating reports, while also being accessible to "
        "users with limited financial or technical knowledge."
    )
    doc.add_page_break()

    # Chapter 3
    add_heading(doc, 'CHAPTER 3\nObjectives', 1, WD_ALIGN_PARAGRAPH.RIGHT)
    doc.add_paragraph(
        "The main objective of this project is to develop a Nifty 100 Financial Intelligence Platform "
        "with Explainable AI that simplifies and automates the process of analyzing financial fundamentals. "
        "The system is designed to assist users in performing comprehensive financial analysis efficiently without "
        "requiring advanced technical or accounting knowledge.\n\n"
        "Specific Objectives:\n"
        "• To develop an automated financial analysis system: The system should be "
        "capable of handling multi-statement financial datasets and performing analysis with minimal user intervention.\n"
        "• To implement data aggregation and calculation techniques: This includes "
        "compiling Balance Sheets, Profit & Loss statements, and computing essential financial ratios (e.g., ROE, Debt-to-Equity).\n"
        "• To generate peer comparisons and insights: The system should "
        "provide meaningful benchmarking against sector medians and peer groups, identifying high-growth and debt-free companies.\n"
        "• To evaluate machine learning readiness of datasets: The system should "
        "analyze whether the financial dataset is suitable for predictive modeling (e.g. bankruptcy prediction or future revenue forecasting).\n"
        "• To provide data visualization support: The system should represent capital allocation "
        "and growth metrics in interactive graphical formats to improve understanding and interpretation.\n"
        "• To generate downloadable financial reports: The system should produce structured "
        "PDF/Excel reports summarizing the fundamental health of companies.\n"
        "• To integrate Explainable AI capabilities: The system aims to provide "
        "explanations for complex financial derivations, improving transparency and user trust (feature under development).\n"
        "• To design a user-friendly interface: The system should be accessible via a Streamlit web app, "
        "even for users with limited technical background."
    )
    doc.add_page_break()

    # Chapter 4
    add_heading(doc, 'CHAPTER 4\nBackground', 1, WD_ALIGN_PARAGRAPH.RIGHT)
    doc.add_paragraph(
        "Fundamental financial analysis is the process of examining a company's financial statements "
        "to determine its intrinsic value and overall financial health. It involves evaluating "
        "income statements, balance sheets, and cash flow statements. Traditionally, these tasks were performed "
        "manually using spreadsheets, which made the process "
        "time-consuming and prone to errors, especially when dealing with decades of data across hundreds of companies (e.g., the Nifty 100).\n\n"
        "With the advancement of technology, programming languages such as Python have "
        "become widely used for financial modeling due to their flexibility and availability of powerful "
        "libraries. Tools like Pandas enable efficient data manipulation, while "
        "libraries such as Plotly and Matplotlib allow visualization of financial trends over time. "
        "These tools have significantly improved the efficiency of fundamental "
        "analysis but still require programming expertise to use effectively.\n\n"
        "Machine Learning has further enhanced the field by enabling systems to learn from financial histories "
        "and make predictions about future performance or distress. However, before applying machine learning models, it is "
        "essential to ensure that the financial dataset is accurately compiled. This includes handling missing "
        "annual reports, aligning accounting periods, and computing derived metrics like Free Cash Flow.\n\n"
        "In recent years, there has been a growing interest in developing automated intelligence platforms "
        "that can democratize institutional-grade financial analysis. These systems aim to "
        "perform multiple tasks such as fundamental screening, charting, and peer benchmarking within a single "
        "platform. However, many existing solutions act as 'black boxes' or only output raw numbers.\n\n"
        "Explainable AI (XAI) has emerged as an important area in artificial intelligence that "
        "focuses on making system decisions transparent and understandable. It helps investors "
        "understand how and why certain financial forecasts or automated stock screenings are generated, which is essential for building "
        "trust in algorithmic decision support.\n\n"
        "This project builds upon these concepts by combining corporate finance principles, "
        "machine learning data preparation, and the paradigms of explainable AI to develop "
        "an intelligent and user-friendly financial analysis system tailored for the Nifty 100."
    )
    doc.add_page_break()

    # Chapter 5
    add_heading(doc, 'CHAPTER 5\nMethodology', 1, WD_ALIGN_PARAGRAPH.RIGHT)
    doc.add_paragraph(
        "The proposed system follows a pipeline-based and modular methodology, where each "
        "stage of financial data processing is handled systematically. This approach ensures that raw accounting data "
        "is transformed into meaningful insights through a sequence of well-defined steps. The "
        "methodology focuses on automation, data integrity, and usability.\n\n"
        "Step 1: Data Integration & Aggregation\n"
        "The first step in the system is acquiring the financial histories of Nifty 100 companies. The platform aggregates datasets from various tables (Profit & Loss, Balance Sheet, Cash Flow). "
        "The system performs basic validation checks to ensure that the dataset spans the required years (e.g. 10 years) and company IDs map correctly.\n\n"
        "Step 2: Metric Computation and Preprocessing\n"
        "Raw financial statements require transformation into standardized ratios for comparative analysis. "
        "In this step, the system performs several operations:\n"
        "• Ratio Calculation: Computation of Return on Equity (ROE), Debt-to-Equity, Free Cash Flow, and Revenue CAGR.\n"
        "• Missing Data Audits: The system checks for documentation gaps, such as missing annual reports or null values in critical fields like Operating Profit.\n"
        "• Data Type Correction: Ensuring monetary values and percentages are cast to appropriate numeric data types.\n\n"
        "Step 3: Sector Benchmarking & Peer Grouping\n"
        "To provide context to the financial metrics, the system categorizes companies into broad sectors and specific peer groups. "
        "It dynamically computes sector medians (e.g. Sector Median ROE) and ranks companies within their peer groups.\n\n"
        "Step 4: Deep Financial Analysis\n"
        "Once metrics are calculated and grouped, the system performs analytical operations:\n"
        "• Capital Allocation Tracking: Identifying patterns in how companies deploy their capital over time.\n"
        "• High Growth & Debt-Free Screening: Filtering companies with >15% Revenue CAGR or zero debt.\n"
        "• ML Readiness Evaluation: Assessing if the financial time-series data is robust enough for predictive models.\n\n"
        "Step 5: Data Visualization\n"
        "Visualization plays a critical role in interpreting multi-year financial trends. "
        "The system generates interactive charts using Plotly and Matplotlib to represent revenue growth, capital allocation patterns, and peer comparisons.\n\n"
        "Step 6: Insight Generation\n"
        "Based on the SQL query results and Python analysis, the system identifies key takeaways, such as the top 10 ROE companies or companies with consistent positive Free Cash Flow for over 5 years.\n\n"
        "Step 7: Report Generation\n"
        "The platform compiles all metrics, visualizations, and insights into structured reports (PDF or Excel formats) using libraries like ReportLab, which can be downloaded by the user for further investment research."
    )
    doc.add_page_break()

    # Chapter 6
    add_heading(doc, 'CHAPTER 6\nImplementation details', 1, WD_ALIGN_PARAGRAPH.RIGHT)
    doc.add_paragraph(
        "The Nifty 100 Financial Intelligence Platform is implemented using a modular and structured approach. "
        "This design improves maintainability, scalability, and ease of debugging. The system is developed using Python and "
        "integrates multiple libraries for data processing, analysis, visualization, and API routing.\n\n"
        "6.1 System Architecture\n"
        "The system follows a modular architecture. The main components include:\n"
        "• Data Management Module (Pandas & SQL)\n"
        "• Ratio Calculation Module\n"
        "• Visualization Module (Plotly/Matplotlib)\n"
        "• API Layer (FastAPI)\n"
        "• User Interface Module (Streamlit)\n"
        "• Reporting Module (ReportLab)\n\n"
        "6.2 Main Application (Streamlit App)\n"
        "The Streamlit app serves as the frontend entry point. It is responsible for:\n"
        "• Handling user interaction and displaying dashboards.\n"
        "• Allowing users to select specific companies or sectors.\n"
        "• Querying the FastAPI backend for processed data.\n"
        "• Displaying outputs such as financial tables, charts, and automated insights.\n\n"
        "6.3 Backend API (FastAPI)\n"
        "The backend is powered by FastAPI, which exposes endpoints for retrieving financial ratios, peer group rankings, and sector medians. "
        "It acts as a robust middle layer between the data files/database and the frontend.\n\n"
        "6.4 Data Processing Module\n"
        "Implemented using Pandas, this module reads the raw Excel/CSV files (Profit & Loss, Balance Sheet, Cash Flow), handles missing values, and merges datasets on company ID and year.\n\n"
        "6.5 Financial Analysis Module\n"
        "This module performs the core business logic, executing exploratory queries to find:\n"
        "• Companies with consecutive positive Free Cash Flow.\n"
        "• Top ROE companies and Debt-Free companies.\n"
        "• Revenue CAGR calculations over 5-year periods.\n\n"
        "6.6 Visualization Module\n"
        "Uses Plotly and Matplotlib to dynamically render interactive charts that map out the financial trajectory of the selected Nifty 100 companies.\n\n"
        "6.7 AI Integration Module (Explainable AI)\n"
        "Provides natural language explanations for the complex financial ratios and model outputs. It is designed to integrate with large language models to generate contextual insights (feature under development)."
    )
    doc.add_page_break()

    # Chapter 7
    add_heading(doc, 'CHAPTER 7\nProgress till date & the Remaining work', 1, WD_ALIGN_PARAGRAPH.RIGHT)
    doc.add_paragraph(
        "The development of the Nifty 100 Financial Intelligence Platform with Explainable AI is "
        "currently in progress, with a significant portion of the core functionalities implemented. "
        "The project has achieved approximately 65-70% completion at this stage.\n\n"
        "7.1 Progress till Date\n"
        "The following components have been successfully implemented:\n"
        "• Data Schema & Aggregation: The financial datasets (Profit & Loss, Balance Sheet, Cash Flow) have been cleaned and structured.\n"
        "• Exploratory SQL Analysis: A comprehensive suite of queries has been developed to track capital allocation, ROE rankings, sector medians, and missing data audits.\n"
        "• Basic Ratio Calculation: Computation of ROE, Debt-to-Equity, Free Cash Flow, and CAGR is functional.\n"
        "• API & UI Scaffolding: The foundational setup for FastAPI and Streamlit has been established.\n\n"
        "7.2 Remaining Work\n"
        "The following components require completion or further refinement:\n"
        "• Advanced Interactive Dashboards: The Streamlit visualization components need to be fully wired to the financial calculation endpoints.\n"
        "• Automated PDF Report Generation: Finalizing the ReportLab module to export the customized financial tear sheets.\n"
        "• Explainable AI Module: The integration of AI-based natural language explanations for the computed financial insights is planned but not fully implemented.\n\n"
        "7.3 Future Scope\n"
        "The system has potential for further enhancement in the following areas:\n"
        "• Integration of advanced machine learning models (e.g., XGBoost) for bankruptcy prediction or earnings forecasting.\n"
        "• Real-time stock price and macroeconomic data integration.\n"
        "• Deployment as a scalable cloud application (AWS/GCP) using the existing Docker configuration."
    )
    doc.add_page_break()

    # Chapter 8
    add_heading(doc, 'CHAPTER 8\nReferences', 1, WD_ALIGN_PARAGRAPH.RIGHT)
    doc.add_paragraph(
        "• McKinney, W. (2017). Python for Data Analysis: Data Wrangling with Pandas, NumPy, and IPython. O'Reilly Media.\n"
        "• FastAPI Documentation. (2024). https://fastapi.tiangolo.com/\n"
        "• Streamlit Inc. (2024). Streamlit Documentation. https://docs.streamlit.io/\n"
        "• Plotly Technologies Inc. (2024). Plotly Python Open Source Graphing Library. https://plotly.com/python/\n"
        "• ReportLab Documentation. (2024). https://www.reportlab.com/docs/\n"
        "• Graham, B., & Dodd, D. (1934). Security Analysis. McGraw-Hill Education (for fundamental accounting and financial ratio principles).\n"
        "• OpenAI (2023). Best Practices for Explainable AI Systems. https://openai.com/research"
    )
    
    doc.save(r'C:\Users\eFuture\Downloads\Nifty100_Synopsis_Report.docx')

if __name__ == '__main__':
    main()
