up:
	docker compose up --build -d

down:
	docker compose down -v

migrate:
	docker compose exec api alembic upgrade head

seed:
	docker compose exec api python scripts/seed_demo.py

logs:
	docker compose logs -f

test:
	curl http://localhost:8000/api/health

clean:
	docker compose down -v
	docker system prune -f

