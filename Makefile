.PHONY: help install run test figures dashboard build clean

help:
	@echo "make install   -install python deps"
	@echo "make run       -run the full audit pipeline (->results/,dashboard data)"
	@echo "make test      -run the pytest suite"
	@echo "make dashboard -start the dev dashboard (npm)"
	@echo "make build     -build the dashboard for production"
	@echo "make clean     -remove generated outputs"

install:
	pip install -r requirements.txt

run:
	python run_all.py

test:
	pytest -q

figures:
	python run_all.py --no-figures && echo "use 'python run_all.py' to include figures"

dashboard:
	cd dashboard && npm install && npm run dev

build:
	cd dashboard && npm install && npm run build

clean:
	rm -f results/results.json results/summary_table.csv results/REPORT.md
	rm -f results/figures/*.png
	rm -f dashboard/public/results.json
	@echo "cleaned generated outputs (regenerate with 'make run')"