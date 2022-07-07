import json
import boto3
from lambda_functions_package import *

# This Example pulls the household pulse survey puf file from the zip repository available online
# and saves it to the path s3://stg-hsr-authoritative-data/hps/hps/hps_puf/2020/07/pulse2020_puf_07.parquet.gzip
dataName = "Household Pulse Survey Data Week 07"
dataOrganization = "US Census Bureau"
dataRecency = "Current"
dataUpdateFrequency = "Every 2 Months"
downloadUrl = "https://www2.census.gov/programs-surveys/demo/datasets/hhp/2020/wk7/HPS_Week07_PUF_CSV.zip" # The URL to download the data from can be an https url or an S3 URI
zipFileName = "pulse2020_puf_07.csv" # Leave this as "None" or dont define this variable when you are not trying to pull a file out of a zip archive
downloadType = "tabularParquet" # Can be tabularParquet, geometry, or stream
destBucket = "stg-hsr-authoritative-data" # This will basically always be hsr-authoritative-data
destPath = "hps/hps/hps_puf/2020/07/pulse2020_puf_07" #IMPORTANT: Follow this structure [dataOrganization]/[dataCategory]/[tableName]/[dataFileName]
# ADDITIONALLY: You only specify the extension to the file name in the destPath if you are streaming the data
# If you have time series data then you will want to have partition folders after the tableName part of the path as follows:
# [dataOrganization]/[dataCategory]/[tableName]/[partition1]/[partition2]/[dataFileName]
# Partitions are just a way to futher organize timeseries data and can be stuff like year, day, week, etc
# Additionally THE PATH CANNOT CONTAIN SPACE BARS I WOULD USE UNDERSCORES OR CAPITALIZE THE FIRST LETTER OF EACH WORK OTHER THAN THE FIRST such as:
# hps/hps/hps_puf/2020/07/pulse2020_puf_07.parquet.gzip  OR hps/hps/hpsPUF/2020/07/pulse2020PUF07.parquet.gzip OR hhs/empower/countyEmpower/2022/countyEmpower2022.parquet.gzip
updateGlue = "yes" # This argument is here to run the glue crawler after this lambda has ran.  
# The values applicable are yes and no.  Only need to run this if you are adding a new data source or partition. Default value is no
hsr_download_data(dataName, dataOrganization, dataRecency, dataUpdateFrequency, downloadUrl, downloadType, destBucket, destPath, zipFileName, updateGlue)

# This Example pulls the cbg table from the safegraph bucket and
# saves it to the s3 path: s3://stg-hsr-authoritative-data/hsr-safegraph-data/sgCBGCensus/sgcbgcensus.parquet.gzip

dataName = "Safegraph CBG Data"
dataOrganization = "Safegraph"
dataRecency = "2020"
dataUpdateFrequency = "Annual"
downloadUrl = "s3://hsr-bri-results/cbg_b01.csv"
# zipFileName = "pulse2020_puf_07.csv"
downloadType = "tabularParquet" # Can be tabularParquet, geometry, or stream
destBucket = "stg-hsr-authoritative-data"
destPath = "hsr-safegraph-data/sgCBGCensus/sgCBGCensus/sgcbgcensus"
# updateGlue = "yes"
hsr_download_data(dataName, dataOrganization, dataRecency, dataUpdateFrequency, downloadUrl, downloadType, destBucket, destPath)

# This Example Streams the data from the google mobility reports to our s3 bucket
dataName = "Google Mobility Reports"
dataOrganization = "Google"
dataRecency = "Current"
dataUpdateFrequency = "Daily"
downloadUrl = "http://www.gstatic.com/covid19/mobility/Global_Mobility_Report.csv"
# zipFileName = "pulse2020_puf_07.csv"
downloadType = "stream" # Can be tabularParquet, geometry, or stream
destBucket = "stg-hsr-authoritative-data"
destPath = "google_mobility_reports/google_mobility_reports/Global_Mobility_Report.csv"
# updateGlue = "yes"
hsr_download_data(dataName, dataOrganization, dataRecency, dataUpdateFrequency, downloadUrl, downloadType, destBucket, destPath)

# This Example pulls the household pulse survey puf file from the zip repository available online
# saves it to the s3 path: s3://hsr-authoritative-data/hps/2022/42/pulse2022_puf_42.parquet

downloadType = 'tabularParquet'
dataCategory = 'HPS Data'
dataName = 'Week 07 Data'
downloadUrl = "https://www2.census.gov/programs-surveys/demo/datasets/hhp/2020/wk7/HPS_Week07_PUF_CSV.zip" # The URL to download the data from can be an https url or an S3 URI
destBucket = 'hsr-authoritative-data' # This will basically always be hsr-authoritative-data
destKey = "hps/2022/42/pulse2022_puf_42" # The path in the bucket to save the file NOTE: do not include the extension as it is automatically added to the filename
fileName = "pulse2020_puf_07.csv" # Only Needed for Pulling Files from a zip archive IMPORTANT: Remove this Variable or keep it as None if not pulling from a zi parchive

hsr_download_data(downloadType, dataCategory, dataName, downloadUrl, destBucket, destKey, fileName)