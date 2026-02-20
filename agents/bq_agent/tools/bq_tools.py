import os
import google.auth
from google.adk.tools.bigquery import BigQueryCredentialsConfig, BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode

def get_bigquery_toolset() -> BigQueryToolset:
    """Initializes and returns the BigQueryToolset."""
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "mg-ce-demos")

    # 1. Setup credentials and toolset
    # Using application default credentials. Ensure they have BigQuery access.
    application_default_credentials, _ = google.auth.default(quota_project_id=project_id)
    credentials_config = BigQueryCredentialsConfig(
        credentials=application_default_credentials
    )

    # Use BLOCKED write mode since we only need to query the public dataset
    tool_config = BigQueryToolConfig(
        write_mode=WriteMode.BLOCKED,
    )

    return BigQueryToolset(
        credentials_config=credentials_config, bigquery_tool_config=tool_config
    )

# Export a configured instance
bigquery_toolset = get_bigquery_toolset()
