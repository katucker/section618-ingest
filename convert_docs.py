import os
import sys
import cgi
import tempfile
import requests

import ckanapi
import win32com.client
import wmi

url = os.getenv('ED_CKAN_URL', None)
apiKey = os.getenv('ED_CKAN_KEY', None)

doc_types = [
	"application/msword",
	"application/vnd.openxmlformats-officedocument.wordprocessingml.document"
]

# Kill WinWord.exe process
def kill_word_process():
	process_list = wmi.WMI()
    for process in process_list.Win32_Process(Name='WINWORD.EXE'):
        try:
            process.Terminate()
        except:
            continue

# Convert Word document at passed path to PDF document at second passed path.
def convert_word_to_pdf(path_to_doc, path_to_pdf):
	print('Converting {} to {}'.format(path_to_doc, path_to_pdf))
    kill_word_process()
    wp = win32com.client.Dispatch("Word.Application")
    word_doc = wp.Documents.Open(path_to_doc)
    word_doc.SaveAs(path_to_pdf, FileFormat=17)
    word_doc.Close()
    wp.Quit()

#Query CKAN for the resources associated with the passed identifier.
def get_resources(id):

    resources = []       # List of all resources
    transformables = []  # List of all transformable resources

    try:
      dataset = remote.call_action(action='package_show', data_dict={
                'id': dataset_id})
      if dataset.get('resources'):
          dataset_resources = [{'id': r['id'], 'url': r['url']} for r in dataset['resources']]
          dataset_transformables = [{'id': r['id'], 'url': r['url']} for r in dataset['resources'] if r['url_type'] != 'upload' and r['url'] and r['mimetype'] in doc_types]
          resources.extend(dataset_resources)
          transformables.extend(dataset_transformables)
                        
    except ckanapi.errors.NotFound:
            print('ID not found: {}'.format(dataset_id))

    return (resources, transformables)

def download_file(url, directory):
    content_type = None

    try:
        headers = {
            "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"
        }
        r = requests.get(url, stream=True, headers=headers)
        #r.raise_for_status()
        # save the content type, we will need to return it
        content_type = r.headers.get('Content-Type','')

        filename = url.split('/')[-1]
        filepath = os.path.join(directory, filename)

		with open(filepath, "wb") as dump_file:
        	# For each chunk of the file we are getting, flush it into out temp file
        	for chunk in r.iter_content(chunk_size=8192):
            	dump_file.write(chunk)
            	
        # Return the file path for the downloaded file
        return (filepath)

    except requests.exceptions.HTTPError as e:
        print("HTTP Error: %s", e)
    except requests.exceptions.ConnectionError as e:
        print("Connection Error: %s", e)
    except requests.exceptions.Timeout as e:
        print("Timeout Error: %s", e)
    except requests.exceptions.TooManyRedirects as e:
        print("Too Many Redirects Error: %s", e)
    except requests.exceptions.RequestException as e:
        print("Request Exception Error: %s", e)

    return (None)

def download_resource(resource, directory):

    resource_id = resource['id']
    resource_url = resource['url']

    filepath = download_file(resource_url, directory)
	
    if not filepath:
        print('Cannot download {} due to an error.'.format(resource_url))
        return False

	#Determine the path to use for the PDF document.
	pdf_filepath = filepath.split('.')[-1].append('pdf')
	filename = pdf_filepath.split('/')[-1]
	
	with open(pdf_filepath,"rb") as pdf_file:
    	try:
        	# CKAN only accepts this kind of object here...
        	file_obj = cgi.FieldStorage()
        	file_obj.file = pdf_file
        	file_obj.filename = resource_url.split('/')[-1]
        	file_obj.file.name = resource_url.split('/')[-1]
        
        	data_dict = {
            	'id': resource_id,
            	'format': 'PDF',
            	'mimetype': 'application/pdf'
        	}
        	result = requests.post('{}api/action/resource_update'.format(url),
            	data=data_dict,
            	headers={"X-CKAN-API-Key": apiKey},
            	files=[('upload', file_obj.file)]
            	)

    	except Exception as e:
        	print('Cannot update resource with ID {}. Error was: {}'.format(resource_id, e))
        	return False


    return result

if __name__ == '__main__':

    errors = []

    if not url:
        errors.append('ED_CKAN_URL environment variable is needed.')
    if not apiKey:
        errors.append('ED_CKAN_KEY environment variable is needed.')

    if len(errors):
        for e in errors:
            print(e)
        sys.exit(1)

    remote = ckanapi.RemoteCKAN(url, apiKey)
    print('CKAN URL: {}'.format(url))

    if len(sys.argv) < 2:
        print("Identifier to convert needed as command line argument.")
        sys.exit(1)

    # Get a list of all resources, and a list of all resources that are links
    resources, docs = get_resources(sys.argv[1])
    print('{} resources found.'.format(len(resources)))
    print('{} resources need to be converted.'.format(len(docs)))
    print('================================')

    # Create a temporary directory for holding all the files. Once this is done,
    # the temporary directory will be automatically "closed" and all its content will
    # be deleted.
    with tempfile.TemporaryDirectory() as temp_dir:

    	# Convert them one by one, counting them as we go.
    	counter = 0
    	for doc in docs:
        	counter = counter + 1
        	print('[{}/{}] Transforming resource {} '.format(counter, len(docs), docs['url']))
        	download_resource(doc, temp_dir.name())