.PHONY: run

run:
	caffeinate -dims & \
	python3 main.py