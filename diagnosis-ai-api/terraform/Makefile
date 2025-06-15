sv:
	for secret in GEMINI_API_KEY; do \
		value=$$(gcloud secrets versions access latest --secret="$$secret"); \
		echo "$${secret//-/_}" | tr '[:upper:]' '[:lower:]' | sed 's/$$/ = "'"$$value"'"/' >> terraform.tfvars; \
	done
