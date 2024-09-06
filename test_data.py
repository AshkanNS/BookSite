import unittest
import app


def test_endpoint(client):
    response = client.get('/')
    assert response.status_code == 200
    
	 

		
		


	




		

    
    

