.PHONY: run worker redis flower stop clean main

# Redis settings
REDIS_CONTAINER=redis
REDIS_PORT=6379

# Celery settings
CELERY_CONCURRENCY=4
CELERY_APP=app.tasks
QUEUE=tokens

# Flower settings
FLOWER_PORT=5555

# Run the entire project
run: redis worker flower main

# Start Redis container
redis:
	@docker ps -q -f name=$(REDIS_CONTAINER) | grep -q . || \
	docker run -d --name $(REDIS_CONTAINER) -p $(REDIS_PORT):6379 redis
	@echo "✅ Redis is running on port $(REDIS_PORT)"

# Start Celery worker with concurrency
worker:
	@echo "🚀 Starting Celery workers with concurrency=$(CELERY_CONCURRENCY)..."
	PYTHONPATH=. celery -A $(CELERY_APP) worker --loglevel=info -Q $(QUEUE) --concurrency=$(CELERY_CONCURRENCY) &

# Start Flower for monitoring Celery tasks
flower:
	@echo "🌸 Starting Flower on port $(FLOWER_PORT)..."
	PYTHONPATH=. celery -A $(CELERY_APP) flower --port=$(FLOWER_PORT) &

# Run the main Python script
main:
	@echo "🎯 Running the main Python script..."
	PYTHONPATH=. caffeinate -dims & \
	PYTHONPATH=. python3 app/main.py

# Stop Redis, Celery, and Flower
stop:
	@echo "🛑 Stopping Redis, Celery, and Flower..."
	-docker stop $(REDIS_CONTAINER)
	-docker rm $(REDIS_CONTAINER)
	-pkill -f 'celery'

# Clean up logs, cache, and containers
clean:
	@echo "🧹 Cleaning up..."
	rm -rf __pycache__ app.log
	-docker rm -f $(REDIS_CONTAINER)
	-pkill -f 'celery'