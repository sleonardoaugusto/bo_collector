.PHONY: run

run:
	@read -s -p "Enter root password: " PASSWORD; \
	echo $$PASSWORD | sudo -S pmset -a disablesleep 1 &&\
	python3 main.py ;\
	echo $$PASSWORD | sudo -S pmset -a disablesleep 0