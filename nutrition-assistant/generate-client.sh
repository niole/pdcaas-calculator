#!/bin/bash
#
# Gets the most recent version of the openapi json for the recipe server and then
# generates a typescript client from it.
# The recipe server must be running for this to work.

OPENAPI_JSON=$(curl http://127.0.0.1:8000/openapi.json)

echo $OPENAPI_JSON | openapi --input /dev/stdin --output ./src/utils/recipe-client --name RecipeClient --exportSchemas true
