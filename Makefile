AUTHOR = cocasema
NAME = stock_bot
VERSION = latest
IMAGE = $(AUTHOR)/$(NAME)

HOST_DIR = /data/$(NAME)

.PHONY: all deps deps_dev build update_config run run_test up

all: build

deps:
	pip3 install --upgrade pip
	pip3 install docker-compose

deps_dev: deps
	pip3 install -r requirements.txt

build:
	docker build --rm -t $(IMAGE):$(VERSION) .

update_config:
	mkdir -p $(HOST_DIR)
	cp -u $(NAME)/$(NAME).conf.default $(HOST_DIR)/$(NAME).conf

run: deps build update_config
	docker-compose run --rm $(NAME)

run_test: deps build update_config
	docker-compose run --rm $(NAME)_test
	
up: deps build update_config
	docker-compose up -d
