'''
Created on Jun 17, 2016

@author: qc
'''

import sqlalchemy
engine = sqlalchemy.create_engine('mssql+pyodbc://.\\SQLEXPRESS/odoo2?trusted_connection=yes') 

