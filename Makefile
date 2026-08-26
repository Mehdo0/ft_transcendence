COMPOSE = docker-compose -f docker/docker-compose.yml
PROD_COMPOSE = docker compose --env-file .env -f docker/docker-compose.prod.yml

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

prod-up: secrets/secret_key
	$(PROD_COMPOSE) up --build -d

secrets/secret_key:
	mkdir -p secrets
	umask 077; openssl rand -hex 32 > $@

prod-down:
	$(PROD_COMPOSE) down

prod-logs:
	$(PROD_COMPOSE) logs -f

fclean: down
	rm -rf data/game_data.db

re: fclean up

.PHONY: all up down logs prod-up prod-down prod-logs fclean re
