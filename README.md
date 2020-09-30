# Dyson-timent

This is a Python app to stream and filter Tweets by keyword, perform sentiment analyis on each Tweet, and upload it all to a BigQuery database.

See the related Medium article for more information: https://medium.com/@robee031/tracking-dysons-public-image-using-46-166-tweets-68af509923a6
See the Data Studio project for a demo of the data this project can retrieve: https://datastudio.google.com/reporting/a813866d-8df3-4691-a89b-b3e1e8386b50

### Additional Setup Required

1) You must use your own Twitter API keys, copy them into Google Cloud Secrets Manager, and update config.conf to use your secrets manager url
2) You should set up a service account in Google Cloud IAM, making sure it has Secrets Manager Secret Accessor and PubSub Publisher permissions
3) You should update config.conf to use the correct PUBSUB_TOPIC and PROJECT_NAME, specific to you.
