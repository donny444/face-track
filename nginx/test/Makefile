# nginx/test/Makefile
#
# Convenience wrapper around the smoke-test compose stack. All targets
# assume you run them from the repo root or from this directory - both
# work because the docker-compose file path is anchored relative to this
# Makefile.

COMPOSE_FILE := $(dir $(lastword $(MAKEFILE_LIST)))docker-compose.test.yml

.PHONY: test syntax up down clean

# Bring the whole smoke stack up, run the assertions, and exit with
# the tester's status code.
test:
	docker compose -f $(COMPOSE_FILE) up --build --abort-on-container-exit --exit-code-from tester
	$(MAKE) -f $(lastword $(MAKEFILE_LIST)) clean

# Verify the production nginx config is syntactically valid without
# starting the rest of the stack.
syntax:
	docker run --rm \
	  -v "$(CURDIR)/$(dir $(lastword $(MAKEFILE_LIST)))../nginx.conf:/etc/nginx/nginx.conf:ro" \
	  -v "$(CURDIR)/$(dir $(lastword $(MAKEFILE_LIST)))../conf.d:/etc/nginx/conf.d:ro" \
	  nginx:alpine nginx -t

# Boot the stack and leave it running for manual poking.
up:
	docker compose -f $(COMPOSE_FILE) up --build -d

# Stop and remove the stack.
down:
	docker compose -f $(COMPOSE_FILE) down -v --remove-orphans

clean:
	-docker compose -f $(COMPOSE_FILE) down -v --remove-orphans
