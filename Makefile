COMPOSE = docker-compose -f docker/docker-compose.yml

all: up

up:
	$(COMPOSE) up --build -d

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
