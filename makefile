IMAGE_NAME=bo_collector
PLATFORM=linux/amd64

all: build run

build:
	@echo "🔨 Building Docker image for $(PLATFORM)..."
	docker buildx build --platform=$(PLATFORM) -t $(IMAGE_NAME) --load .

run:
	@echo "🚀 Running Docker container..."
	docker run --platform=$(PLATFORM) --rm -v $(PWD)/downloads:/app/downloads $(IMAGE_NAME)

shell:
	@echo "🐚 Starting interactive shell..."
	docker run --platform=$(PLATFORM) --rm -it -v $(PWD)/downloads:/app/downloads $(IMAGE_NAME) /bin/bash

clean:
	@echo "🧹 Cleaning up..."
	docker rmi $(IMAGE_NAME) || true