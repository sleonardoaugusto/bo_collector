.PHONY: run

run:
	sudo pmset -a disablesleep 1 ;\
	python3 main.py ;\
	sudo pmset -a disablesleep 0