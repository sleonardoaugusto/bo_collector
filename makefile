.PHONY: run

run:
	@if [ -z "$(PASSWORD)" ]; then \
		echo "Error: root password is required. Run with 'make run PASSWORD=your_password'"; \
		exit 1; \
	fi
	echo "$(PASSWORD)" | sudo -S pmset -a disablesleep 1 &&\
	python3 main.py ;\
	echo "$(PASSWORD)" | sudo -S pmset -a disablesleep 0