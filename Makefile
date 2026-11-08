collect-static:
	./vfinper/bin/python src/manage.py collectstatic --noinput --clear

test-server:
	./vfinper/bin/python src/manage.py runserver 8002

test-server-debug-false:
	DJANGO_DEBUG_FALSE=true \
	DJANGO_SECRET_KEY=secret  \
	DJANGO_ALLOWED_HOST=localhost \
	DJANGO_DB_PATH=src/db.sqlite3 \
	./vfinper/bin/python src/manage.py runserver 8002

# Comandos de control de versiones
tag-live:
	git tag -f LIVE && export TAG=`date +DEPLOYED-%F/%H%M` && git tag $TAG && git push origin -f --tags