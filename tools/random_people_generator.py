"""A quick script to generate arbitrary numbers of random people in PCO.

Usage: `python tools/random_people_generator.py 100` 
    (100 is number of records to generate)

Useful for quickly mocking a large amount of test data.

Expects a PCO_APP_ID and PCO_SECRET to be present as environment variables
"""

import os
import random
import sys

# Not quite sure why we're needing to do this for this import,
# but it makes the import work.
sys.path.append('..')
sys.path.append('.')

PCO_APP_ID = os.environ['PCO_APP_ID']
PCO_SECRET = os.environ['PCO_SECRET']

from pypco import PCO #pylint: disable=wrong-import-position

def generate_rand_string(length):
    """Generate a random string of the requested length.

    Returns lowercase letters.

    Args:
        length (int): The length of the random string.

    Returns
        (str): The random string.
    """

    output = []

    for ndx in range(length): #pylint: disable=unused-variable
        output += chr(random.randint(97,122))

    return ''.join(output)

def generate_people(num_people):
    """Generate the specified number of random people objects.

    Also generates the emails for the random people using the Mailinator service
    (https://www.mailinator.com/)
    """

    pco = PCO(PCO_APP_ID, PCO_SECRET)

    for ndx in range(num_people):

        new_person = PCO.template(
            'Person',
            {
                'first_name': generate_rand_string(6).title(),
                'last_name': generate_rand_string(8).title(),
            }
        )

        person = pco.post(
            '/people/v2/people',
            new_person
        )

        person_id = person['data']['id']

        new_email = PCO.template(
            'Email',
            {
                'address': f'{generate_rand_string(8)}@mailinator.com',
                'location': 'Home',
                'primary': True,
            }
        )

        pco.post(
            f'/people/v2/people/{person_id}/emails',
            new_email
        )

        sys.stdout.write(f'Created {ndx+1} of {num_people}\r')
        sys.stdout.flush()

    sys.stdout.write('\n')

if __name__ == '__main__':
    generate_people(int(sys.argv[1]))
