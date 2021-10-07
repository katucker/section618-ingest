import os
import sys
import cgi
#import cgitb
#import requests

import ckanapi

	
if __name__ == '__main__':

    url = os.getenv('ED_CKAN_URL', None)
    apiKey = os.getenv('ED_CKAN_KEY', None)

    errors = []

    if not url:
        errors.append('ED_CKAN_URL environment variable is needed.')
    if not apiKey:
        errors.append('ED_CKAN_KEY environment variable is needed.')

    if len(sys.argv) < 3:
        errors.append("Format: {} resource_identifer replacement_file.".format(sys.argv[0]))

    if len(errors):
        for e in errors:
            print(e)
        sys.exit(1)

#    cgitb.enable()
    
    remote = ckanapi.RemoteCKAN(address=url, apikey=apiKey, get_only=False)
    print('CKAN URL: {}'.format(url))

    resource_id = sys.argv[1]
    filepath = sys.argv[2]
    filename = filepath.split('/')[-1]

    try:
        update_file = open(filename, "rb")
    except EnvironmentError:
        print('Could not open {}'.format(filename))
    else:
        with update_file:
            try:
                # CKAN only accepts this kind of object here...
                #file_obj = cgi.FieldStorage()
                #file_obj.file = update_file
                #file_obj.filename = filename
                #file_obj.file.name = filename
            
                result = remote.call_action(action='resource_patch', data_dict={
                    'id': resource_id,
                    'name': filename,
                    }, files={'upload': update_file})
                # result = requests.post('{}api/action/resource_update'.format(url),
                #     data=data_dict,
                #     headers={"X-CKAN-API-Key": apiKey},
                #     files=[('upload', file_obj.file)]
                #     )
        
            except Exception as e:
                print('Cannot update resource with ID {}. Error was: {}'.format(resource_id, e))
#                cgitb.handler()
 