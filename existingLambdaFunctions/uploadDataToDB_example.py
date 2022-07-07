import json
import boto3
from lambda_functions_package import *

# This Example pulls data from: s3://stg-hsr-internal-data-products/careDeserts/womensHealthDesert/finalProducts/usWomensHealthCountyAnalysis/usWomensHealthCountyAnalysis.geojson
# And uploads it to the database with the name: layer_caredeserts_uswomenshealthcountyanalysis

s3_bucket = 'stg-hsr-internal-data-products'
s3_path = 'careDeserts/womensHealthDesert/finalProducts/usWomensHealthStateAnalysis/usWomensHealthStateAnalysis.geojson'
db_table_name = 'layer_caredeserts_uswomenshealthstateanalysis'
table_state = "Replace" # Can be Replace or Update
data_type = 'geometry' # Can be parquet or csv or geometry
geometry_type = "MULTIPOLYGON" # Only Needed for Geometry / Geospatial files Can be POINT, LINESTRING, or MULTIPOLYGON
geometry_crs = "4326" # Only Needed for Geometry / Geospatial files.  Is the epsg/crs projection of the data.  Default is 4326 which is WGS84
hsr_upload_to_db(s3_bucket, s3_path, db_table_name, table_state, data_type)