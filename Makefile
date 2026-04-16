COMPOSE = docker compose -f docker/docker-compose.yml

all: up

up:
	$(COMPOSE) up --build -d

down:
	$(COMPOSE) down

ps:
	$(COMPOSE) ps -a

logs:
	$(COMPOSE) logs -f

logs-front:
	$(COMPOSE) logs -f frontend

logs-back:
	$(COMPOSE) logs -f backend

logs-db:
	$(COMPOSE) logs -f db

fclean: down
	rm -rf data

re: fclean up

.PHONY: all up down logs logs-front logs-back logs-db fclean re
