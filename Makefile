.PHONY: setup pipeline dashboard

setup:
	pip install -r requirements.txt

pipeline:
	python load_data.py
	python -m src.analysis
	python -m src.stats
	python -m src.subsets

dashboard:
	streamlit run app.py