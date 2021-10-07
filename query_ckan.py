import os
import sys

import ckanapi
import json

url = os.getenv('ED_CKAN_URL', None)
apiKey = os.getenv('ED_CKAN_KEY', None)

def dump_dataset(id):
    
    try:
        result = remote.call_action(action='package_show', data_dict={'id': id})
        print("Metadata:")
        print(json.dumps(result,indent=2))

    except ckanapi.errors.NotFound:
       print('ID not found: {}'.format(id))

    try:
        rel_result = remote.call_action(action='package_relationships_list', data_dict={
            'id': id,
            'rel': 'parent_of'
            })
        for rel in rel_result:
            try:
                doc_id = rel['object']
                print("Checking id {} for documentation.".format(doc_id))
                result = remote.call_action(action='package_show', data_dict={'id': doc_id})
                if (result.get('type') != 'documentation'): continue
                print("Documentation metadata:")
                print(json.dumps(result,indent=2))

            except ckanapi.errors.NotFound:
                continue
            
    except:
        return

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

    id = ''
    if len(sys.argv) > 1:
        id = sys.argv[1]
        print('Metadata for id {}:'.format(id))
        dump_dataset(id)
    else:
        print('Enter an identifier as the only command argument.')

