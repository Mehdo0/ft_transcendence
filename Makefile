COMPOSE = docker-compose -f docker/docker-compose.yml

all: up

up: secrets/server.crt
	$(COMPOSE) up --build -d

secrets/server.crt:
	bash setup.sh

down:
	$(COMPOSE) down

ps:
	$(COMPOSE) ps -a

logs:
	$(COMPOSE) logs -f

fclean: down
	rm -rf data

re: fclean up

.PHONY: all up down logs fclean re
