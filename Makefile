.PHONY: load ratios test report dashboard api clean all

load:
	python src/etl/loader.py

ratios:
	python src/analytics/ratios.py

test:
	python -m pytest tests/ --html=reports/pytest_report.html --self-contained-html

report:
	python src/reports/tearsheet.py
	python src/reports/sector_report.py
	python src/reports/portfolio_report.py
	python src/reports/build_analyst_guide.py
	python src/reports/build_acceptance_checklist.py

dashboard:
	streamlit run src/dashboard/app.py --server.port 8501

api:
	uvicorn src.api.main:app --port 8000 --reload

clean:
	python -c "import os, shutil, glob; [shutil.rmtree(p, ignore_errors=True) for p in glob.glob('**/__pycache__', recursive=True)]"

all: load ratios test report
