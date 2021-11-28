To run in production.

* Ensure that you have _settings_prod_private.py_ file that contains `SECRET_KEY`, `WORKER_TOKEN`, `EMAIL_HOST_PASSWORD`, etc. variables. Use _settings_prod_private_sample.py_ as a template to create your own secret file. Never commit it to the repository.

* In _settings_common.py_, at the last line, set proper _customized_for_..._ import.
