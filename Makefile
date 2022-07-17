# deploy:
#     cd deploy_tools && git push && fab

migrate:
	python manage.py migrate

migrations:
	python manage.py makemigrations

pytest:
	pytest pytests

test:
	python manage.py test tests.diario

pyunittest:
	pytest tests/diario

test-model:
	python manage.py test tests.diario.test_models