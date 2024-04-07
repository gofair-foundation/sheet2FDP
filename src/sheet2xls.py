import os
import requests
import sys
import pandas as pd

##############################################
def getGoogleSeet(spreadsheet_id, spreadsheet_gid, outDir, outFile):
  
  url = f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={spreadsheet_gid}'
  response = requests.get(url)
  if response.status_code == 200:
    filepath = os.path.join(outDir, outFile)
    with open(filepath, 'wb') as f:
      f.write(response.content)
      print('CSV file saved to: {}'.format(filepath))    
  else:
    print(f'Error downloading Google Sheet: {response.status_code}')
    sys.exit(1)


##############################################
def write_output(filename):
  print(filename)
  txt_delimiter = ','
  df = pd.read_csv(
    filename + ".csv", delimiter=txt_delimiter
  )
  df.to_csv(filename + ".tsv", sep="\t", index=False, header=False)

##############################################

file_name = os.environ['FILE_NAME']
sheet_id = os.environ["SHEET_ID"]
sheet_gid = os.environ["SHEET_GID"]

outDir = './'

os.makedirs(outDir, exist_ok = True)

output_filename = file_name + ".csv"
filepath = getGoogleSeet(sheet_id, spreadsheet_gid=0, outDir=outDir, outFile=output_filename)
write_output(file_name)

filepath = getGoogleSeet(sheet_id, sheet_gid, outDir, file_name + str(sheet_gid) + ".csv")
write_output(file_name + str(sheet_gid) )

sys.exit(0); ## success
