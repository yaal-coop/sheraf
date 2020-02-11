PERSISTENT=local.persistent

run-zeo:
	@mkdir --parents "${PERSISTENT}/files" "${PERSISTENT}/blobs" "${PERSISTENT}/logs"
	env PYTHONPATH=. poetry run runzeo -C ./tests/zeo.config

run-zeo-for-test:
	@mkdir --parents "${PERSISTENT}/files" "${PERSISTENT}/blobs" "${PERSISTENT}/logs"
	env PYTHONPATH=. poetry run runzeo -C ./tests/zeo_filestorage_test.config

clean:
	@find . \( -name "*.pyc" -o -name "*.orig" -o -name "*.swp" -o -name "*~" -o -name "__pycache__" -o -name "*.egg-info" -o -name "htmlcov" -o -name dist \) -exec rm -rf "{}" +
	@rm -fr ./build

perf:
	poetry run pytest tests/perf/test_perf.py

perf-size:
	poetry run python tests/perf/perfs_large_dict_size_and_object_type.py

disk-usage:
	mkdir -p tmp/
	poetry run pytest tests/perf/test_disk_usage.py
