# deploy:
#     cd deploy_tools && git push && fab

migrate:
	docker-composer run web python manage.py migrate

migrations:
	docker-compose run web python manage.py makemigrations

pytest:
	docker-compose run web pytest pytests

test:
	python manage.py test tests.diario

pyunittest:
	docker-compose run web pytest tests/diario

pyut:
	docker-compose run web pytest pytests/diario

pyft:
	docker-compose run web pytest pytests/functional

test-model:
	docker-compose run web python manage.py test tests.diario.test_models
